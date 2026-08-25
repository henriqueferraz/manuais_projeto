"""Gancho low-code (n8n/Make): snapshot e ingestão de relatório."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class LowcodeReportIn(BaseModel):
    """Payload que o n8n/Make envia de volta para o painel ops."""

    source: str = Field(default="n8n", max_length=32)
    title: str = Field(default="Relatório low-code", max_length=200)
    message: str = Field(default="", max_length=4000)
    failures_24h: int = Field(default=0, ge=0)
    queues: dict[str, Any] = Field(default_factory=dict)
    severity: str = Field(default="warning", max_length=16)


def parse_lowcode_report(raw: dict[str, Any]) -> LowcodeReportIn:
    """Valida o JSON do fluxo visual; levanta ValidationError se inválido."""
    return LowcodeReportIn.model_validate(raw)


def snapshot_should_alert(queues: dict, failures_24h: int) -> bool:
    """Regra determinística no app: o n8n só orquestra, não decide o domínio."""
    return (
        failures_24h > 0
        or int(queues.get("tickets_breached") or 0) > 0
        or int(queues.get("awaiting_review") or 0) > 0
    )
