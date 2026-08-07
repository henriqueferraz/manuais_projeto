# ADR 0008 — Escala de dados, índices e orçamento de tokens

- **Status:** Aceito
- **Data:** 2026-08-06
- **Pilares:** P07, P11, P14

## Contexto

Volume maior de catálogo/chat exige índices e limites de custo.

## Decisão

1. Command `seed_scale_catalog` com categorias e marcas adicionais (Mondial, Britânia, Electrolux, Consul, Philco…).
2. Índices compostos extras em Product/Order/Ticket (brand+status, attribution, sla).
3. Setting opcional `DATABASE_READ_REPLICA_URL` + `PrimaryReplicaRouter` (leituras → `replica`).
4. `AI_TOKEN_BUDGET_DAILY` + contador em cache; rejeitar requests quando estourar.

## Consequências

+ Pronto para crescimento sem redesign.  
− Read replica só ativa com Postgres + URL — default continua primary-only.

## Atualização T-P.5 (2026-08-07)

- Router `apps.core.db_router.PrimaryReplicaRouter` ativo quando `DATABASE_READ_REPLICA_URL` está setada.
- Índice `ProductTranslation(locale, name)` para listagens multi-idioma pós-`seed_scale_catalog`.
- Revisão de índices Product/Order/Ticket: compostos F8 mantidos; sem mudança adicional necessária até volume real de produção (ADR “não necessário ainda” para novos índices de pedido/ticket).
