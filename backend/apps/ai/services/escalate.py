"""Escalonamento de chat → chamado humano (F5.4)."""

from __future__ import annotations

import structlog
from django.db import transaction

from apps.ai.models import ChatFeedback, ChatMessage, ChatSession
from apps.tickets.models import Ticket
from apps.tickets.services import create_ticket

logger = structlog.get_logger(__name__)


@transaction.atomic
def register_feedback(
    message: ChatMessage,
    *,
    vote: str,
    reason: str = "",
    email: str = "",
    user=None,
) -> ChatFeedback:
    """Persiste 👍/👎; 👎 (ou 2 seguidos) abre Ticket com histórico."""
    if message.role != ChatMessage.Role.ASSISTANT:
        raise ValueError("Feedback só se aplica a respostas da assistente.")

    session = message.session
    feedback, _ = ChatFeedback.objects.update_or_create(
        message=message,
        defaults={
            "vote": vote,
            "reason": reason[:2000],
            "chunk_ids_snapshot": list(message.chunk_ids or []),
        },
    )

    if vote == ChatFeedback.Vote.DOWN:
        session.consecutive_downvotes += 1
    else:
        session.consecutive_downvotes = 0
    session.save(update_fields=["consecutive_downvotes", "updated_at"])

    should_escalate = vote == ChatFeedback.Vote.DOWN and (
        session.consecutive_downvotes >= 2
        or (message.confidence is not None and message.confidence < 0.35)
        or not message.found_in_manual
    )
    # Também escala no primeiro 👎 se o usuário pedir explicitamente
    if vote == ChatFeedback.Vote.DOWN and reason.strip().lower().startswith("escalar"):
        should_escalate = True

    if should_escalate and not feedback.created_ticket_id:
        ticket = escalate_session(
            session,
            trigger_message=message,
            reason=reason,
            email=email,
            user=user,
        )
        feedback.created_ticket = ticket
        feedback.save(update_fields=["created_ticket"])

    logger.info(
        "chat_feedback",
        message_id=str(message.pk),
        vote=vote,
        escalated=bool(feedback.created_ticket_id),
    )
    return feedback


@transaction.atomic
def escalate_session(
    session: ChatSession,
    *,
    trigger_message: ChatMessage | None = None,
    reason: str = "",
    email: str = "",
    user=None,
) -> Ticket:
    if session.escalated_ticket_id:
        return session.escalated_ticket

    history = _format_history(session)
    contact = email or getattr(user, "email", "") or "cliente@techparts.local"
    title = session.title or "Suporte via chat IA"
    description = (
        "Chamado aberto automaticamente a partir do chat de suporte.\n\n"
        f"Motivo do feedback: {reason or 'resposta marcada como não útil'}\n\n"
        f"Histórico da conversa:\n{history}"
    )
    if trigger_message and trigger_message.sources:
        description += "\n\nFontes usadas na última resposta:\n"
        for src in trigger_message.sources[:5]:
            description += (
                f"- {src.get('section', '—')} "
                f"(pág. {src.get('page') or '—'}, score={src.get('score')})\n"
            )

    ticket = create_ticket(
        email=contact,
        title=f"[Chat] {title}"[:200],
        description=description[:8000],
        equipment=(session.product.model_code if session.product_id else ""),
        user=user,
        origin=Ticket.Origin.CHAT,
        priority=(
            Ticket.Priority.HIGH
            if (trigger_message and not trigger_message.found_in_manual)
            else Ticket.Priority.MEDIUM
        ),
    )
    session.escalated_ticket = ticket
    session.save(update_fields=["escalated_ticket", "updated_at"])
    return ticket


def _format_history(session: ChatSession) -> str:
    lines: list[str] = []
    for msg in session.messages.order_by("created_at"):
        label = "Cliente" if msg.role == ChatMessage.Role.USER else "Assistente"
        lines.append(f"{label}: {msg.content}")
    return "\n".join(lines) if lines else "(sem mensagens)"
