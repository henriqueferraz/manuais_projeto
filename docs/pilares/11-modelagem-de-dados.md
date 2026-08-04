# Pilar 11 — Modelagem de dados (Django + PostgreSQL)

> **Parte 2 — Pilares Específicos do Projeto** · Fonte-mestre: [`pilares-app-ia-vendas-pecas.md`](../pilares-app-ia-vendas-pecas.md)

## Definição do pilar

Product, Manual, ManualChunk (pgvector), ExtractionLog — e modelos de apoio do domínio.

## Núcleo do pilar

| Model | Papel |
|---|---|
| `Product` | Dados do produto (SKU, specs, preço, estoque, i18n-ready) |
| `Manual` | FK / referência ao PDF no R2 |
| `ManualChunk` | Trechos com embedding (pgvector) + metadados |
| `ExtractionLog` | Histórico de execuções da IA, revisão humana, timestamps |

## Models de domínio (consolidados do plano)

- **Estoque** — disponível, reservado, mínimo para alerta
- **Compatibilidade** — modelo × peça (verificador e cross-sell)
- **Ticket** — chamado técnico (status, origem, SLA, histórico)
- **ChatFeedback** — 👍/👎 + motivo
- **SubscriptionPlan** — assinatura de manutenção (fase 8)
- **PartnerService** — assistência parceira (fase 8)
- **ReturnRequest** — trocas/devoluções
- **Coupon** — cupons/promoções
- Role/Permission — RBAC configurável
- Audit log — django-simple-history ou equivalente

## PostgreSQL + pgvector

- Postgres: usuários, pedidos, produtos, estoque, categorias, chamados, assinaturas, compatibilidade
- pgvector: embeddings, chunks, busca semântica
- Índices em SKU e compatibilidade; HNSW/IVFFlat no vetor desde fase 4
- Schema já preparado para i18n

## Tipos de referência no protótipo

Ver `src/types.ts`: `Product`, `ManualReview`, `Ticket`, `ChatMessage`, `DiagnosticCardData`.

## Fontes

- `pilares-app-ia-vendas-pecas.md` — Pilar 11
- `plan.md` — Banco de Dados
- `plano-ecommerce-ia-pecas.md` — Dados
- `src/types.ts`
