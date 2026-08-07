# ADR 0008 — Escala de dados, índices e orçamento de tokens

- **Status:** Aceito
- **Data:** 2026-08-06
- **Pilares:** P07, P11, P14

## Contexto

Volume maior de catálogo/chat exige índices e limites de custo.

## Decisão

1. Command `seed_scale_catalog` com categorias e marcas adicionais (Mondial, Britânia, Electrolux, Consul, Philco…).
2. Índices compostos extras em Product/Order/Ticket (brand+status, attribution, sla).
3. Setting opcional `DATABASE_READ_REPLICA_URL` documentado (router futuro; não obrigatório no MVP).
4. `AI_TOKEN_BUDGET_DAILY` + contador em cache; rejeitar requests quando estourar.

## Consequências

+ Pronto para crescimento sem redesign.  
− Read replica só ativa com Postgres + router — default continua primary-only.
