# Checkout

| | |
|---|---|
| **URLs** | `/checkout/` → frete → `/checkout/pagamento/` → sucesso |
| **Auth** | sessão (carrinho) |

## Pagamento

| `PAYMENT_PROVIDER` | Fluxo |
|---|---|
| `mock` | Form com `payment_token` (`tok_sandbox_4242` / `tok_fail`) |
| `stripe` | Token / PaymentMethod no form |
| `mercadopago` + `MERCADOPAGO_CHECKOUT_MODE=preference` | **Checkout Pro**: Preference + redirect |
| `mercadopago` + `MERCADOPAGO_CHECKOUT_MODE=transparent` | **Checkout Transparente**: Card Payment Brick no site |
| `mercadopago` + `MERCADOPAGO_CHECKOUT_MODE=token` | Token manual (legado / smoke) |

### Preference (Checkout Pro)

1. Cliente conclui endereço e frete.
2. Em `/checkout/pagamento/` clica **Pagar com Mercado Pago** (form com `hx-disable` — redirect externo).
3. Backend cria `Order` + `Payment` pendente e Preference (`sdk.preference().create`).
4. Redirect full-page para `init_point` / `sandbox_init_point` (`302` ou header `HX-Redirect` se o POST veio via HTMX).
5. `back_urls.success` → `/checkout/sucesso/<uuid>/` (sync via `payment_id`).
6. `notification_url` → `/checkout/webhooks/pagamento/` (IPN; busca pagamento na API).

CSP: `form-action` inclui domínios MP — sem isso o browser **bloqueia** o 302 do form.

Sandbox: se o browser já tem sessão **real** do ML/MP, o Checkout Pro mostra o erro 145 sem pedir login. Use janela anônima + usuário **comprador** de teste (`TESTUSER…`), não o vendedor.

### Checkout Transparente (Card Payment Brick)

1. `MERCADOPAGO_CHECKOUT_MODE=transparent` + `MERCADOPAGO_PUBLIC_KEY` + Access Token.
2. Brick (`sdk.mercadopago.com/js/v2`) tokeniza o cartão no browser.
3. `POST /checkout/pagamento/` JSON (`token`, `installments`, `payment_method_id`, `issuer_id`, `payer`…).
4. Backend: `build_order_from_cart` + `pay_order(..., charge_extra=payload)` → Payments API.
5. Resposta `{ ok, redirect }` → página de sucesso.

Cartões de teste: titular **`APRO`** (aprovado), CPF `12345678909` — ver conta sandbox MP.

**Credenciais:** Checkout Transparente / Bricks / Payments API exige Access Token e Public Key de **teste** com prefixo `TEST-` (painel MP → Sua integração → Credenciais de teste). Credenciais `APP_USR-` servem para Checkout Pro (Preference), mas a API de pagamento com cartão responde `Unauthorized use of live credentials`.

Env: `MERCADOPAGO_ACCESS_TOKEN`, `MERCADOPAGO_PUBLIC_KEY`, `PUBLIC_BASE_URL`.

Em local (`http://127.0.0.1`), Preference omite `notification_url`/`auto_return`. Transparente não precisa de URL pública para cobrar.

Checkout Transparente: Brick carrega via `static/checkout/mp_card_brick.js` (base + `htmx:afterSettle`), porque o frete usa `hx-boost` e não inclui `extra_js`.
