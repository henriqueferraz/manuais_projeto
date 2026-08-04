"""Mascaramento de PII em logs estruturados."""

from __future__ import annotations

import re
from typing import Any

_EMAIL = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
_CPF = re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")
_PHONE = re.compile(r"\b(?:\+?55\s?)?(?:\(?\d{2}\)?\s?)?\d{4,5}-?\d{4}\b")
_SENSITIVE_KEYS = frozenset(
    {
        "password",
        "token",
        "authorization",
        "secret",
        "cpf",
        "email",
        "phone",
        "telefone",
        "credit_card",
        "card_number",
    }
)


def _mask_str(value: str) -> str:
    value = _EMAIL.sub("[EMAIL]", value)
    value = _CPF.sub("[CPF]", value)
    value = _PHONE.sub("[PHONE]", value)
    return value


def mask_pii(logger: Any, method_name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    """Processor structlog: mascara PII em valores e chaves sensíveis."""
    del logger, method_name
    for key, value in list(event_dict.items()):
        if key.lower() in _SENSITIVE_KEYS:
            event_dict[key] = "[REDACTED]"
        elif isinstance(value, str):
            event_dict[key] = _mask_str(value)
    return event_dict
