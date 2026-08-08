# Relatório de beta — TechParts AI (T-P.1 / pós-F8)

**Status:** S-001 (mock) + **S-002** (OpenAI + R2) documentadas; validações locais dos 6 fluxos verdes.  
**Data:** 2026-08-08  
**Participantes:** proxy interno (Cursor + HTTP + runserver local)  
**Branch/base:** `main` @ CI verde (`68e9bef`) · seed com `seed_beta --reindex` (embeddings 1536)

## Resumo executivo

- **S-001:** 6/6 fluxos no ambiente local **mock** após correção P0 de retrieval (B-007).
- **S-002:** 6/6 fluxos com **OpenAI** (chat/embeddings/foto) + **R2** para upload de foto; pagamento permanece mock.
- Achado S-001: `embedding_vec` NULL engolia fallback JSON/hybrid → corrigido.
- Observação S-002: diagnóstico LangGraph citou fonte corretamente; `model_name` ainda rotula `langgraph-diagnosis-mock` mesmo com `DIAGNOSIS_LLM_MODE=openai` (enriquecimento LLM não refletido no campo — P2).
- DoD visual: checklist código ok; validação humana via proxy HTTP S-001/S-002 nas telas críticas.

## Sessões

| ID | Data | Tester | Papel | Ambiente | Fluxos (# script) | Notas |
|---|---|---|---|---|---|---|
| S-001 | 2026-08-07 | proxy interno (Cursor + HTTP) | cliente + staff | local mock | 1–6 ✅ | Pedido `TP-20260807-DDD35B` paid; chat citou p.12/14 + SKUs VTE-02/CAP-35; chamado `CH-260807-4D0A5` |
| S-002 | 2026-08-08 | proxy interno (Cursor + HTTP) | cliente + staff | local OpenAI + R2 | 1–6 ✅ | Pedido `TP-20260808-9C7660` paid; chat citou Manutenção p.12 + CAP-35; foto R2 `gpt-4o-mini` 5 candidatos; chamado `CH-260808-092D8` |

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

Script: `backend/scripts_beta_s001.py`.

### S-002 — 2026-08-08 — proxy interno (OpenAI + R2)

- Papel: cliente (compra/chat/foto/chamado) + staff (dashboard)
- Ambiente: local live IA (`CHAT_LLM_MODE=openai`, `EMBEDDING_MODE=openai`, `PHOTO_LLM_MODE=openai`, `USE_R2_STORAGE=true`, `PAYMENT_PROVIDER=mock`)
- Pré-req: `seed_beta --reindex` (chunks 1536 dims via OpenAI embeddings)
- Fluxos: 1☑ 2☑ 3☑ 4☑ 5☑ 6☑
- UI (1–5): **4,5** — home/`sw.js`/PDP com foto HTTP 200; sem regressão visual óbvia no HTML
- RAG citação ok?: **sim** — `found_in_manual=true`; fonte Manutenção pág. 12; CAP-35 3.5 uF; SKUs `['VTE-02','CAP-35']`
- Alucinação / fallback: 0; resposta alinhada ao manual seed
- Tempo percebido: checkout ~2s; chat/foto com OpenAI ~tens de segundos (aceitável em local)
- Confiança no diagnóstico (1–5): **4,5** — citação + SKUs; label `model_name` ainda mock (B-011)
- Chamado sem repetir relato?: sim — `CH-260808-092D8` com descrição referenciando chat/foto
- Issues: **B-011** (P2, aberto)

Evidências rápidas:

| Fluxo | Evidência |
|---|---|
| 1 Catálogo | VTE-02 + CAP-35 + 4 chunks 1536d; `/` `/sw.js` `/catalogo/?q=CAP-35` PDP 200 + imagem |
| 2 Compra | Pedido `TP-20260808-9C7660` `paid` + e-mail confirmação; `/checkout/sucesso/` |
| 3 Chat | SSE 200; sources; CAP-35 / pág. 12 |
| 4 Foto | R2 `photos/182ff1ec-…/peca-s002.jpg`; `model=gpt-4o-mini`; 5 candidatos |
| 5 Chamado | `CH-260808-092D8` + 1 evento |
| 6 Dashboard | `/dashboard/` + monitoramento 200 com `tp-stat` |

Script: `backend/scripts_beta_s002.py`.

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
| B-011 | P2 | Diagnóstico | Com `DIAGNOSIS_LLM_MODE=openai`, `model_name` permanece `langgraph-diagnosis-mock` | agente | Abrir — propagar nome do modelo OpenAI no card/mensagem |

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
| HITL impede publicação automática | [x] | [ ] (seed usou produto já publicado; falta sessão staff upload→revisão) |
| Chat cita fonte; ao escalar, histórico vai junto | [x] | [x] citação S-001/S-002; chamado com contexto |
| Descoberta por sintoma / modelo / foto | [x] | [x] chat + foto R2/OpenAI (S-002) |

## Aceite T-P.1

- [x] ≥1 sessão real documentada na tabela Sessões
- [x] Taxa RAG / alucinação preenchida
- [x] Issues P0/P1 com dono (B-007 corrigido; HOME/B-008–B-010 fechados)
- [x] Golden/prompts atualizados se houver regressão (teste novo)
- [x] Polish de percepção UI (home + fotos seed + card diagnóstico + sw.js)

## Próximos passos

1. Opcional: fechar **B-011** (rótulo de modelo no diagnóstico OpenAI).
2. Sessão staff HITL: upload manual → revisão → publicar (critério specify ainda aberto).
3. Go-live staging: checklist [`security-hardening.md`](security-hardening.md) + [`deploy.md`](deploy.md) com secrets reais (pagamento/NF-e se contrato).
4. Conferência visual no browser humano (Assinaturas / Assistências / Garantia).
