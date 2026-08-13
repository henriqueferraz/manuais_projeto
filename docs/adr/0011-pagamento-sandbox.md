# ADR 0011 — Pagamento sandbox Stripe / Mercado Pago

- **Status:** Aceito (atualizado)
- **Data:** 2026-08-07 · Preference: 2026-08-13 · Transparente: 2026-08-13
- **Pilares:** P05, P15
- **Fase:** T-P.4

## Contexto

Cobrança tokenizada (`PAYMENT_PROVIDER=stripe|mercadopago`). Em 2026-08:
Checkout Pro (Preference) e Checkout Transparente (Card Payment Brick).

## Decisão

1. CI/local default de testes: `PAYMENT_PROVIDER=mock`.
2. Staging: `PAYMENT_PROVIDER=stripe` **ou** `mercadopago`.
3. Mercado Pago (`MERCADOPAGO_CHECKOUT_MODE`):
   - **`preference`**: Preference + redirect Checkout Pro.
   - **`transparent`**: Card Payment Brick no site; Payments API com token + parcelas.
   - **`token`**: campo manual de card token (legado).
4. Credenciais: `MERCADOPAGO_ACCESS_TOKEN` + `MERCADOPAGO_PUBLIC_KEY`.
   - Checkout Pro (`preference`): `APP_USR-` ok.
   - Transparente / Bricks: usar par **`TEST-`** (credenciais de teste); `APP_USR-` na Payments API retorna `Unauthorized use of live credentials`.
5. `PUBLIC_BASE_URL` para Preference (`back_urls` / IPN). Em localhost HTTP, IPN/`auto_return` omitidos.
6. CSP: `form-action` e `script-src`/`connect-src`/`frame-src` liberam hosts MP.
7. Smoke: Preference / Brick + `manage.py smoke_live_integrations`.

## Consequências

+ Pro sem coletar cartão; Transparente sem sair do site (PCI via Brick).  
+ Token API permanece disponível.  
− Transparente exige Public Key e CSP mais permissivo para SDK MP.
