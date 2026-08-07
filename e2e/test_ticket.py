"""E2E: abertura de chamado técnico (T-P.6)."""

from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.django_db(transaction=True)
def test_open_ticket(page: Page, live_server, db):
    page.goto(f"{live_server.url}/chamados/")
    expect(page.get_by_role("heading", name="Chamados Técnicos")).to_be_visible()

    page.fill("#id_email", "chamado-e2e@techparts.local")
    page.fill("#id_title", "Ventilador não liga — E2E")
    page.fill("#id_equipment", "VTE-02")
    page.fill("#id_description", "Equipamento não liga após queda de energia. Teste E2E.")
    page.get_by_role("button", name="Abrir chamado").click()

    expect(page.get_by_role("heading", name="Ventilador não liga — E2E")).to_be_visible(
        timeout=15000
    )
