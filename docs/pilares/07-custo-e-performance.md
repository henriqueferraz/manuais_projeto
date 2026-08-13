# Pilar 07 — Custo e performance

> **Parte 1 — Pilares Gerais para Apps de IA** · Fonte-mestre: [`pilares-app-ia-vendas-pecas.md`](../pilares-app-ia-vendas-pecas.md)

## Definição do pilar

Escolha do modelo certo; monitoramento de latência; otimização de prompts/tokens.

## Princípios

- Custo de IA é **métrica de primeira classe**
- Toda funcionalidade com modelo/serviço pago entra com estimativa de custo + rate limiting
- Menos tokens = mais rápido e barato (prompts enxutos; extrair texto do PDF antes de mandar imagem)

## Monitoramento

- LangSmith: tokens, latência e custo por chamada/produto/cliente
- Alertas de gasto anômalo (loop no chat ou na extração)
- Dashboard interno com custo de IA no período (extração vs chat)

## Ordem de grandeza (MVP, baixo volume)

| Serviço | Estimativa |
|---|---|
| OpenAI (chat / embeddings / extração) | R$ 300–1.500/mês (ordem de grandeza; depende do volume) |
| Hospedagem | R$ 150–600/mês |
| Cloudflare R2 | R$ 10–50/mês |
| Observabilidade | R$ 0–150/mês |

Custos variáveis (API + gateway) tendem a pesar mais que fixos conforme o volume cresce.

## Performance

- Cache Redis em catálogo e compatibilidade
- Índices (SKU, compatibilidade) e índice vetorial (HNSW/IVFFlat) desde a fase 4
- Celery para não bloquear request em extração/embeddings/imagem

## Fontes

- `constitution.md` — Artigos 2.4 e 9
- `plano-ecommerce-ia-pecas.md` — Custo estimado, Observabilidade, Cache
