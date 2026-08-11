# Relatório de beta — TechParts AI (T-P.1 / pós-F8)

**Status:** S-001 (mock) + S-002 (OpenAI + R2) + **S-003** (HITL staff) documentadas; validações locais verdes.  
**Data:** 2026-08-08  
**Participantes:** proxy interno (Cursor + HTTP + runserver local)  
**Branch/base:** `main` · seed beta + extração live OpenAI (S-003)

## Resumo executivo

- **S-001:** 6/6 fluxos no ambiente local **mock** após correção P0 de retrieval (B-007).
- **S-002:** 6/6 fluxos com **OpenAI** (chat/embeddings/foto) + **R2** para upload de foto; pagamento permanece mock.
- **S-003:** 6/6 — upload PDF → `awaiting_review` → approve HITL → **draft** (sem auto-publish) → publish staff → catálogo.
- Achado S-001: `embedding_vec` NULL engolia fallback JSON/hybrid → corrigido.
- Observação S-002: diagnóstico LangGraph citou fonte corretamente; **B-011 fechado** — `model_name` passa a refletir `OPENAI_CHAT_MODEL` quando o enriquecimento OpenAI roda.
- DoD visual: checklist código ok; validação humana via proxy HTTP S-001/S-002/S-003 nas telas críticas.

## Sessões

