# Anomalia: E2E de chat vs. contexto de produto

Investigação de **uma execução real** (Senac 4.6) e **detecção de anomalia + tendência** (4.8).

## O que quebrou (resolvido)

Workflow **E2E Playwright (nightly)** — run 2026-08-25 06:23 UTC  
https://github.com/henriqueferraz/manuais_projeto/actions/runs/32816737222  

```
FAILED e2e/test_chat.py::test_chat_stream_basic[chromium]
AssertionError: Locator expected to contain text 'manual'
```

O teste envia só: *“Qual a voltagem do capacitor de partida?”* e espera a palavra `manual` em `#tp-chat-body` (`e2e/test_chat.py`).

A UI respondeu com o card **“Qual é o produto?”** (pedir tipo/modelo). Isso é o grafo `ask_product` → `END`, alinhado a `diagnosis_system_v2`. O teste foi corrigido para validar esse comportamento.

## Correlação de dois sinais (mesma execução)

`request_id` = `783c4d81-3d59-4c6e-9d87-04b6f5dc248b`

| Sinal | Valor |
|---|---|
| `request_finished` / `streaming_started` (structlog) | `POST /assistente/chat/stream/` + mesmo `request_id` |
| `diagnosis_done` | `found=False`, `confidence=0.2`, `skus=[]`, `latency_ms=22`, `ticket_code=None`, mesmo `request_id` |

Conclusão da execução: o HTTP **200** e o stream **terminaram**; a falha é **assert de UI desatualizado**, não timeout nem 5xx. Latência 22 ms (mock). Confiança 0,2 < 0,70 → não tratar como resposta firme (sem SKU).

## Anomalia histórica

Erro **recorrente** no nightly: o mesmo spec falhou em runs sucessivos (pelo menos 22–25/08/2026, mesmo `AssertionError` / mesma pergunta sem modelo). Não foi flutuação de rede.

Causa raiz: commit de grounding (`eebcc7e`) passou a **exigir contexto de produto** antes do RAG; o E2E T-P.6 não foi ajustado.

## Tendência / risco (estimativa simples)

| Observação | Estimativa |
|---|---|
| Nightly chat vermelho em ≥ 4 dias seguidos | Taxa de falha do spec ≈ **100%** no período amostrado |
| CI `quality` (pytest) no mesmo intervalo | Permanece verde no run de referência 18/08 |
| Risco de **peça errada em produção** por este bug | **Baixo** — o agente recusa diagnosticar sem modelo |
| Risco de **falso alarme operacional** | **Alto** — nightly vermelho todo dia mascara outras regressões E2E |
| Risco na **gravação Senac** se o roteiro repetir a pergunta curta | **Médio** — o avaliador verá o pedido de produto (comportamento certo); cite este doc |

Probabilidade de o nightly chat voltar a verde **sem** mudar o teste ou a pergunta: ≈ 0 (comportamento determinístico).

Mitigação aplicada: o E2E espera `Qual é o produto?`, que é a saída esperada para uma pergunta sem tipo/modelo. A próxima execução nightly deve confirmar a correção no GitHub Actions.

## Extração ≥ 3 falhas / 24 h

Regra no app (`scan_and_emit_alerts`): `ExtractionLog` com `FAILED` ≥ 3 em 24 h gera `OpsAlert` “Falhas recorrentes de extração”. Complementa o n8n (`alert_recommended` / `?demo=1`).
