"""Serviços de monitoramento consolidado (F7 / T-7.2)."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Sum
from django.utils import timezone

from apps.ai.models import ChatMessage, PhotoSearch
from apps.dashboard.models import OpsAlert
from apps.manuals.models import ExtractionLog
from apps.tickets.models import Ticket


@dataclass
class MonitoringSnapshot:
    health: dict
    failures: list
    queues: dict
    links: dict
    alerts: list
    uptime_note: str

    def to_dict(self) -> dict:
        return asdict(self)


def external_links() -> dict:
    return {
        "sentry": getattr(settings, "SENTRY_UI_URL", "") or "",
        "flower": getattr(settings, "FLOWER_URL", "") or "http://localhost:5555",
        "grafana": getattr(settings, "GRAFANA_URL", "") or "",
        "health": "/health/",
    }


def collect_monitoring(*, limit: int = 20) -> MonitoringSnapshot:
    since = timezone.now() - timedelta(hours=24)
    failures: list[dict] = []

    for log in ExtractionLog.objects.filter(
        status=ExtractionLog.Status.FAILED,
        updated_at__gte=since,
    ).order_by("-updated_at")[:limit]:
        failures.append(
            {
                "kind": "extraction",
                "id": str(log.pk),
                "message": (log.error_message or "extração falhou")[:240],
                "at": log.updated_at.isoformat(),
            }
        )

    for photo in PhotoSearch.objects.filter(
        status=PhotoSearch.Status.FAILED,
        updated_at__gte=since,
    ).order_by("-updated_at")[:limit]:
        failures.append(
            {
                "kind": "photo",
                "id": str(photo.pk),
                "message": (photo.error_message or "busca por foto falhou")[:240],
                "at": photo.updated_at.isoformat(),
            }
        )

    failures.sort(key=lambda x: x["at"], reverse=True)
    failures = failures[:limit]

    queues = {
        "extractions_pending": ExtractionLog.objects.filter(
            status__in=[
                ExtractionLog.Status.PENDING,
                ExtractionLog.Status.RUNNING,
            ]
        ).count(),
        "photos_pending": PhotoSearch.objects.filter(
            status__in=[PhotoSearch.Status.PENDING, PhotoSearch.Status.RUNNING]
        ).count(),
        "tickets_breached": Ticket.objects.filter(
            sla_breached=True,
            status__in=[
                Ticket.Status.OPEN,
                Ticket.Status.IN_ANALYSIS,
                Ticket.Status.WAITING_PART,
            ],
        ).count(),
        "awaiting_review": ExtractionLog.objects.filter(
            status=ExtractionLog.Status.AWAITING_REVIEW
        ).count(),
    }

    alerts = [
        {
            "id": str(a.pk),
            "severity": a.severity,
            "title": a.title,
            "message": a.message,
            "channel": a.channel,
            "acknowledged": a.acknowledged,
            "created_at": a.created_at.isoformat(),
        }
        for a in OpsAlert.objects.filter(acknowledged=False).order_by("-created_at")[:limit]
    ]

    return MonitoringSnapshot(
        health={"status": "ok", "checked_at": timezone.now().isoformat()},
        failures=failures,
        queues=queues,
        links=external_links(),
        alerts=alerts,
        uptime_note="Probe local /health/ OK. Histórico longo via Grafana (se configurado).",
    )


def raise_ops_alert(
    *,
    kind: str,
    severity: str,
    title: str,
    message: str,
    payload: dict | None = None,
    notify: bool = True,
) -> OpsAlert:
    alert = OpsAlert.objects.create(
        kind=kind,
        severity=severity,
        title=title[:200],
        message=message[:4000],
        payload=payload or {},
        channel="panel+email",
    )
    if notify:
        _dispatch_alert(alert)
    return alert


def _dispatch_alert(alert: OpsAlert) -> None:
    """E-mail ops + webhook Slack opcional."""
    import structlog

    log = structlog.get_logger(__name__)
    recipients = getattr(settings, "OPS_ALERT_EMAILS", []) or []
    if isinstance(recipients, str):
        recipients = [e.strip() for e in recipients.split(",") if e.strip()]
    if recipients:
        send_mail(
            subject=f"[TechParts][{alert.severity}] {alert.title}",
            message=alert.message,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@techparts.local"),
            recipient_list=list(recipients),
            fail_silently=True,
        )

    webhook = getattr(settings, "SLACK_WEBHOOK_URL", "") or ""
    if webhook.startswith("https://"):
        try:
            import json
            from urllib import request as urlrequest

            body = json.dumps(
                {"text": f"*{alert.severity.upper()}* — {alert.title}\n{alert.message}"}
            ).encode("utf-8")
            req = urlrequest.Request(
                webhook,
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urlrequest.urlopen(req, timeout=5)  # nosec B310
            alert.channel = "panel+email+slack"
            alert.save(update_fields=["channel", "updated_at"])
        except Exception as exc:  # noqa: BLE001
            log.warning("slack_webhook_failed", error=str(exc)[:200])


def scan_and_emit_alerts() -> list[OpsAlert]:
    """Varredura periódica: custo IA, budget tokens, SLA, falhas recorrentes."""
    created: list[OpsAlert] = []
    since = timezone.now() - timedelta(hours=24)
    cost_threshold = Decimal(str(getattr(settings, "AI_COST_ALERT_USD", 5.0)))

    chat_cost = ChatMessage.objects.filter(
        created_at__gte=since,
        role=ChatMessage.Role.ASSISTANT,
    ).aggregate(s=Sum("cost_estimate"))["s"] or Decimal("0")
    if chat_cost >= cost_threshold:
        created.append(
            raise_ops_alert(
                kind=OpsAlert.Kind.COST,
                severity=OpsAlert.Severity.WARNING,
                title="Custo de IA acima do limiar (24h)",
                message=f"Custo estimado de chat/RAG nas últimas 24h: US$ {chat_cost:.4f}",
                payload={"chat_cost": float(chat_cost)},
            )
        )

    # Budget diário de tokens (T-P.2) — aviso a 80% e crítico a 100%
    from django.core.cache import cache

    daily_budget = int(getattr(settings, "AI_TOKEN_BUDGET_DAILY", 0) or 0)
    if daily_budget > 0:
        used = int(cache.get("ai-token-budget:daily", 0) or 0)
        ratio = used / daily_budget
        if ratio >= 1.0:
            created.append(
                raise_ops_alert(
                    kind=OpsAlert.Kind.COST,
                    severity=OpsAlert.Severity.CRITICAL,
                    title="Budget diário de tokens esgotado",
                    message=f"Tokens usados: {used}/{daily_budget}.",
                    payload={"used": used, "budget": daily_budget},
                )
            )
        elif ratio >= 0.8:
            created.append(
                raise_ops_alert(
                    kind=OpsAlert.Kind.COST,
                    severity=OpsAlert.Severity.WARNING,
                    title="Budget diário de tokens acima de 80%",
                    message=f"Tokens usados: {used}/{daily_budget} ({ratio:.0%}).",
                    payload={"used": used, "budget": daily_budget, "ratio": ratio},
                )
            )

    breached = Ticket.objects.filter(
        sla_breached=True,
        status__in=[
            Ticket.Status.OPEN,
            Ticket.Status.IN_ANALYSIS,
            Ticket.Status.WAITING_PART,
        ],
    ).count()
    if breached:
        created.append(
            raise_ops_alert(
                kind=OpsAlert.Kind.SLA,
                severity=OpsAlert.Severity.CRITICAL,
                title=f"{breached} chamado(s) com SLA estourado",
                message="Há chamados abertos com sla_breached=True. Ver painel de suporte.",
                payload={"count": breached},
            )
        )

    failed_ext = ExtractionLog.objects.filter(
        status=ExtractionLog.Status.FAILED,
        updated_at__gte=since,
    ).count()
    if failed_ext >= 3:
        created.append(
            raise_ops_alert(
                kind=OpsAlert.Kind.ERROR,
                severity=OpsAlert.Severity.WARNING,
                title="Falhas recorrentes de extração",
                message=f"{failed_ext} extrações falharam nas últimas 24h.",
                payload={"count": failed_ext},
            )
        )

    return created


def simulate_incident(*, title: str = "Incidente simulado (F7)") -> OpsAlert:
    """Gera alerta artificial para aceite T-7.2."""
    return raise_ops_alert(
        kind=OpsAlert.Kind.INCIDENT,
        severity=OpsAlert.Severity.CRITICAL,
        title=title,
        message=("Incidente simulado para validar o painel de monitoramento e canais de alerta."),
        payload={"simulated": True},
    )
