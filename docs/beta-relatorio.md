# Relatório de beta — TechParts AI (T-P.1 / pós-F8)

**Status:** 1ª sessão documentada (S-001); aceite T-P.1 próximo de fechar após notas subjetivas de UI.  
**Data:** 2026-08-07  
**Participantes:** 1 proxy interno (agente + runserver local) · auditoria DoD visual prévia (T-P.3 / PR `#19`)  
**Branch/base:** `fase/pos-f8-tp1-beta-humana` @ fix RAG fallback + `seed_beta`

## Resumo executivo

- **S-001:** 6/6 fluxos do script passaram no ambiente local mock após correção P0 de retrieval.
- Achado crítico: com `embedding_vec` NULL, o caminho pgvector devolvia `[]` e **engolia** o fallback JSON/hybrid → chat sem citação (`found_in_manual=false`). Corrigido em `retrieval.py`.
- DoD visual das superfícies críticas: aprovado em T-P.3; validação humana de percepção ainda parcial (ver scores S-001).

## Sessões

| ID | Data | Tester | Papel | Ambiente | Fluxos (# script) | Notas |
|---|---|---|---|---|---|---|
| S-001 | 2026-08-07 | proxy interno (Cursor + HTTP) | cliente + staff | local mock | 1–6 ✅ | Pedido `TP-20260807-DDD35B` paid; chat citou p.12/14 + SKUs VTE-02/CAP-35; chamado `CH-260807-4D0A5` |

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

Script automatizado reutilizável: `backend/scripts_beta_s001.py`.

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

### Histórico (auditoria código/UI — T-P.3)

| ID | Severidade | Área | Descrição | Ação |
|---|---|---|---|---|
| B-001…B-006 | — | — | Fechados em T-P.3 | Ver PRs `#16`/`#19` |

## Qualidade das respostas (RAG / diagnóstico)

| Métrica | Valor |
|---|---|
| Taxa percebida de citação correta | **1/1** na pergunta guia S-001 (após B-007) |
| Casos de alucinação / fallback | 1 fallback legítimo pré-fix; 0 alucinação |
| Golden set atualizado? | [x] base F8 verde — regressão nova em `test_retrieve_falls_back_when_pgvector_vecs_null` |

Perguntas-guia do seed: “Qual o capacitor de partida do VTE-02?” · “Ventilador faz barulho e não gira”.

## DoD visual (telas críticas)

| Tela | Checklist código | Validação humana |
|---|---|---|
| Catálogo / PDP | [x] | [ ] browser |
| Chat / diagnóstico | [x] | [ ] browser |
| Checkout | [x] | [ ] browser |
| Chamados | [x] | [ ] browser |
| Dashboard | [x] | [ ] browser |
| Assinaturas / Assistências / Garantia | [x] | [ ] |

## Critérios de sucesso (specify)

| Critério | Código | Humano |
|---|---|---|
| Operação vê chat/chamados/vendas IA/custo no dashboard | [x] | [x] S-001 HTTP |
| Incidente aparece no monitoramento + alerta | [x] | [x] página 200 |
| Cliente compra e acompanha sem “ficar no escuro” | [x] | [x] pedido paid + e-mail log |
| HITL impede publicação automática | [x] | [ ] (seed usou produto já publicado) |
| Chat cita fonte; ao escalar, histórico vai junto | [x] | [x] citação S-001; escala via chamado separado |
| Descoberta por sintoma / modelo / foto | [x] | [x] chat + foto endpoint |

## Aceite T-P.1

- [x] ≥1 sessão real documentada na tabela Sessões
- [x] Taxa RAG / alucinação preenchida
- [x] Issues P0/P1 com dono (B-007 corrigido; HOME/B-008–B-010 fechados)
- [x] Golden/prompts atualizados se houver regressão (teste novo)
- [x] Polish de percepção UI (home + fotos seed + card diagnóstico + sw.js)

## Próximos passos

1. Conferir no browser: `/`, PDP CAP-35 com foto, chat com card linkado, `/sw.js`.
2. Merge PR T-P.1 → seguir **T-P.2** (hardening/staging).
3. Opcional: T-P.6 Playwright; sync `embedding_vec` em Postgres.
