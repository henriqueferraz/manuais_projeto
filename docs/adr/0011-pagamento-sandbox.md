# ADR 0011 — Pagamento sandbox Stripe / Mercado Pago

- **Status:** Aceito (atualizado)
- **Data:** 2026-08-07 · update Preference: 2026-08-13
- **Pilares:** P05, P15
- **Fase:** T-P.4

## Contexto

Cobrança tokenizada já existia (`PAYMENT_PROVIDER=stripe|mercadopago`). Em 2026-08
passamos a oferecer **Checkout Pro (Preference)** como modo padrão do Mercado Pago.

## Decisão

1. CI/local: `PAYMENT_PROVIDER=mock`.
2. Staging: `PAYMENT_PROVIDER=stripe` **ou** `mercadopago`.
3. Mercado Pago:
   - **`MERCADOPAGO_CHECKOUT_MODE=preference`** (default): cria Preference, redireciona ao Checkout Pro; confirmação via `notification_url` + `back_urls`.
   - **`MERCADOPAGO_CHECKOUT_MODE=token`**: Payments API com card token (fluxo anterior).
4. `PUBLIC_BASE_URL` define `back_urls` e `notification_url` (ex.: `https://staging.exemplo.com`).
   Em `http://localhost`/`127.0.0.1`, `notification_url` e `auto_return` são omitidos (API MP rejeita).
5. Webhooks Stripe com assinatura; MP IPN autenticado ao **buscar o pagamento** com `MERCADOPAGO_ACCESS_TOKEN`.
6. Smoke: Preference via `create_mercadopago_preference` / `manage.py smoke_live_integrations`.

## Consequências

+ Checkout Pro sem coletar cartão no site.  
+ Token API permanece disponível se necessário.  
− `PUBLIC_BASE_URL` precisa ser HTTPS público em staging para o MP chamar o webhook.
