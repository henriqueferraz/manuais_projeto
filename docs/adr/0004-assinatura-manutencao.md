# ADR 0004 — Assinatura de manutenção preventiva

- **Status:** Aceito
- **Data:** 2026-08-06
- **Pilares:** P01, P11

## Contexto

Modelo de receita recorrente previsto no schema de pilares (`SubscriptionPlan`).

## Decisão

1. App `subscriptions` com `SubscriptionPlan` e `Subscription` (status, período, usuário/e-mail).
2. Checkout de assinatura na F8 = **stub** (criar assinatura `active` em mock; gateway recorrente em ADR futura).
3. UI storefront listando planos + “Assinar (mock)”.

## Consequências

+ Dados prontos para billing recorrente.  
− Cobrança real Stripe/MP Subscriptions fica para iteração pós-F8.
