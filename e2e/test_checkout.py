"""E2E: checkout → pagamento mock (T-P.6)."""

from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.django_db(transaction=True)
def test_checkout_payment_mock(page: Page, live_server, e2e_product):
    base = live_server.url
    page.goto(f"{base}/catalogo/{e2e_product.slug}/")
    expect(page.get_by_role("heading", level=1)).to_be_visible()

    page.get_by_role("button", name="Adicionar ao carrinho").click()
    # hx-post: aguarda resposta antes de ir ao checkout
    page.wait_for_timeout(800)
    page.goto(f"{base}/carrinho/")
    expect(page.locator("body")).to_contain_text("E2E", timeout=10000)

    page.goto(f"{base}/checkout/")
    expect(page.get_by_role("heading", name="Endereço de entrega")).to_be_visible(timeout=15000)

    page.fill("#id_email", "e2e@techparts.local")
    page.fill("#id_shipping_name", "Cliente E2E")
    page.fill("#id_shipping_phone", "11988887777")
    page.fill("#id_shipping_cep", "01310100")
    page.fill("#id_shipping_street", "Av Paulista")
    page.fill("#id_shipping_number", "1000")
    page.fill("#id_shipping_district", "Bela Vista")
    page.fill("#id_shipping_city", "São Paulo")
    page.fill("#id_shipping_state", "SP")
    page.get_by_role("button", name="Continuar para frete").click()

    expect(page.get_by_role("heading", name="Frete")).to_be_visible(timeout=20000)
    page.locator('input[name="shipping_option_id"]').first.check()
    page.get_by_role("button", name="Continuar para pagamento").click()

    expect(page.get_by_role("heading", name="Pagamento")).to_be_visible(timeout=20000)
    page.fill("#id_payment_token", "tok_sandbox_4242")
    page.get_by_role("button", name="Pagar e finalizar").click()

    expect(page.get_by_role("heading", name="Pedido confirmado")).to_be_visible(timeout=25000)
