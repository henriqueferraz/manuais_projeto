# Pilar 13 — Observabilidade

> **Parte 2 — Pilares Específicos do Projeto** · Fonte-mestre: [`pilares-app-ia-vendas-pecas.md`](../pilares-app-ia-vendas-pecas.md)

## Definição do pilar

LangSmith; logs estruturados correlacionados; métricas de negócio; alertas de custo.

## Camadas

| Camada | Ferramenta |
|---|---|
| Erros de app | Sentry (Django + Celery) |
| Logs | structlog / JSON — correlacionar `request_id` ↔ `trace_id` LangSmith; sem PII em texto aberto |
| IA | LangSmith — prompts, respostas, latência, tokens, custo |
| Filas | Flower |
| Infra | Prometheus + Grafana (ou Better Stack/Datadog) |
| Uptime | UptimeRobot / Healthchecks.io |

## Métricas de negócio

- Taxa de aprovação humana das extrações
- Taxa de “não encontrei resposta”
- Tempo médio de resposta
- Taxa de resolução sem humano
- Pedidos influenciados por IA (diagnóstico, foto, cross-sell, assinatura)
- Gasto em tokens/dia e por produto processado

## Alertas

Indisponibilidade, custo anômalo, chamado sem resposta dentro do SLA — **antes** do cliente reclamar.

## Dashboard interno (fase 7)

Painel no site para operação não-técnica: insights de chat/chamados/vendas-IA/custo + links para Sentry/Flower/Grafana.

## Fontes

- `constitution.md` — Artigo 4
- `plano-ecommerce-ia-pecas.md` — Observabilidade, Dashboard
- `plan.md` — Observabilidade
