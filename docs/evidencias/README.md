# Evidências de operação e DevOps (Senac 4.6 / 4.8)

| Artefato | O quê |
|---|---|
| [`ci-e-logs.md`](ci-e-logs.md) | Pipeline CI: lint + pytest + golden; duas etapas com logs |
| [`anomalia-e2e-chat.md`](anomalia-e2e-chat.md) | Anomalia real (E2E nightly), correlação `request_id` + `diagnosis_done`, tendência |
| Código | `scan_and_emit_alerts`: ≥ 3 extrações `FAILED` em 24h → `OpsAlert` |
| Low-code | Demo 2026-08-25: alerta *Alerta ops (n8n)* em `/dashboard/monitoramento/` |

Dois sinais correlacionáveis em toda execução do assistente:

1. Log estruturado `django_structlog` (`request_id` no request HTTP).
2. Log `diagnosis_done` / headers `X-Request-ID` e `X-LangSmith-Trace` (`langsmith_trace_id` no `ChatMessage`).
