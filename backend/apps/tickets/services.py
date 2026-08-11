"""Serviços de chamados e cross-sell."""

from __future__ import annotations

from django.core.mail import send_mail
from django.db import transaction
from django.template.loader import render_to_string
from django.utils import timezone

from apps.compatibility.models import Compatibility
from apps.notifications.models import EmailLog
from apps.products.models import Product
from apps.tickets.models import CrossSellAttribution, Ticket, TicketEvent


@transaction.atomic
def create_ticket(
    *,
    email: str,
    title: str,
    description: str,
    equipment: str = "",
    user=None,
    origin: str = Ticket.Origin.SITE,
    priority: str = Ticket.Priority.MEDIUM,
    order=None,
) -> Ticket:
    ticket = Ticket.objects.create(
        code=Ticket.next_code(),
        email=email,
        title=title,
        description=description,
        equipment=equipment,
        user=user if getattr(user, "is_authenticated", False) else None,
        origin=origin,
        priority=priority,
        order=order,
        status=Ticket.Status.OPEN,
    )
    TicketEvent.objects.create(
        ticket=ticket,
        author=user if getattr(user, "is_authenticated", False) else None,
        note="Chamado aberto pelo cliente.",
        status_to=Ticket.Status.OPEN,
    )
    notify_ticket_status(ticket, previous="")
    return ticket


@transaction.atomic
def update_ticket_status(
    ticket: Ticket,
    *,
    new_status: str,
    note: str = "",
    author=None,
) -> Ticket:
    previous = ticket.status
    if previous == new_status and not note:
        return ticket
    ticket.status = new_status
    ticket.save(update_fields=["status", "updated_at"])
    TicketEvent.objects.create(
        ticket=ticket,
        author=author,
        note=note or f"Status alterado para {ticket.get_status_display()}.",
        status_from=previous,
        status_to=new_status,
    )
    notify_ticket_status(ticket, previous=previous)
    return ticket


def notify_ticket_status(ticket: Ticket, *, previous: str) -> None:
    subject = f"[{ticket.code}] Atualização: {ticket.get_status_display()}"
    body = render_to_string(
        "emails/ticket_status.txt",
        {"ticket": ticket, "previous": previous, "brand_name": "TechParts AI"},
    )
    log = EmailLog.objects.create(
        to_email=ticket.email,
        subject=subject,
        kind=EmailLog.Kind.OTHER,
        status=EmailLog.Status.QUEUED,
    )
    try:
        send_mail(subject, body, None, [ticket.email], fail_silently=False)
        log.status = EmailLog.Status.SENT
        log.save(update_fields=["status", "updated_at"])
    except Exception as exc:  # noqa: BLE001
        log.status = EmailLog.Status.FAILED
        log.error_message = str(exc)[:2000]
        log.save(update_fields=["status", "error_message", "updated_at"])


def cross_sell_for_product(product: Product, *, limit: int = 12) -> list[Product]:
    """Sugestões na PDP a partir da tabela de compatibilidade."""
    if product.product_kind == Product.Kind.SPARE_PART:
        # outras peças do mesmo equipamento
        models = list(
            Compatibility.objects.filter(part_product=product).values_list(
                "equipment_brand", "equipment_model"
            )[:5]
        )
        if not models:
            return []
        q = Compatibility.objects.none()
        for brand, model in models:
            q = q | Compatibility.objects.filter(equipment_brand=brand, equipment_model=model)
        ids = (
            q.exclude(part_product=product)
            .values_list("part_product_id", flat=True)
            .distinct()[:limit]
        )
    else:
        ids = (
            Compatibility.objects.filter(
                equipment_brand__iexact=product.brand,
                equipment_model__icontains=product.model_code or product.sku,
            )
            .values_list("part_product_id", flat=True)
            .distinct()[:limit]
        )

    return list(
        Product.objects.filter(id__in=ids, status=Product.Status.PUBLISHED)
        .select_related("stock")
        .prefetch_related("translations", "images")
    )


def cross_sell_for_order(order, *, limit: int = 4) -> list[Product]:
    """Peças relacionadas aos itens do pedido (e-mail pós-compra)."""
    seen: set[int] = set()
    results: list[Product] = []
    for item in order.items.select_related("product"):
        if not item.product_id:
            continue
        for p in cross_sell_for_product(item.product, limit=limit):
            if p.id not in seen and p.id != item.product_id:
                seen.add(p.id)
                results.append(p)
            if len(results) >= limit:
                return results
    return results


def record_cross_sell_attribution(
    *,
    order,
    product: Product,
    source_product: Product | None = None,
    source: str = CrossSellAttribution.Source.PDP,
) -> CrossSellAttribution:
    return CrossSellAttribution.objects.create(
        order=order,
        product=product,
        source_product=source_product,
        source=source,
    )


def check_sla_breaches() -> int:
    """Marca e alerta tickets com SLA estourado."""
    now = timezone.now()
    qs = Ticket.objects.filter(
        sla_breached=False,
        sla_due_at__lt=now,
    ).exclude(status__in=[Ticket.Status.RESOLVED, Ticket.Status.CLOSED])
    count = 0
    for ticket in qs:
        ticket.sla_breached = True
        ticket.sla_alerted_at = now
        ticket.save(update_fields=["sla_breached", "sla_alerted_at", "updated_at"])
        TicketEvent.objects.create(
            ticket=ticket,
            note="Alerta SLA: prazo estourado.",
            is_internal=True,
            status_from=ticket.status,
            status_to=ticket.status,
        )
        # e-mail para o cliente + log (equipe vê no painel)
        notify_ticket_status(ticket, previous=ticket.status)
        count += 1
    return count
