# ADR 0011 — Pagamento sandbox Stripe / Mercado Pago

- **Status:** Aceito
- **Data:** 2026-08-07
- **Pilares:** P05, P15
- **Fase:** T-P.4

## Contexto

Cobrança tokenizada já existia em código (`PAYMENT_PROVIDER=stripe|mercadopago`). Faltava formalizar o contrato de staging e smoke.

## Decisão

1. CI/local: `PAYMENT_PROVIDER=mock`.
2. Staging: `PAYMENT_PROVIDER=stripe` (test keys) **ou** `mercadopago` (sandbox token).
3. UI continua enviando `payment_token` (PaymentMethod / card token) — Elements/Brick no front é opcional pós-smoke.
4. Webhooks com assinatura (`STRIPE_WEBHOOK_SECRET` / `MERCADOPAGO_WEBHOOK_SECRET`).
5. Smoke: `manage.py smoke_live_integrations` (imprime modos/credenciais e testa frete; sem charge real).

## Consequências

+ Sandbox real documentado.  
− Tokenização no browser ainda é manual/dev; PCI permanece no gateway.
