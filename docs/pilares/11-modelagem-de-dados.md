# Pilar 11 — Modelagem de dados (Django + PostgreSQL)

> **Parte 2 — Pilares Específicos do Projeto** · Fonte-mestre: [`pilares-app-ia-vendas-pecas.md`](../pilares-app-ia-vendas-pecas.md)

## Definição do pilar

Product, Manual, ManualChunk (pgvector), ExtractionLog — e modelos de apoio do domínio.

## Núcleo do pilar

| Model | Papel |
|---|---|
| `Product` | SKU, specs, preço, estoque, i18n; `category` FK (principal) + `categories` M2M |
| `Manual` | FK / referência ao PDF no R2 |
| `ManualChunk` | Trechos com embedding (pgvector) + metadados |
| `ExtractionLog` | Histórico de execuções da IA, revisão humana, timestamps |

Código: `backend/apps/products/models.py`, `catalog/models.py`, `manuals/`, `ai/`.  
Multi-categoria no form: [`../pages/dashboard-produto.md`](../pages/dashboard-produto.md).  
Schema F1 (histórico + evolução): [`../fase-1-schema-produto.md`](../fase-1-schema-produto.md).

## Models de domínio (consolidados do plano)

- **Estoque** — disponível, reservado, mínimo para alerta
- **Compatibilidade** — modelo × peça (verificador e cross-sell)
- **Ticket** — chamado técnico (status, origem, SLA, histórico)
- **ChatFeedback** — 👍/👎 + motivo
- **SubscriptionPlan** — assinatura de manutenção (fase 8)
- **PartnerService** — assistência parceira (fase 8)
- **ReturnRequest** — trocas/devoluções
- **Coupon** / **ProductPromotion** — cupons/promoções (por produto ou categoria)
- Role/Permission — RBAC configurável
- Audit log — django-simple-history

## PostgreSQL + pgvector

- Postgres: usuários, pedidos, produtos, estoque, categorias, chamados, assinaturas, compatibilidade
- pgvector: embeddings, chunks, busca semântica
- Índices em SKU e compatibilidade; HNSW/IVFFlat no vetor desde fase 4
- Schema já preparado para i18n (`ProductTranslation`)

## Fontes

- `pilares-app-ia-vendas-pecas.md` — Pilar 11
- `plan.md` — Banco de Dados
- `fase-1-schema-produto.md` — schema inicial + evolução M2M
- Models em `backend/apps/*/models.py`
