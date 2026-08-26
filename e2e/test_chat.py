"""E2E: chat stream básico (mock LLM) — T-P.6."""

from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.django_db(transaction=True)
def test_chat_stream_basic(page: Page, live_server, db):
    page.goto(f"{live_server.url}/assistente/chat/")
    expect(page.get_by_role("heading", name="Assistente de diagnóstico")).to_be_visible()

    page.fill("#tp-chat-input", "Qual a voltagem do capacitor de partida?")
    page.get_by_role("button", name="Enviar").click()

    # Sem modelo, o grafo pede contexto antes de consultar o manual.
    chat_body = page.locator("#tp-chat-body")
    expect(chat_body).to_contain_text("Qual é o produto?", timeout=20000)
