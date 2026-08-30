# Entrega Senac — gap analysis e plano (M2.2)

Auditoria do TechParts AI contra o enunciado [`senac.md`](senac.md) (IA para Desenvolvedores T1, Módulo 2, Semana 12).

**Data da análise:** 20/08/2026  
**Veredito (atualizado 25/08/2026 após Fase D):** o sistema **ainda não cumpre 100%**. Fases A–D fechadas (grafo, n8n, README 5.2, evidências, Kanban + `develop`). Resta E (vídeo e AVA).

**Peso:** Avaliação M2.2 — 60% da nota do módulo.  
**Liberação:** 21/08/26 às 22h.  
**Entrega:** 31/08/26 até às 15h.  
**Submissão no AVA:** Projeto Avaliativo – M2.2 (links do repositório, do quadro e do vídeo).

Este documento não substitui o README da entrega: é o **plano de fechamento**. O enunciado canônico permanece em [`senac.md`](senac.md).

---

## 1. Contexto do enunciado (o que será avaliado)

Sistemas de IA passaram a executar tarefas, consultar dados, usar tools, manter memória e coordenar fluxos. O projeto deve ser **funcional, demonstrável e tecnicamente explicável**: entrada → fluxo → decisões do agente → tools → contexto → controles de autonomia → qualidade → sinais para investigar.

O domínio pode ser qualquer um (incluindo continuidade do mini-projeto). O objetivo **não** é acumular funcionalidades de e-commerce; é evidenciar os conteúdos do Módulo 2.

Entrega individual: repositório GitHub, GitHub Project Kanban, README completo, evidências em `/docs`, vídeo YouTube não listado.

---

## 2. Veredito resumido

