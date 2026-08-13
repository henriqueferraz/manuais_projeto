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
| `mercadopago` + `MERCADOPAGO_CHECKOUT_MODE=preference` (default) | **Checkout Pro**: cria Preference e redireciona ao MP |
| `mercadopago` + `MERCADOPAGO_CHECKOUT_MODE=token` | Payments API com card token (legado) |

### Preference (Checkout Pro)

1. Cliente conclui endereço e frete.
2. Em `/checkout/pagamento/` clica **Pagar com Mercado Pago**.
3. Backend cria `Order` + `Payment` pendente e Preference (`sdk.preference().create`).
4. Redirect para `init_point` / `sandbox_init_point`.
5. `back_urls.success` → `/checkout/sucesso/<uuid>/` (sync via `payment_id`).
6. `notification_url` → `/checkout/webhooks/pagamento/` (IPN; busca pagamento na API).

Env: `MERCADOPAGO_ACCESS_TOKEN`, `PUBLIC_BASE_URL`.

Em local (`http://127.0.0.1`), a Preference **omite** `notification_url` e `auto_return` (o MP exige HTTPS público). A confirmação no return usa `payment_id` / `collection_id` na URL de sucesso. Em staging, use `PUBLIC_BASE_URL=https://...`.

Código: `apps.checkout.payments.create_mercadopago_preference`, `start_mercadopago_preference_checkout`.