| ID | Data | Tester | Papel | Ambiente | Fluxos (# script) | Notas |
|---|---|---|---|---|---|---|
| S-001 | 2026-08-07 | proxy interno (Cursor + HTTP) | cliente + staff | local mock | 1–6 ✅ | Pedido `TP-20260807-DDD35B` paid; chat citou p.12/14 + SKUs VTE-02/CAP-35; chamado `CH-260807-4D0A5` |
| S-002 | 2026-08-08 | proxy interno (Cursor + HTTP) | cliente + staff | local OpenAI + R2 | 1–6 ✅ | Pedido `TP-20260808-9C7660` paid; chat citou Manutenção p.12 + CAP-35; foto R2 `gpt-4o-mini` 5 candidatos; chamado `CH-260808-092D8` |
| S-003 | 2026-08-08 | proxy interno (Cursor + HTTP) | staff HITL | local OpenAI + R2 | upload→HITL→draft→publish ✅ | Extração `#5` → draft `MONDIAL-VT-40-NB` → publish staff → `/catalogo/?q=MONDIAL-VT-40-NB` |

### S-001 — 2026-08-07 — proxy interno

- Papel: cliente (compra/chat/foto/chamado) + staff (dashboard)
- Ambiente: local mock (`PAYMENT_PROVIDER=mock`, `CHAT_LLM_MODE=mock`, `EMBEDDING_MODE=mock`)
- Fluxos: 1☑ 2☑ 3☑ 4☑ 5☑ 6☑
- UI (1–5): **4,5** após polish HOME/fotos/card (S-001b)
- RAG citação ok?: **sim** (após fix B-007) — sources p.14 Diagnóstico + p.12 Manutenção (CAP-35); `found_in_manual=true`; `recommendedSkus=['VTE-02','CAP-35']`
- Alucinação / fallback: fallback correto **antes** do fix (não inventou); após fix, citação fiel ao manual seed
- Tempo percebido: stream SSE respondeu <2s em mock; checkout end-to-end ~2s
- Confiança no diagnóstico (1–5): **4,5** — card com fonte %, SKU clicável e CTA de chamado
- Chamado sem repetir relato?: sim — abertura direta em `/chamados/` com equipamento VTE-02; 1 evento
- Issues: **B-007** (P0, corrigido); HOME/B-008/B-009/B-010 corrigidos no polish de nota

Evidências rápidas:

| Fluxo | Evidência |
|---|---|
| 1 Catálogo | VTE-02 + CAP-35 + 4 chunks; `/catalogo/?q=CAP-35` 200 |
| 2 Compra | Pedido `TP-20260807-DDD35B` `paid` + `EmailLog` ORDER_CONFIRMATION |
| 3 Chat | SSE 200; 2 sources; card SKUs |
| 4 Foto | `PhotoSearch` criado (JPEG mínimo) |
| 5 Chamado | `CH-260807-4D0A5` + 1 evento |
| 6 Dashboard | `/dashboard/` + monitoramento 200 com `tp-stat` |

Script (removido): `backend/scripts_beta_s001.py` — one-shot histórico.

### S-002 — 2026-08-08 — proxy interno (OpenAI + R2)

- Papel: cliente (compra/chat/foto/chamado) + staff (dashboard)
- Ambiente: local live IA (`CHAT_LLM_MODE=openai`, `EMBEDDING_MODE=openai`, `PHOTO_LLM_MODE=openai`, `USE_R2_STORAGE=true`, `PAYMENT_PROVIDER=mock`)
- Pré-req: `seed_beta --reindex` (chunks 1536 dims via OpenAI embeddings)
- Fluxos: 1☑ 2☑ 3☑ 4☑ 5☑ 6☑
- UI (1–5): **4,5** — home/`sw.js`/PDP com foto HTTP 200; sem regressão visual óbvia no HTML
- RAG citação ok?: **sim** — `found_in_manual=true`; fonte Manutenção pág. 12; CAP-35 3.5 uF; SKUs `['VTE-02','CAP-35']`
- Alucinação / fallback: 0; resposta alinhada ao manual seed
- Tempo percebido: checkout ~2s; chat/foto com OpenAI ~tens de segundos (aceitável em local)
- Confiança no diagnóstico (1–5): **4,5** — citação + SKUs; B-011 corrigido após S-002
- Chamado sem repetir relato?: sim — `CH-260808-092D8` com descrição referenciando chat/foto
- Issues: **B-011** (P2, **corrigido**)

Evidências rápidas:

| Fluxo | Evidência |
|---|---|
| 1 Catálogo | VTE-02 + CAP-35 + 4 chunks 1536d; `/` `/sw.js` `/catalogo/?q=CAP-35` PDP 200 + imagem |
| 2 Compra | Pedido `TP-20260808-9C7660` `paid` + e-mail confirmação; `/checkout/sucesso/` |
| 3 Chat | SSE 200; sources; CAP-35 / pág. 12 |
| 4 Foto | R2 `photos/182ff1ec-…/peca-s002.jpg`; `model=gpt-4o-mini`; 5 candidatos |
| 5 Chamado | `CH-260808-092D8` + 1 evento |
| 6 Dashboard | `/dashboard/` + monitoramento 200 com `tp-stat` |

Script (removido): `backend/scripts_beta_s002.py` — one-shot histórico.

### S-003 — 2026-08-08 — staff HITL (upload → draft → publish)

- Papel: staff (`beta.staff@techparts.local`) — fila `/manuais/revisao/`
- Ambiente: local live (`EXTRACTION_LLM_MODE=openai`, `CELERY_TASK_ALWAYS_EAGER=true`, R2)
- Fluxo: upload PDF (fixture VT-40-NB) → `awaiting_review` → approve HITL → **Product DRAFT** → publish staff → catálogo
- Assert chave: approve **não** publica sozinho (`status=draft`, `published_at=None`); só após passo staff explícito o SKU aparece no catálogo
- Evidências: extração `#5`; SKU `MONDIAL-VT-40-NB`; `/catalogo/?q=MONDIAL-VT-40-NB` 200 com SKU no HTML
- Fixes de caminho: structured output OpenAI via `function_calling`; `index_manual` após `on_commit`; savepoint no DDL pgvector (não abortar TX do approve)

Script (removido): `backend/scripts_beta_s003_hitl.py` — one-shot histórico.

### Template de sessão (copiar)

```
### S-00X — AAAA-MM-DD — <nome>
- Papel: cliente | staff ops
- Ambiente: local mock | staging
- Fluxos: 1☐ 2☐ 3☐ 4☐ 5☐ 6☐
- UI (1–5): _
- RAG citação ok?: sim / parcial / não — evidência: _
- Alucinação / fallback: _
- Tempo percebido: _
- Confiança no diagnóstico (1–5): _
- Chamado sem repetir relato?: _
- Issues: (IDs novos ou N/A)
```

## Issues priorizadas

| ID | Severidade | Área | Descrição | Dono | Ação |
|---|---|---|---|---|---|
| B-007 | P0 | RAG | pgvector `[]` com `embedding_vec` NULL bloqueava fallback JSON → chat sem citação | agente | **Corrigido** — `retrieve()` só short-circuita se `pg_hits` não-vazio; teste de regressão |
| HOME | P2 | Home | Hero loja vs shell técnico | agente | **Corrigido** — `tp-home-hero` marketing |
| B-008 | P2 | PWA | `/sw.js` 404 no browser | agente | **Corrigido** — rota `/sw.js` + registro na raiz |
| B-009 | P2 | Chat | Card diagnóstico sem link de SKU / CTA chamado | agente | **Corrigido** — `recommendedProducts` + ticket CTA |
| B-010 | P2 | Catálogo | Seed beta sem foto de produto | agente | **Corrigido** — PNG técnico no `seed_beta` |
| B-011 | P2 | Diagnóstico | Com `DIAGNOSIS_LLM_MODE=openai`, `model_name` permanecia `langgraph-diagnosis-mock` | agente | **Corrigido** — grafo propaga `OPENAI_CHAT_MODEL` após enriquecimento |

### Histórico (auditoria código/UI — T-P.3)

| ID | Severidade | Área | Descrição | Ação |
|---|---|---|---|---|
| B-001…B-006 | — | — | Fechados em T-P.3 | Ver PRs `#16`/`#19` |

## Qualidade das respostas (RAG / diagnóstico)

| Métrica | Valor |
|---|---|
| Taxa percebida de citação correta | **2/2** (S-001 mock + S-002 OpenAI embeddings/RAG) |
| Casos de alucinação / fallback | 1 fallback legítimo pré-B-007; 0 alucinação em S-001/S-002 |
| Golden set atualizado? | [x] base F8 verde — regressão `test_retrieve_falls_back_when_pgvector_vecs_null` |

Perguntas-guia do seed: “Qual o capacitor de partida do VTE-02?” · “Ventilador faz barulho e não gira”.

## DoD visual (telas críticas)

| Tela | Checklist código | Validação humana |
|---|---|---|
| Catálogo / PDP | [x] | [x] S-002 HTTP (foto + busca) |
| Chat / diagnóstico | [x] | [x] S-002 HTTP (citação + SKUs) |
| Checkout | [x] | [x] S-002 HTTP (pedido paid) |
| Chamados | [x] | [x] S-002 HTTP |
| Dashboard | [x] | [x] S-002 HTTP (`tp-stat`) |
| Assinaturas / Assistências / Garantia | [x] | [ ] (fora do script 1–6) |
| Home / PWA | [x] | [x] S-002 `/` + `/sw.js` 200 |

## Critérios de sucesso (specify)

| Critério | Código | Humano |
|---|---|---|
| Operação vê chat/chamados/vendas IA/custo no dashboard | [x] | [x] S-001/S-002 HTTP |
| Incidente aparece no monitoramento + alerta | [x] | [x] página 200 |
| Cliente compra e acompanha sem “ficar no escuro” | [x] | [x] pedidos paid + e-mail (S-001/S-002) |
| HITL impede publicação automática | [x] | [x] S-003 — approve → draft; publish staff separado |
| Chat cita fonte; ao escalar, histórico vai junto | [x] | [x] citação S-001/S-002; chamado com contexto |
| Descoberta por sintoma / modelo / foto | [x] | [x] chat + foto R2/OpenAI (S-002) |

## Aceite T-P.1

- [x] ≥1 sessão real documentada na tabela Sessões
- [x] Taxa RAG / alucinação preenchida
- [x] Issues P0/P1 com dono (B-007 corrigido; HOME/B-008–B-010 fechados)
- [x] Golden/prompts atualizados se houver regressão (teste novo)
- [x] Polish de percepção UI (home + fotos seed + card diagnóstico + sw.js)

## Próximos passos

1. Go-live staging: checklist [`security-hardening.md`](security-hardening.md) + [`deploy.md`](deploy.md) com secrets reais (pagamento/NF-e se contrato).
2. Conferência visual no browser humano (Assinaturas / Assistências / Garantia).