| Área | Cumpre 100%? | Observação |
|---|---|---|
| Aplicação funcional + domínio | Sim (docs) | Dois cenários no README; demo no vídeo |
| LangGraph (seq + condicional + **paralelo**) | Sim (Fase A) | Fan-out `emit_trace` ∥ `emit_done` |
| Tool / MCP / API / serviço / webhook | Sim | Tools Pydantic no grafo + webhooks |
| Memória / RAG | Sim | README + pilar 10 |
| Segurança + cenário adversarial | Sim (docs) | Testes + cenário 2 no README; demo no vídeo ainda Fase E |
| Observabilidade + resiliência | Sim (docs) | Investigação `request_id` + `diagnosis_done` em evidencias |
| IA para QA | Sim (docs) | [`docs/qa/`](qa/README.md) — review `eebcc7e` + teste adversarial |
| DevOps inteligente | Sim (docs) | CI + anomalia E2E + tendência; build Docker explícito e execução verde confirmados |
| Low-code / no-code visual | Sim (Fase B) | n8n importável + `OpsAlert` no painel |
| README Senac (item 5.2) | Sim (Fase C) | Seções no [`README.md`](../README.md); vídeo TBD |
| `/docs/prompts`, `/docs/qa`, `/docs/evidencias` | Sim (Fase C) | Pastas criadas |
| Fluxo `develop` → `feature/*` → `main` | Sim (Fase D) | PRs [#54](https://github.com/henriqueferraz/manuais_projeto/pull/54), [#55](https://github.com/henriqueferraz/manuais_projeto/pull/55) e [#58](https://github.com/henriqueferraz/manuais_projeto/pull/58) |
| GitHub Project Kanban | Sim (Fase D) | [Project nº 2](https://github.com/users/henriqueferraz/projects/2); `#48` em Andamento |
| Professor colaborador | Sim | Convite concluído; confirmação externa ao repositório |
| Vídeo 5.5 | Não | Sem gravação nem link |

O produto é **maior** que o pedido. O risco de nota é **não demonstrar** o que o avaliador vai procurar, não falta de loja.

---

## 3. O que já atende (reaproveitar)

| Requisito Senac | Situação no código / docs |
|---|---|
| App web executável, dados de exemplo, `.env.example` | [`README.md`](../README.md) + `seed_beta` |
| Lógica real de IA (não só respostas fixas) | Extração, RAG, diagnóstico |
| Saída estruturada | Estado do grafo + JSON/Pydantic da extração |
| LangGraph com state tipado, nodes, edges, ramificação, **paralelização**, parada | `diagnosis.py` (condicional + fan-out) + `extraction.py` (HITL / `interrupt` + `recursion_limit`) |
| Tool/integração (MCP **ou** API/serviço/webhook) | `apps.ai.graphs.tools`, webhook de pagamento, RAG, Melhor Envio, WhatsApp, `/ops/hooks/lowcode/` |
| Ação irreversível com humano | Fila `/manuais/revisao/` |
| Memória / RAG | pgvector, state, checkpoint SQLite persistente na extração; [`pilares/10-rag-duvidas-tecnicas.md`](pilares/10-rag-duvidas-tecnicas.md) |
| Segredos fora do repo | `.env.example`; modelo via `*_LLM_MODE` / `OPENAI_*` |
| Observabilidade (pelo menos 2 sinais) | structlog (`request_id`) + `diagnosis_done`/auditoria; LangSmith apenas quando configurado |
| Timeout / retry / fallback | NF-e (`max_retries`), frete, chat `low-confidence-fallback` |
| Pipeline lint + testes | `.github/workflows/ci.yml` (ruff, black, bandit, pytest, golden) |
| Integração / E2E | pytest de integração + Playwright (`e2e/test_chat.py`, checkout, ticket) |
| Prompts versionados | `backend/apps/*/prompts/` (v1–v3) |
| Repositório GitHub + histórico incremental | `henriqueferraz/manuais_projeto`, branches `fase/*` |
| Alertas / ChatOps (extensão opcional) | `backend/apps/dashboard/services/monitoring.py` (e-mail + Slack webhook) |

Isso já sustenta bem os critérios **6, 8, 9** e parte de **7, 10, 11**.

### Classificação sugerida da solução (para o README)

**Sistema híbrido:** regras determinísticas (roteamento por regex/contexto de produto, HITL, sanitização, confiança mínima) + decisões do modelo (extração estruturada, geração RAG, sugestão de causa/peça **somente** com evidência).

### Dois cenários (rascunho para documentar)

1. **Principal:** relato de falha no chat → LangGraph (`understand` → busca → `suggest`) → RAG no manual → resposta estruturada com fonte e SKU sugerido.  
2. **Risco / falha / adversarial (escolher e gravar um):** prompt injection no chat ou PDF; **ou** extração recusada na revisão humana; **ou** baixa confiança → fallback / chamado, sem inventar peça.

---

## 4. Lacunas que impedem 100%

Fases A–C **fecharam** paralelização LangGraph, n8n, adversarial no README, `docs/prompts|qa|evidencias` e README 5.2 (falta só o **URL do vídeo**).

### 4.2 Ainda aberto ou parcial

**Link do vídeo no README (item 5.5 / critério 1 e 5)**  
Seções 5.2 existem; o campo do YouTube não listado é Fase E.

**Fluxo Git Senac (item 5.4 / critério 4)**  
A branch `develop` e o fluxo documentado existem no estado atual. A sequência de PRs é evidência externa ao clone e deve ser conferida no GitHub.

**GitHub Project Kanban (item 5.3 / critérios 2–3)**  
O Project e os cards estão informados como existentes, mas sua criação, atualização e movimentação são evidências externas ao repositório. Colunas pedidas: Backlog, A Fazer, Em Andamento, Bloqueado, Em Revisão, Concluído.

**Vídeo (item 5.5 / critério 1) — 1,00 ponto**  
Não há gravação, YouTube não listado nem link no README.

**Processo AVA**  
Convite do professor concluído; ainda falta submeter os links no AVA e **não** alterar o repositório após o prazo.

---

## 5. Mapa nota × esforço (critérios oficiais)

Nota 0–10. Projetos com plágio, credenciais expostas, artefatos inacessíveis ou código que o estudante não explica podem zerar.

| Nº | Critério | Peso | Status | Ação |
|---|---|---|---|---|
| 1 | Vídeo YouTube não listado, ≤ 12 min, pontos do 5.5 | 1,00 | Ausente | Fase E |
| 2 | Cards no quadro GitHub | 0,50 | Feito ([Project nº 2](https://github.com/users/henriqueferraz/projects/2)) | URL no AVA |
| 3 | Quadro atualizado durante o desenvolvimento | 0,50 | Feito; `#48` em Andamento | Fase E fecha `#48` |
| 4 | Branches `develop` / feature / `main`, commits semânticos | 0,75 | Feito (PRs #54 → develop, #55 → main) | — |
| 5 | README + docs para compreender, executar e avaliar | 0,75 | Feito (Fase C); falta URL do vídeo | Fase E |
| 6 | App funcional + 2 cenários + saída estruturada | 0,75 | Feito (README + `seed_beta`) | Demo no vídeo |
| 7 | LangGraph (state, seq, condicional, **paralelo**, parada) | 0,75 | Feito (Fase A) | — |
| 8 | Tool integrada com validação e falhas | 0,75 | Feito (tools Pydantic) | Demo no vídeo |
| 9 | Memória / RAG adequada ao domínio | 0,75 | Feito (README + pilar 10) | Demo no vídeo |
| 10 | Segurança, autonomia, cenário adversarial | 0,75 | Documentado + testes; demo no vídeo | Fase E |
| 11 | Dois sinais correlacionados + timeout/retry/fallback | 0,75 | Parcial: sinais locais e resiliência feitos; trace LangSmith não é garantido | Demo no vídeo |
| 12 | IA em code review + testes (integração/aceitação/E2E) + risco | 0,50 | Feito ([`docs/qa/`](qa/README.md)) | — |
| 13 | Pipeline + IA em logs (2 etapas) + anomalia + tendência | 0,50 | Feito ([`evidencias/`](evidencias/README.md)); CI inclui build Docker explícito | — |
| 14 | Low-code/no-code integrado (trigger + saída) | 0,50 | Feito (n8n + POST report) | Demo no vídeo |
| 15 | Refinamento documentado + evidências | 0,50 | Feito ([`prompts/ciclo-refinamento.md`](prompts/ciclo-refinamento.md)) | — |
| | **Total** | **10,00** | | |

---

## 6. Planejamento para fechar 100%

Ordem: código primeiro, evidências no meio, vídeo por último. Estimativa: **4–6 dias** de trabalho focado até 31/08.

Sugestão de branches (enunciado): `feature/langgraph-agente`, `feature/tool-integracao`, `feature/memoria-rag`, `feature/governanca`, `feature/observabilidade`, `feature/qa-inteligente`, `feature/devops-anomalias`, `feature/low-code`, `docs/readme-video`.

### Fase A — Código mínimo Senac (1–2 dias) — **feita (2026-08-20)**

1. [x] **Paralelizar** no grafo: após `suggest`, fan-out `emit_trace` ∥ `emit_done` (sem ORM). Tools RAG + pedidos em `search_context` (mesma thread — SQLite/CI). Condicional `ask_*` → `END`.
2. [x] **Limite de execução:** `recursion_limit` em `run_diagnosis` (8) e extração (12); parada HITL documentada no módulo do grafo.
3. [x] **Tools explícitas:** `retrieve_manual_chunks` e `search_user_orders` em `apps.ai.graphs.tools` (Pydantic + erro).
4. [x] **Cenário adversarial:** sanitização de leak de chave/prompt + testes de chat/diagnóstico (sem vazar secret, sem cadastro).
5. [x] **Gancho low-code:** `GET|POST /ops/hooks/lowcode/` (`LOWCODE_WEBHOOK_SECRET` / `X-Lowcode-Secret`).

### Fase B — Low-code (meio dia) — **feita (2026-08-20); demo ao vivo 2026-08-25**

6. [x] Fluxo visual n8n: gatilho manual + cron 15 min → GET snapshot → IF `alert_recommended` → POST relatório. JSON em [`lowcode/n8n-techparts-ops.json`](lowcode/n8n-techparts-ops.json). Instância: [TechParts — snapshot ops](https://n8n.hferraz.com.br/workflow/xOru4XDHJhmWLSB4). Saída: `OpsAlert` em `/dashboard/monitoramento/` (ex.: *Alerta ops (n8n)* com filas reais). Slack/e-mail = ChatOps opcional (`panel+email`).
7. [x] Passos de reprodução no README e em [`lowcode/README.md`](lowcode/README.md) (túnel EasyPanel + localhost). **Falta só gravar o canvas no vídeo** (Fase E / item 5.5).

### Fase C — Evidências em `/docs` (1–2 dias) — **feita (2026-08-25)**

- [x] [`prompts/`](prompts/README.md) — índice das instruções vigentes + [`ciclo-refinamento.md`](prompts/ciclo-refinamento.md)
- [x] [`qa/`](qa/README.md) — review do commit real `eebcc7e` + teste adversarial por risco
- [x] [`evidencias/`](evidencias/README.md) — CI (Ruff + Pytest), correlação `request_id`/`diagnosis_done`, anomalia E2E nightly, tendência
- [x] README item 5.2 (cenários, diagrama, low-code). **URL do vídeo** = Fase E.

### Fase D — GitHub — **implementada e conferida em 2026-08-25**

Guia: [`github-kanban.md`](github-kanban.md).

11. [x] GitHub Project com colunas do enunciado: [TechParts Senac M2.2](https://github.com/users/henriqueferraz/projects/2).
12. [x] Um card por tema (issues `#43`–`#53` no Project).
13. [x] Cada card: objetivo, resultado, evidência; `#48` em **Em Andamento** (vídeo/AVA = Fase E).
14. [x] Branch [`develop`](https://github.com/henriqueferraz/manuais_projeto/tree/develop); PRs `feature/*` → `develop` → `main` ([#54](https://github.com/henriqueferraz/manuais_projeto/pull/54), [#55](https://github.com/henriqueferraz/manuais_projeto/pull/55), [#58](https://github.com/henriqueferraz/manuais_projeto/pull/58)).
15. [x] Commits semânticos no fluxo `develop` / `main`.
16. [x] Professor colaborador (convite concluído; confirmação externa ao repo).
17. [x] `.env` não versionado (`.gitignore`); só `.env.example`.

### Fase E — Vídeo e AVA (último dia útil)

18. Gravar **11:00–11:30** (teto **12:00**), YouTube **não listado**, link no README. Roteiro falado: [`video-roteiro-venda.txt`](video-roteiro-venda.txt).

Roteiro do enunciado (expandido no doc para caber 10–12 min):

| Tempo | Conteúdo |
|---|---|
| 0:00–1:10 | Problema, objetivo, classificação (híbrido) |
| 1:10–2:25 | Arquitetura e integrações |
| 2:25–4:50 | Dois cenários (principal + risco/falha/injection) |
| 4:50–6:00 | Segurança, bloqueio ou HITL |
| 6:00–7:10 | Uma evidência de QA |
| 7:10–9:20 | Pipeline, análise de logs, anomalia, tendência/risco |
| 9:20–10:40 | Low-code/no-code |
| 10:40–11:30 | Limitações e melhorias futuras |

19. Submeter no AVA os três links **antes** das 15h de 31/08. **Não** alterar o repositório depois.

---

## 7. Checklist final (espelho do enunciado §7)

Marcar à medida que fechar. Estado na data da análise: quase tudo **aberto** no lado Senac, apesar do produto estar avançado.

### Repositório e organização

- [x] Repositório no GitHub; nenhum segredo/`.env` versionado; professor colaborador convidado
- [x] Quadro Kanban criado e atualizado ([Project nº 2](https://github.com/users/henriqueferraz/projects/2); `#48` ainda em andamento)
- [x] Fluxo `develop` → `feature/*` → `develop` → `main`, commits semânticos
- [x] Versão funcional na `main` (congelar só após o vídeo/AVA)

### Domínio, arquitetura e agente

- [x] Problema/domínio definidos; dois cenários (incluindo risco/falha/anomalia)
- [x] LangGraph: state, nodes, sequencial, **condicional**, **paralelização**, condição de parada
- [x] Tool funcional (MCP, API, serviço, backend ou webhook)
- [x] Memória / RAG documentada e demonstrada

### Segurança, observabilidade e resiliência

- [x] Validação de payloads/schemas, limites de autonomia, HITL, cenário adversarial
- [x] Dois sinais correlacionados (logs estruturados + `request_id`/auditoria); erros e latência
- [x] Timeout, retry limitado ou fallback nas integrações

### QA, DevOps e low-code

- [x] Code review com IA + testes relevantes (integração, aceitação ou E2E) + priorização por risco
- [x] Pipeline lint/testes/build + IA em logs de 2 etapas + anomalia + tendência/risco (lint/testes/golden, build Docker e execução verde confirmados)
- [x] Automação low-code/no-code com trigger e saída observável

### README e evidências

- [x] README permite compreender, configurar, executar e avaliar (prompts + modelo via env)
- [x] Ciclo de refinamento documentado (problema → alteração → resultado)
- [x] Evidências em `/docs` (testes, observabilidade, QA, DevOps, low-code)
- [ ] Link do vídeo no README

### Vídeo e submissão

- [ ] Vídeo ≤ 12 min, não listado, pontos do 5.5
- [ ] Demo dos dois cenários + pipeline + logs + anomalia + tendência + low-code
- [ ] Evidências no repo e no quadro
- [ ] Links no AVA; repositório congelado após a entrega

---

## 8. Referências rápidas no código

| Tema | Onde |
|---|---|
| Grafo diagnóstico | `backend/apps/ai/graphs/diagnosis.py`, `backend/apps/ai/graphs/state.py` |
| Grafo extração + HITL | `backend/apps/manuals/graphs/extraction.py` |
| RAG / chat | `backend/apps/ai/services/retrieval.py`, `backend/apps/ai/services/chat.py` |
| Sanitização injection (PDF) | `backend/apps/manuals/services/sanitize.py`, `test_sanitize_strips_injection` |
| Prompts | `backend/apps/ai/prompts/`, `backend/apps/manuals/prompts/` |
| Observabilidade | `backend/apps/core/logging.py`, structlog, `langsmith_trace_id` |
| Monitoramento / alertas | `backend/apps/dashboard/services/monitoring.py` |
| CI | `.github/workflows/ci.yml` |
| E2E | `e2e/test_chat.py`, `e2e/test_checkout.py`, `e2e/test_ticket.py` |
| Enunciado | [`senac.md`](senac.md) |

---

## 9. Princípio de execução

Não reconstruir o e-commerce. Fechar **somente** o que o avaliador Senac exige: paralelo no grafo, low-code visual, cenário adversarial, pastas de evidência, README no formato 5.2, Kanban + `develop`, vídeo e AVA.
