"""Agregações de insights operacionais (F7 / T-7.1)."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from datetime import timedelta
from decimal import Decimal

from django.db.models import Count, Sum
from django.utils import timezone

from apps.ai.models import ChatFeedback, ChatMessage, ChatSession
from apps.manuals.models import ExtractionLog
from apps.orders.models import Order
from apps.tickets.models import CrossSellAttribution, Ticket, TicketEvent


@dataclass
class InsightsPayload:
    days: int
    since: str
    chat: dict
    tickets: dict
    sales_ai: dict
    ai_cost: dict

    def to_dict(self) -> dict:
        return asdict(self)


def _period_start(days: int):
    return timezone.now() - timedelta(days=max(1, days))


def collect_insights(*, days: int = 30) -> InsightsPayload:
    since = _period_start(days)
    return InsightsPayload(
        days=days,
        since=since.isoformat(),
        chat=_chat_metrics(since),
        tickets=_ticket_metrics(since),
        sales_ai=_sales_ai_metrics(since),
        ai_cost=_ai_cost_metrics(since),
    )


def _chat_metrics(since) -> dict:
    sessions = ChatSession.objects.filter(created_at__gte=since)
    total_sessions = sessions.count()
    escalated = sessions.exclude(escalated_ticket_id=None).count()
    resolved_without_human = max(0, total_sessions - escalated)
    resolution_rate = (
        round(100.0 * resolved_without_human / total_sessions, 1) if total_sessions else 0.0
    )

    feedback = ChatFeedback.objects.filter(created_at__gte=since)
    up = feedback.filter(vote=ChatFeedback.Vote.UP).count()
    down = feedback.filter(vote=ChatFeedback.Vote.DOWN).count()
    total_fb = up + down
    upvote_rate = round(100.0 * up / total_fb, 1) if total_fb else 0.0

    user_msgs = (
        ChatMessage.objects.filter(
            created_at__gte=since,
            role=ChatMessage.Role.USER,
        )
        .order_by("-created_at")
        .values_list("content", flat=True)[:500]
    )
    counter: Counter[str] = Counter()
    for content in user_msgs:
        key = " ".join((content or "").strip().lower().split())[:80]
        if key:
            counter[key] += 1
    top_questions = [{"question": q, "count": n} for q, n in counter.most_common(8)]

    found_rate = 0.0
    assistant_qs = ChatMessage.objects.filter(
        created_at__gte=since,
        role=ChatMessage.Role.ASSISTANT,
    )
    asst_total = assistant_qs.count()
    if asst_total:
        found = assistant_qs.filter(found_in_manual=True).count()
        found_rate = round(100.0 * found / asst_total, 1)

    return {
        "sessions": total_sessions,
        "escalated": escalated,
        "resolved_without_human": resolved_without_human,
        "resolution_rate_pct": resolution_rate,
        "feedback_up": up,
        "feedback_down": down,
        "upvote_rate_pct": upvote_rate,
        "found_in_manual_pct": found_rate,
        "top_questions": top_questions,
    }


def _ticket_metrics(since) -> dict:
    qs = Ticket.objects.filter(created_at__gte=since)
    by_status = list(qs.values("status").annotate(n=Count("id")).order_by("-n"))
    by_origin = list(qs.values("origin").annotate(n=Count("id")).order_by("-n"))
    breached = qs.filter(sla_breached=True).count()
    openish = qs.filter(
        status__in=[
            Ticket.Status.OPEN,
            Ticket.Status.IN_ANALYSIS,
            Ticket.Status.WAITING_PART,
        ]
    ).count()

    resolved_ids = qs.filter(status__in=[Ticket.Status.RESOLVED, Ticket.Status.CLOSED]).values_list(
        "id", flat=True
    )
    events = (
        TicketEvent.objects.filter(
            ticket_id__in=resolved_ids,
            status_to__in=[Ticket.Status.RESOLVED, Ticket.Status.CLOSED],
        )
        .order_by("ticket_id", "created_at")
        .select_related("ticket")
    )
    seen: set = set()
    durations_h: list[float] = []
    for ev in events:
        if ev.ticket_id in seen:
            continue
        seen.add(ev.ticket_id)
        delta = (ev.created_at - ev.ticket.created_at).total_seconds() / 3600.0
        if delta >= 0:
            durations_h.append(delta)
    tmr_hours = round(sum(durations_h) / len(durations_h), 2) if durations_h else None

    return {
        "total": qs.count(),
        "openish": openish,
        "sla_breached": breached,
        "tmr_hours": tmr_hours,
        "by_status": by_status,
        "by_origin": by_origin,
    }


def _sales_ai_metrics(since) -> dict:
    ai_sources = [
        Order.AttributionSource.CHAT,
        Order.AttributionSource.DIAGNOSIS,
        Order.AttributionSource.PHOTO,
    ]
    orders = Order.objects.filter(created_at__gte=since)
    by_attr = list(
        orders.filter(attribution_source__in=ai_sources)
        .values("attribution_source")
        .annotate(n=Count("id"), revenue=Sum("total"))
        .order_by("-n")
    )
    for row in by_attr:
        row["revenue"] = float(row["revenue"] or 0)

    cross = CrossSellAttribution.objects.filter(created_at__gte=since)
    return {
        "ai_influenced_orders": orders.filter(attribution_source__in=ai_sources).count(),
        "ai_revenue": float(
            orders.filter(attribution_source__in=ai_sources).aggregate(s=Sum("total"))["s"] or 0
        ),
        "by_attribution": by_attr,
        "cross_sell_count": cross.count(),
        "cross_sell_by_source": list(cross.values("source").annotate(n=Count("id")).order_by("-n")),
        "total_orders": orders.count(),
    }


def _ai_cost_metrics(since) -> dict:
    chat_cost = ChatMessage.objects.filter(
        created_at__gte=since,
        role=ChatMessage.Role.ASSISTANT,
    ).aggregate(s=Sum("cost_estimate"))["s"] or Decimal("0")
    extraction_cost = ExtractionLog.objects.filter(created_at__gte=since).aggregate(
        s=Sum("cost_estimate")
    )["s"] or Decimal("0")
    chat_tokens = ChatMessage.objects.filter(
        created_at__gte=since,
        role=ChatMessage.Role.ASSISTANT,
    ).aggregate(tin=Sum("tokens_in"), tout=Sum("tokens_out"))
    return {
        "chat_usd": float(chat_cost),
        "extraction_usd": float(extraction_cost),
        "total_usd": float(chat_cost + extraction_cost),
        "chat_tokens_in": int(chat_tokens["tin"] or 0),
        "chat_tokens_out": int(chat_tokens["tout"] or 0),
        "extractions": ExtractionLog.objects.filter(created_at__gte=since).count(),
    }
