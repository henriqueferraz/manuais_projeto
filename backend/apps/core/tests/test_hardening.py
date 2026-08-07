"""Testes de hardening T-P.2 (budget de tokens e alertas)."""

from __future__ import annotations

import pytest
from django.core.cache import cache
from django.test import override_settings


def test_record_token_usage_increments_daily_counter():
    from apps.core.ratelimit import record_token_usage

    cache.clear()
    with override_settings(AI_TOKEN_BUDGET_DAILY=1000):
        record_token_usage(100)
        record_token_usage(50)
        assert int(cache.get("ai-token-budget:daily", 0)) == 150


def test_production_guards_logic():
    """Regras de boot de produção (espelho de settings.production)."""
    fragments = ("change-me", "dev-only", "flower-local", "insecure")

    def validate(*, secret, hosts, csrf, axes, budget):
        if not secret or any(f in secret.lower() for f in fragments):
            raise RuntimeError("SECRET_KEY")
        if len(secret) < 50:
            raise RuntimeError("SECRET_KEY length")
        if not hosts or hosts == ["localhost", "127.0.0.1"]:
            raise RuntimeError("ALLOWED_HOSTS")
        if not csrf:
            raise RuntimeError("CSRF")
        if not axes:
            raise RuntimeError("AXES")
        if int(budget or 0) <= 0:
            raise RuntimeError("BUDGET")

    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        validate(
            secret="dev-only",
            hosts=["shop.example.com"],
            csrf=["https://shop.example.com"],
            axes=True,
            budget=1,
        )

    with pytest.raises(RuntimeError, match="BUDGET"):
        validate(
            secret="a" * 50,
            hosts=["shop.example.com"],
            csrf=["https://shop.example.com"],
            axes=True,
            budget=0,
        )

    validate(
        secret="a" * 50,
        hosts=["shop.example.com"],
        csrf=["https://shop.example.com"],
        axes=True,
        budget=1000,
    )


@pytest.mark.django_db
def test_scan_alerts_includes_token_budget_warning(settings):
    from apps.dashboard.services.monitoring import scan_and_emit_alerts

    cache.clear()
    settings.AI_TOKEN_BUDGET_DAILY = 100
    # Evitar alerta de custo por chat zerado vs limiar baixo em fixtures
    settings.AI_COST_ALERT_USD = 9999
    cache.set("ai-token-budget:daily", 85, timeout=86400)
    created = scan_and_emit_alerts()
    titles = [a.title for a in created]
    assert any("80%" in t or "Budget" in t for t in titles)


def test_clamav_tcp_settings_present(settings):
    assert hasattr(settings, "CLAMAV_HOST")
    assert hasattr(settings, "CLAMAV_PORT")
