# ADR 0004 — Assinatura de manutenção preventiva

- **Status:** Aceito
- **Data:** 2026-08-06
- **Pilares:** P01, P11

## Contexto

Modelo de receita recorrente previsto no schema de pilares (`SubscriptionPlan`).

## Decisão

1. App `subscriptions` com `SubscriptionPlan` e `Subscription` (status, período, usuário/e-mail).
2. Checkout de assinatura: `SUBSCRIPTION_BILLING_MODE=mock|stripe|mercadopago`.
3. UI storefront lista planos + assinar; live exige `payment_token` / `stripe_price_id`.
4. Persistência local guarda `billing_provider` + `provider_subscription_id`.

## Consequências

+ Dados e billing plugáveis.  
− Webhooks de recorrência (invoice.paid / preapproval) ainda são evolução futura.

## Atualização T-P.4 (2026-08-07)

Billing real via `apps/subscriptions/billing.py`. CI/local permanece mock.
