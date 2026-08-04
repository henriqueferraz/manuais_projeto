# Plano de Tarefas — E-commerce de Peças com IA

Plano de tarefas e subtarefas para desenvolver o sistema completo, alinhado ao roadmap técnico, à constitution, ao specify e aos **24 pilares** (incluindo qualidade visual e experiência do usuário).

**Stack:** Python + Django + htmx + Bootstrap + PostgreSQL/pgvector + Celery + LangChain/LangGraph + Cloudflare R2

**Fontes:** [`plano-ecommerce-ia-pecas.md`](plano-ecommerce-ia-pecas.md) · [`pilares-app-ia-vendas-pecas.md`](pilares-app-ia-vendas-pecas.md) · [`pilares/`](pilares/) · [`constitution.md`](constitution.md) · [`specify.md`](specify.md) · [`DESIGN.md`](DESIGN.md) · [`plan.md`](plan.md)

---

## Regras base (obrigatórias)

Estas regras valem para **todas as fases** e para qualquer agente/dev que execute o plano.

### R1 — Versões estáveis mais recentes

Todo sistema, runtime, biblioteca, ferramenta de CLI ou material instalado/adicionado ao projeto deve usar a **maior versão estável disponível no momento da instalação daquela fase** (não betas, RCs ou nightlies, salvo exceção explícita e registrada em ADR).

- Inclui: Python, Django, Bootstrap, PostgreSQL/pgvector, Redis, Celery, LangChain/LangGraph, Node (se necessário para tooling), Docker images base, actions do CI, etc.
- Ao iniciar uma fase que introduz dependência nova: consultar a versão estável atual e fixar no lock/`requirements`/`package` com essa versão.
- Não “congelar para sempre” no início do projeto se uma fase posterior for a primeira a instalar o pacote — usa-se a estável **daquela** data.
- Upgrades major no meio de uma fase só com motivo (CVE, bloqueio) e registro curto.

### R2 — Git por fase: PR no início, merge na `main` no fim

Cada fase (F0, F1, F2, F3, **F4a, F4b, F4c, F4d**, F5, F6, F7, F8) é uma unidade de entrega na `main`.

**Decisões confirmadas (2026-08-04):**

| # | Decisão |
|---|---|
| D1 | F4a–F4d = **4 PRs/merges distintos** na `main` |
| D2 | Merge = **squash** na `main`, CI verde (quando houver), branch remota apagada |
| D3 | No início da fase: branch + push + abrir PR (draft ok); **sem** commit vazio; primeiro commit útil abre o histórico |
| D4 | R1 = maior estável **na data em que a dependência entra** naquela fase |
| D5 | **F1 é PR só de docs** (escopo/schema) — válido e obrigatório como primeira entrega |
| D6 | Sequência fixa de merge: **F1 → F0 → F2 → …** (F0 e F2 **não** compartilham a mesma PR) |
| D7 | Projeto solo: **merge automático ao fim da fase**, sem review humano obrigatório; se branch protection bloquear, ajustar proteção ou usar `--admin` conforme política do repo |
| D8 | **Primeira ação da F1:** inicializar git + remote GitHub + `main`, se ainda não existirem |

**Bootstrap do repositório (antes ou como T-1.0 da F1):**

1. `git init`, branch `main`, `.gitignore` adequado
2. Commit inicial na `main` (docs existentes, se ainda não versionados)
3. Criar repo no GitHub (`gh repo create`) e `git push -u origin main`
4. A partir daí, aplicar o ciclo abaixo em **toda** fase

**Antes de iniciar a fase (obrigatório, automático):**

1. Garantir working tree limpa a partir de `main` atualizada (`git pull` / sync com remote).
2. Criar branch `fase/<id>-<slug>` (ex.: `fase/4a-catalogo-estoque-carrinho`).
3. Commit inicial da fase se já houver artefatos pendentes alinhados ao escopo (ex.: docs da fase); senão, commit vazio **não** — o primeiro commit útil abre o histórico.
4. `git push -u` da branch.
5. Abrir PR para `main` (`gh pr create`) com título/corpo citando a fase, pilares e checklist de aceite — PR pode começar como draft e sair de draft quando o aceite da fase estiver completo.

**Durante a fase:**

- Commits frequentes na branch da fase (Conventional Commits).
- CI da PR deve passar antes do merge (a partir da F2, quando o CI existir; na F1/F0 docs-only, merge após aceite das tarefas).

**Ao finalizar a fase (obrigatório, automático):**

1. Conferir aceite de todas as tarefas `T-X.Y` da fase + DoD visual/UX quando houver UI.
2. Garantir CI verde na PR (quando aplicável).
3. Tirar PR de draft se necessário; merge squash na `main` (`gh pr merge --squash --delete-branch`) **sem aguardar review humano** (D7).
4. Só então iniciar a próxima fase (nova branch a partir da `main` já atualizada).

**Exceções:**

- F8: cada item grande (WhatsApp, assinatura, etc.) pode ter PR próprio sob o guarda-chuva da fase, com aceite explícito do item antes do merge.

### R3 — Testes automatizados e unitários (obrigatórios)

Testes não são “fase opcional”: são regra de entrega a partir da **F2** (quando o código e o CI nascem). Alinha P06, constitution Art. 5 e o gate de merge da R2.

**O que é obrigatório**

| Tipo | Ferramenta | Quando |
|---|---|---|
| Unitários | pytest (+ Django TestCase / pytest-django) | Todo código de domínio novo (models, services, parsers, validators) |
| Integração | pytest + DB/Redis de teste | Fluxos que cruzam apps (estoque+carrinho, upload+task, etc.) |
| Tasks Celery | pytest com eager/mocks | Extração, embeddings, NF-e, e-mails |
| IA | mocks da API Anthropic + golden set | Extração/RAG — **nunca** chamar API paga no CI unitário |
| E2E | Playwright (a partir de F4b/F5) | Checkout, chamado, chat — caminhos críticos |
| Estáticos | ruff, black --check, bandit, check migrations | Todo PR com código |

**Regras de execução**

1. **Nenhuma feature de código mergeia sem testes que cubram o caminho feliz e ao menos um caso de erro/edge** relevante ao aceite da tarefa.
2. Testes da mudança rodam **localmente antes do push** e de novo no **CI da PR**; merge só com CI verde (R2/D2).
3. **Cobertura mínima** nos fluxos críticos (checkout, pagamento, extração de IA): meta **≥ 80%** (pytest-cov no CI), verificada a partir da F4b/F3 conforme o código existir.
4. **Novo comportamento = novo teste** na mesma PR; regressão sem teste que a pegaria é débito proibido no merge.
5. Chamadas reais a Claude/Anthropic **fora** do CI unitário; no CI usar fixtures/mocks. Golden set (F3 local → F6 no CI) valida prompts/extração com gabarito conhecido.
6. F1 e F0 (docs / fundação visual sem app): testes automatizados de app **não se aplicam**; a partir da F2, pipeline pytest existe mesmo que a suíte inicial seja mínima (“smoke”).
7. Stack de teste também segue **R1** (maior pytest/pytest-django/Playwright estável na instalação).

**Gate de merge (resumo)**

```
lint + typecheck(opcional) + pytest(+cov) + migrations check [+ e2e se a fase já tiver]
        → CI verde → squash merge na main
```

---
## Como usar este documento

| Campo | Significado |
|---|---|
| `T-X.Y` | Tarefa da fase X |
| Subtarefas | Checklist acionável |
| Pilares | P01–P24 materializados pela tarefa |
| Aceite | Critério objetivo de “pronto” |

Toda tela/fluxo de UI deve passar pelo [Definition of Done visual/UX](#definition-of-done-visualux) antes de ser considerada concluída.

**Checklist Git (por fase):** ver [R2](#r2--git-por-fase-pr-no-início-merge-na-main-no-fim).  
**Checklist testes:** ver [R3](#r3--testes-automatizados-e-unitários-obrigatórios).

```mermaid
flowchart LR
  F1[F1 Escopo] --> F0[F0 DesignSystem]
  F0 --> F2[F2 Base CI Docker]
  F2 --> F3[F3 Ingestao Manuais]
  F3 --> F4a[F4a Catalogo]
  F4a --> F4b[F4b Checkout]
  F4b --> F4c[F4c Chamados]
  F4c --> F4d[F4d Cupons Trocas]
  F4d --> F5[F5 Chat RAG]
  F5 --> F6[F6 LangGraph]
  F6 --> F7[F7 Beta Dashboard]
  F7 --> F8[F8 Escala]
```

Ordem de merge na `main` (R2): **F1 → F0 → F2 → F3 → F4a → F4b → F4c → F4d → F5 → F6 → F7 → F8**.

---

## Fase 0 — Fundação visual e UX

> Objetivo: materializar o design system **Industrial Precision** antes do catálogo, para que toda UI nasça no padrão certo.  
> **Git:** após merge da F1; antes da F2 (ver R2).  
> Pilares centrais: **P16, P17, P18, P19, P20, P21, P22, P24**

### T-0.1 — Tokens e tema Bootstrap customizado

**Pilares:** P16, P17, P24

- [ ] Definir variáveis CSS/SCSS a partir de [`DESIGN.md`](DESIGN.md) (Industrial Navy, AI Cyan, Tech Gray, surfaces, success/danger)
- [ ] Configurar tipografia: Inter (UI) + JetBrains Mono (specs/SKU)
- [ ] Mapear tokens para overrides do Bootstrap 5 (cores, radii 4px, espaçamento base 4px)
- [ ] Documentar uso: cyan **somente** em features de IA
- [ ] Página/story de tokens (preview interno) para validação visual

**Aceite:** tema Bootstrap não parece “tema padrão”; tokens documentados e aplicáveis em templates.

### T-0.2 — Componentes reutilizáveis

**Pilares:** P16, P17, P19, P20

- [ ] Botões: Primary (navy), AI Action (cyan), Ghost/Outline
- [ ] Product Card (foto, brand label-caps, título, linha técnica mono, badge)
- [ ] Status Badges (estoque, rascunho, SLA)
- [ ] Inputs e tabelas densas (foco navy 2px)
- [ ] Shell do AI Chat (header cyan, bolhas, tag de fonte técnica)
- [ ] Skeletons, empty states e error states com ação de recuperação
- [ ] Ícones Material Symbols Outlined de forma consistente

**Aceite:** componentes renderizam em desktop e mobile; checklist DoD visual passa.

### T-0.3 — Layout, responsividade e acessibilidade base

**Pilares:** P21, P22

- [ ] Grid 12/8/4 (desktop/tablet/mobile), container max 1280px na loja
- [ ] Margens/gutters conforme design system
- [ ] Contraste WCAG AA em textos, botões e badges
- [ ] Navegação por teclado e foco visível
- [ ] Padrão de `alt` em imagens/ícones

**Aceite:** layout base mobile-first; auditoria rápida de contraste e teclado OK.

### T-0.4 — Guia de marca e checklist de revisão visual

**Pilares:** P18, P24

- [ ] Registrar tom técnico/industrial (não consumer “fofo”)
- [ ] Regras de fotografia de produto (fundo neutro, ângulo, iluminação)
- [ ] Checklist de revisão visual por PR/tela (ligar ao DoD abaixo)
- [ ] Referenciar protótipos em `docs/code*.html` e `docs/src/` como meta visual

**Aceite:** qualquer nova tela pode ser revisada contra um checklist único.

---

## Fase 1 — Descoberta e escopo do MVP

> Objetivo: travar o que entra no MVP e o schema mínimo para vender.  
> Entrega: **PR só de documentação** (D5).  
> Pilares: **P01**  
> **Git:** primeira fase — inclui bootstrap do repositório (D8).

### T-1.0 — Bootstrap Git + remote GitHub

**Pilares:** P14 (base), R2

- [ ] Verificar se já existe `.git` e remote; se **não**, executar bootstrap (D8)
- [ ] `git init`, branch `main`, `.gitignore` (Python/Django/Node/env/secrets)
- [ ] Commit inicial na `main` com a documentação já existente em `docs/` (e demais arquivos do repo que devam versionar)
- [ ] Criar repositório no GitHub e `git push -u origin main`
- [ ] Abrir branch `fase/1-escopo-mvp` + PR draft para o trabalho de T-1.1/T-1.2

**Aceite:** `main` existe no GitHub; PR da F1 aberta; working tree pronta para docs de escopo.

### T-1.1 — Escopo comercial e de IA

**Pilares:** P01

- [ ] Definir categorias MVP (ex.: ventiladores de teto + peças de reposição)
- [ ] Listar fabricantes/manuais de validação (mín. 3 layouts diferentes)
- [ ] Confirmar critérios de sucesso de [`specify.md`](specify.md) §7
- [ ] Explicitar fora de escopo imediato (WhatsApp, multi-idioma prod, PWA, assinatura, assistências)
- [ ] Registrar decisão: IA só entra se transformar manual em venda, suporte ou economia

**Aceite:** documento de escopo MVP aprovado; lista de manuais de teste definida.

### T-1.2 — Schema mínimo de produto

**Pilares:** P01, P11

- [ ] Definir campos mínimos de `Product` para vender (SKU, nome, preço, estoque, specs-chave, compatibilidade)
- [ ] Prever i18n no schema sem implementar conteúdo multi-idioma
- [ ] Mapear campos extraíveis do manual → schema

**Aceite:** schema mínimo documentado e alinhado à F3/F4a.

**Encerramento F1 (R2/D7):** marcar PR ready → squash merge na `main` → apagar branch → só então iniciar F0.

---

## Fase 2 — Base do projeto

> Objetivo: monólito modular com cinto de segurança desde o dia 1.  
> Pilares: **P04, P05, P06, P07, P12, P13, P14, P15** (+ layout base da F0)

### T-2.1 — Estrutura do monólito Django

**Pilares:** P04, P12

- [ ] Criar apps: `accounts`, `catalog`, `products`, `cart`, `checkout`, `orders`, `tickets`, `ai`, `manuals`, `compatibility`, `dashboard`, `notifications`, `core`
- [ ] Templates base + static com tema da F0
- [ ] Header/nav e footer no padrão Industrial Precision
- [ ] Configurar Django Templates + htmx + Alpine.js pontual
- [ ] Settings por ambiente (local / staging / production)

**Aceite:** `runserver` sobe com layout base; apps vazios criados.

### T-2.2 — Docker e serviços locais

**Pilares:** P04, P14

- [ ] Compose: Django, PostgreSQL (+ pgvector), Redis, Celery worker/beat, Flower, Nginx (opcional local)
- [ ] Healthchecks básicos
- [ ] Documentar `make up` / comandos de bootstrap

**Aceite:** stack sobe com um comando; Postgres com pgvector disponível.

### T-2.3 — CI/CD, qualidade e commits

**Pilares:** P06, P14 · **Regra:** R3

- [ ] GitHub Actions: lint (ruff + black), testes pytest, check migrations
- [ ] Pre-commit: black, ruff, detect-secrets
- [ ] Conventional Commits + commitlint
- [ ] Bandit + pip-audit/Dependabot
- [ ] pytest + pytest-django + pytest-cov configurados; job de CI bloqueia merge se falhar
- [ ] Suíte smoke inicial (ex.: health/settings) para a R3 valer desde o primeiro PR de código
- [ ] Stub de coverage nos apps críticos (meta ≥ 80% em checkout/pagamento/extração quando existirem)

**Aceite:** PR sem lint/testes verdes não mergeia; commits padronizados; R3 aplicável.

### T-2.4 — Segurança, secrets e observabilidade base

**Pilares:** P05, P07, P13, P15

- [ ] Secrets só via env / secret manager (nunca no repo)
- [ ] HTTPS/HSTS, cookies secure/HttpOnly/SameSite, CSRF, CSP básico
- [ ] Auth Django + grupos/RBAC inicial (admin, revisão catálogo, suporte)
- [ ] structlog com `request_id`; mascaramento de PII
- [ ] Sentry integrado (Django + Celery)
- [ ] Rate limit stub nos endpoints futuros de IA

**Aceite:** app sem secrets no git; erro de teste aparece no Sentry de staging.

### T-2.5 — Contas, 2FA staff e auditoria

**Pilares:** P05, P15

- [ ] Login/logout; proteção brute-force (django-axes ou equivalente)
- [ ] 2FA obrigatório para staff/admin
- [ ] Trilha de auditoria para ações sensíveis (base com django-simple-history ou equivalente)

**Aceite:** staff sem 2FA não acessa admin; ações sensíveis registradas.

---

## Fase 3 — Pipeline de ingestão de manuais

> Objetivo: coração do diferencial — PDF → extração → revisão humana → rascunho.  
> Pilares: **P02, P09, P11** (+ P05/P15 uploads)

### T-3.1 — Models e storage de manuais

**Pilares:** P09, P11

- [ ] Models: `Manual`, `ExtractionLog` (e vínculo futuro com `Product`)
- [ ] Upload para Cloudflare R2 (django-storages); bucket privado; URLs assinadas
- [ ] Validação MIME/tamanho + varredura antivírus antes do pipeline
- [ ] Versionar PDF fonte vinculado ao produto/manual

**Aceite:** PDF sobe no R2; log de extração criado; arquivo hostil rejeitado.

### T-3.2 — Extração de texto e estruturação com LangChain

**Pilares:** P02, P09

- [ ] Extrair texto/tabelas (pdfplumber/unstructured); OCR se escaneado
- [ ] Prompt versionado + `with_structured_output` / Pydantic (schema fixo)
- [ ] Task Celery: PDF → JSON estruturado → produto/rascunho
- [ ] Sanitizar conteúdo do manual antes do LLM (anti prompt injection via PDF)
- [ ] Medir tokens/custo por execução (hook LangSmith)

**Aceite:** ≥3 manuais reais geram JSON válido no schema; custo visível por run.

### T-3.3 — Human-in-the-loop (revisão)

**Pilares:** P02, P08, P09

- [ ] Produto nasce como **rascunho**; nunca publicar automático
- [ ] Django admin + evolução para tela amigável de revisão (fila, confiança, diff)
- [ ] Aprovar / corrigir / rejeitar com auditoria (quem, quando, o quê)
- [ ] UI da fila alinhada ao protótipo (`AdminManualsView` / `code (cópia 2).html`)

**Aceite:** nada vai ao catálogo sem aprovação humana; auditoria completa.

### T-3.4 — Golden set inicial de extração

**Pilares:** P02, P06

- [ ] Conjunto fixo de manuais + JSON esperado
- [ ] Script/teste local de regressão (CI completo na F6)
- [ ] Critério de qualidade mínimo para aprovação em massa

**Aceite:** regressão local detecta quebra de prompt.

---

## Fase 4a — Catálogo, estoque e carrinho

> Objetivo: navegar, filtrar, ver produto e adicionar ao carrinho com estoque confiável.  
> Pilares: **P11, P12, P17, P18, P19, P20, P21, P23** (+ P16/P24)

### T-4a.1 — Models de catálogo e estoque

**Pilares:** P11

- [ ] `Product`, categorias, imagens, specs
- [ ] Estoque: disponível, reservado, mínimo para alerta
- [ ] Model de compatibilidade (modelo × peça)
- [ ] Índices em SKU e compatibilidade
- [ ] Cache Redis para listagens/consultas quentes

**Aceite:** migrations aplicadas; reserva de estoque testada unitariamente.

### T-4a.2 — Listagem, busca e filtros

**Pilares:** P12, P21, P23

- [ ] Catálogo com htmx (filtros: categoria, voltagem, modelo, compatibilidade)
- [ ] Busca full-text Postgres + autocomplete com miniatura
- [ ] Empty state (“nenhum produto”) com sugestão de busca/diagnóstico
- [ ] Skeletons no carregamento de filtros
- [ ] Mobile-first; DoD visual

**Aceite:** filtrar e buscar sem reload completo; UX mobile OK.

### T-4a.3 — Página de produto (PDP)

**Pilares:** P17, P18, P20, P21

- [ ] Hierarquia: nome > preço > specs > descrição
- [ ] Specs em JetBrains Mono; whitespace generoso
- [ ] Imagens (WebP/AVIF via R2), lazy loading; zoom/ângulos se disponível
- [ ] Badge de compatibilidade; CTA Add to Cart / AI Action
- [ ] Microinterações hover (~200ms)

**Aceite:** PDP alinhada aos protótipos; DoD visual passa.

### T-4a.4 — Carrinho e reserva de estoque

**Pilares:** P12, P19, P20

- [ ] Carrinho htmx (add/update/remove)
- [ ] Reserva temporária no checkout para evitar overselling
- [ ] Feedback imediato ao adicionar
- [ ] Estados de erro (sem estoque) amigáveis

**Aceite:** não vende além do estoque em teste de concorrência simples.

### T-4a.5 — Verificador de compatibilidade e tela de revisão amigável

**Pilares:** P12, P23

- [ ] Widget: informar modelo → listar peças compatíveis (ORM, sem LLM)
- [ ] Tela interna de cadastro/revisão de produtos (além do admin cru)
- [ ] Gestão de categorias e relações de compatibilidade

**Aceite:** cliente acha peça pelo modelo; operação revisa sem admin cru.

---

## Fase 4b — Checkout, pagamento, frete e NF-e

> Objetivo: fechar o ciclo de compra legal no Brasil.  
> Pilares: **P05, P15** (+ UX P19–P21)

### T-4b.1 — Checkout e frete

**Pilares:** P12, P19, P21

- [ ] Fluxo checkout (endereço, frete, resumo)
- [ ] Integração frete (Melhor Envio / Correios) + fallback frete fixo
- [ ] UX mobile: teclado, steps claros, erros recuperáveis
- [ ] Alinhar ao protótipo de checkout

**Aceite:** pedido criado ponta a ponta em staging com frete calculado.

### T-4b.2 — Pagamento tokenizado

**Pilares:** P05, P15

- [ ] Gateway (Stripe / Mercado Pago / PagSeguro) com tokenização
- [ ] Backend nunca armazena dados de cartão — só token + status
- [ ] Webhooks com validação de assinatura
- [ ] Testes de sucesso/falha/estorno

**Aceite:** pagamento sandbox OK; nenhum PAN no banco/logs.

### T-4b.3 — NF-e e e-mail transacional

**Pilares:** P01 (legal), P13

- [ ] Emissão NF-e via provedor (task Celery pós-pagamento)
- [ ] Reprocessamento em falha da API fiscal
- [ ] E-mails: confirmação, NF-e (SES/SendGrid); log de bounce
- [ ] Templates de e-mail no tom da marca

**Aceite:** pedido pago gera NF-e + e-mail; falha fiscal não “some” silenciosa.

---

## Fase 4c — Chamados técnicos e cross-sell

> Objetivo: pós-venda básico + venda por compatibilidade.  
> Pilares: **P03, P08, P11, P12, P19**

### T-4c.1 — Área de chamados

**Pilares:** P11, P12, P19

- [ ] Model `Ticket` (status, origem, SLA, histórico, anexos)
- [ ] “Meus chamados” no site (htmx) + painel suporte
- [ ] Notificações de mudança de status (e-mail) e alerta de SLA (Celery beat)
- [ ] Empty/loading/error states; DoD visual
- [ ] Alinhar a `TicketsView` / `code (cópia 5).html`

**Aceite:** cliente abre e acompanha chamado; SLA estourado alerta a equipe.

### T-4c.2 — Cross-sell por compatibilidade

**Pilares:** P01, P23

- [ ] Sugestões na PDP e e-mail pós-compra a partir da tabela de compatibilidade
- [ ] Tracking simples de pedidos influenciados (para F7)

**Aceite:** peça relacionada aparece na PDP; dado de influência registrado.

---

## Fase 4d — Cupons, trocas e devoluções

> Objetivo: conveniência comercial após checkout estável.  
> Pilares: **P01, P12, P19**

### T-4d.1 — Cupons e promoções

**Pilares:** P12

- [ ] Model Cupom (código, tipo, validade, limites)
- [ ] Aplicar no carrinho via htmx
- [ ] Preço promocional por produto/categoria com vigência

**Aceite:** cupom válido reduz total; inválido mostra erro claro.

### T-4d.2 — Trocas, devoluções e direito de arrependimento

**Pilares:** P05, P15, P19

- [ ] Fluxo CDC 7 dias a partir da entrega
- [ ] Model de solicitação (motivo, status, reembolso/peça nova)
- [ ] Painel operação + reembolso via gateway
- [ ] Estados de UI claros em cada etapa

**Aceite:** solicitação de arrependimento no prazo funciona até reembolso sandbox.

---

## Fase 5 — Chat de suporte com RAG

> Objetivo: dúvidas técnicas com base no manual real, com UX de IA de primeira classe.  
> Pilares: **P02, P03, P07, P08, P10, P12, P13, P15** (+ P16/P19/P20/P21/P22)

### T-5.1 — Indexação e retrieval

**Pilares:** P02, P10, P11

- [ ] Chunking semântico (seção/parágrafo); preservar tabelas; metadados (produto, seção, página)
- [ ] Embeddings → `ManualChunk` + pgvector (índice HNSW/IVFFlat)
- [ ] Filtro por produto/categoria antes da busca semântica
- [ ] Task Celery de indexação pós-aprovação do manual

**Aceite:** pergunta de teste recupera o chunk correto do manual indexado.

### T-5.2 — Endpoint de chat + streaming SSE

**Pilares:** P03, P08, P10, P12

- [ ] View/DRF + htmx/JS: pergunta → retrieval → Claude → resposta
- [ ] Streaming via SSE (`StreamingHttpResponse`)
- [ ] Citação de fonte (página/seção) em toda resposta técnica
- [ ] Fallback explícito: “não encontrei isso no manual”
- [ ] Indicador “IA está digitando”; shell visual cyan; tag Technical Source
- [ ] Chat usável no mobile (input não coberto pelo teclado)
- [ ] Acessibilidade: teclado no chat; contraste

**Aceite:** resposta streama; fonte clicável/visível; mobile OK; DoD visual.

### T-5.3 — Feedback, rate limit e observabilidade do chat

**Pilares:** P03, P06, P07, P13, P15

- [ ] 👍/👎 (+ motivo opcional) por resposta; persistir com trechos usados
- [ ] Rate limiting por IP/usuário nos endpoints de IA
- [ ] Isolar system prompt; guardrails (conteúdo do manual ≠ instrução)
- [ ] LangSmith desde o dia 1; correlacionar `request_id` ↔ `trace_id`
- [ ] Alertas de custo e latência básicos

**Aceite:** feedback salvo; abuso rate-limited; trace LangSmith por conversa.

### T-5.4 — Escalonamento inicial para humano

**Pilares:** P03, P08

- [ ] 👎 (ou dois seguidos) / baixa confiança → abrir `Ticket` com histórico anexado
- [ ] Cliente não precisa repetir o relato

**Aceite:** feedback negativo gera chamado com histórico completo.

---

## Fase 6 — Diagnóstico assistido e LangGraph

> Objetivo: fluxos com estado; qualidade contínua no CI.  
> Pilares: **P02, P03, P06, P09, P10**

### T-6.1 — Grafo de diagnóstico

**Pilares:** P03, P10

- [ ] LangGraph: entender relato → decidir busca (manual / pedidos / pedir detalhes) → sugerir causa/peça
- [ ] Sempre citar trecho do manual
- [ ] Card de diagnóstico (confiança, ref. manual, SKUs recomendados) — ver `DiagnosticCardData`
- [ ] UI alinhada a `DiagnosticChatView` / `code.html`
- [ ] Tracking de pedidos vindos do diagnóstico

**Aceite:** sintoma de teste sugere peça correta com fonte; card renderiza.

### T-6.2 — HITL no grafo de extração

**Pilares:** P09

- [ ] Nó de interrupção LangGraph até aprovação no admin/tela de revisão
- [ ] Retomar de onde parou (não reiniciar o processo)

**Aceite:** pausa/retomada funciona em staging.

### T-6.3 — Busca de peça por foto

**Pilares:** P03, P15, P23

- [ ] Upload de imagem → R2 → Claude vision (Celery)
- [ ] Validação MIME/tamanho + rate limit
- [ ] Candidatos ranqueados na UI com loading/skeleton

**Aceite:** foto de peça de teste retorna candidatos; upload inválido rejeitado.

### T-6.4 — Golden set no CI e regressão de prompts

**Pilares:** P06, P14

- [ ] Golden set de extração no pipeline CI
- [ ] Dataset de perguntas/respostas esperadas do RAG (amostra)
- [ ] Bloquear merge se regressão piorar casos conhecidos

**Aceite:** CI falha ao quebrar caso golden propositalmente.

---

## Fase 7 — Beta, dashboard e monitoramento

> Objetivo: validar com usuários reais e dar visibilidade à operação.  
> Pilares: **P06, P07, P13** (+ P12 UI dashboard)

### T-7.1 — Dashboard de insights

**Pilares:** P07, P12, P13

- [ ] Métricas chat/RAG: perguntas frequentes, resolução sem humano, média 👍/👎
- [ ] Métricas chamados: volume, TMR, SLA, origem
- [ ] Vendas influenciadas por IA (diagnóstico, foto, cross-sell)
- [ ] Custo de IA no período (extração vs chat)
- [ ] UI no design system (não admin cru)

**Aceite:** operação vê as 4 áreas sem abrir ferramentas externas.

### T-7.2 — Monitoramento consolidado

**Pilares:** P13

- [ ] Painel: falhas recentes, filas atrasadas, uptime — com links Sentry/Flower/Grafana
- [ ] Alertas (custo, erro recorrente, SLA) visíveis no painel + Slack/e-mail

**Aceite:** incidente simulado aparece no painel e no canal de alerta.

### T-7.3 — Beta fechado e loop de qualidade

**Pilares:** P01, P06

- [ ] Recrutar usuários reais; script de testes (cadastro via manual, compra, chat, chamado)
- [ ] Coletar feedback UX/visual e de qualidade das respostas
- [ ] Atualizar golden set e prompts com base nos achados
- [ ] Revisar DoD visual nas telas críticas pós-beta

**Aceite:** relatório de beta com issues priorizadas; critérios de sucesso do specify avaliados.

---

## Fase 8 — Iteração e escala

> Fora do escopo imediato do MVP, mas planejado para não distorcer o desenho.  
> Pilares: **P01, P05, P10, P15** (+ expansão)

### T-8.1 — Canais e idiomas

- [ ] Multi-idioma no catálogo e chat (estrutura já preparada)
- [ ] WhatsApp reaproveitando pipeline RAG/diagnóstico
- [ ] Hardening de segurança antes de tráfego maior

### T-8.2 — Novos modelos de negócio e campo

- [ ] Assinatura de manutenção preventiva
- [ ] Rede de assistências parceiras
- [ ] PWA offline para técnicos (manual + chamado)
- [ ] Garantia digital com QR-code

### T-8.3 — Escala de dados e catálogo

- [ ] Mais fabricantes/categorias
- [ ] Revisar índices, read replica/particionamento se volume justificar
- [ ] Revisar orçamento de tokens e rate limits

**Aceite (fase):** cada item acima com escopo próprio e ADR antes de iniciar.

---

## Matriz pilar × fase

| Pilar | Nome | Fase(s) principal(is) | Validação |
|---|---|---|---|
| P01 | Propósito e escopo | F1, F7, F8 | Escopo MVP; critérios specify |
| P02 | Qualidade dados/contexto | F3, F5, F6 | Schema, golden set, citações |
| P03 | UX pensada para IA | F5, F6 | Stream, fallback, escalonamento |
| P04 | Arquitetura técnica | F2 | Monólito, Celery, separação IA |
| P05 | Segurança e privacidade | F2, F4b, F8 | Secrets, pagamento, LGPD |
| P06 | Avaliação e testes | F2, F3, F6, F7 | CI, golden set, beta |
| P07 | Custo e performance | F2, F5, F7 | LangSmith, cache, alertas |
| P08 | Transparência | F3, F5 | Fonte, rótulos IA, HITL |
| P09 | Pipeline ingestão | F3, F6 | PDF→JSON→revisão |
| P10 | RAG técnico | F5, F6 | Chunks, pgvector, diagnóstico |
| P11 | Modelagem de dados | F1, F3, F4a, F4c | Models + pgvector |
| P12 | Frontend htmx | F2, F4*, F5, F7 | Telas storefront + ops |
| P13 | Observabilidade | F2, F5, F7 | Sentry, LangSmith, dashboard |
| P14 | CI/CD | F2, F6 | Pipeline + golden no CI |
| P15 | Segurança de domínio | F2, F3, F5, F4b | Uploads, injection, rate limit |
| P16 | Design system | F0 | Tokens + componentes |
| P17 | Hierarquia/tipografia | F0, F4a | PDP e listagens |
| P18 | Fotografia produto | F0, F4a | PDP + padrão de imagem |
| P19 | Estados de UI | F0, F4*, F5 | Skeleton/empty/error |
| P20 | Microinterações | F0, F4a, F5 | Hover, feedback, typing |
| P21 | Mobile-first | F0, F4*, F5 | Grid + chat mobile |
| P22 | Acessibilidade | F0, F5 | AA, teclado, alt |
| P23 | Busca e filtros | F4a, F6 | Filtros, sintoma, foto |
| P24 | Identidade de marca | F0, F4*, F5 | Consistência PDP↔chat |

---

## Definition of Done visual/UX

Usar em **toda** tarefa que entregue UI. Marcar só quando todos aplicáveis passarem:

- [ ] **Marca:** parece TechParts AI (navy + cyan só em IA); não parece Bootstrap genérico
- [ ] **Hierarquia:** título > preço/ação > specs > corpo; JetBrains Mono em dados técnicos
- [ ] **Whitespace:** seções com respiro; página não “cheia”
- [ ] **Estados:** loading (skeleton), vazio e erro com próximo passo claro
- [ ] **Feedback:** ação do usuário tem resposta visual imediata (~200ms)
- [ ] **Mobile:** usável em viewport estreito; chat com input acessível
- [ ] **A11y:** contraste AA; foco teclado; `alt` onde couber
- [ ] **IA (se houver):** rótulo de IA, fonte citada, fallback sem inventar, indicador de digitação
- [ ] **Protótipo:** confrontado com `docs/code*.html` / `DESIGN.md` quando existir tela equivalente

---

## Dependências críticas

| Dependência | Bloqueia |
|---|---|
| F0 tokens/componentes | Qualidade visual de F2 layout e todas as telas F4–F7 |
| F2 Docker + CI + secrets | Qualquer deploy/staging e trabalho seguro em F3+ |
| F3 pipeline + revisão humana | Catálogo alimentado por IA e indexação RAG |
| F4a catálogo + estoque | Carrinho, checkout, compatibilidade, cross-sell |
| F4b checkout + NF-e | Venda legal; beta com compra real |
| F5 chat RAG | Diagnóstico LangGraph (F6) e métricas de chat (F7) |
| F4c tickets | Escalonamento automático do chat (F5/F6) |
| Indexação pgvector (F5.1) | Qualidade das respostas do chat |
| LangSmith + feedback (F5.3) | Loop de qualidade e dashboard de custo (F7) |

---

## Ordem sugerida de execução (equipe pequena)

Sequência de alto nível (ajustar duração à capacidade; ~1 unidade = bloco de foco). **Cada linha = 1 branch + 1 PR + merge na `main` (R2).** Dependências novas = maior versão estável (R1).

| Ordem | Bloco | Foco |
|---|---|---|
| 1 | F1 | Bootstrap git/remote (T-1.0) + escopo MVP + schema (PR docs) |
| 2 | F0 | Design system (tokens, componentes, a11y, marca) |
| 3 | F2 | Repo/Docker/CI/segurança + layout base no tema F0 |
| 4 | F3 | Pipeline manuais + HITL + golden set local |
| 5 | F4a | Catálogo, PDP, estoque, carrinho, compatibilidade |
| 6 | F4b | Checkout, pagamento, frete, NF-e, e-mail |
| 7 | F4c | Chamados + cross-sell |
| 8 | F4d | Cupons + trocas/CDC |
| 9 | F5 | RAG, stream, feedback, rate limit, LangSmith |
| 10 | F6 | Diagnóstico, foto, HITL grafo, golden no CI |
| 11 | F7 | Dashboard, alertas, beta, ajustes |
| 12 | F8 | Itens de escala sob demanda (ADR + PR por item) |

**Regra de ouro:** não iniciar F5 sem ao menos um conjunto de manuais aprovados e produtos publicados; não iniciar F7 sem feedback 👍/👎 e traces LangSmith fluindo; não iniciar fase seguinte sem merge da anterior na `main`.

---

## Critérios de sucesso do sistema (visão specify)

O plano está cumprido quando:

1. Produto novo entra via manual com pouco esforço humano e qualidade revisável.
2. Chat resolve parcela relevante das dúvidas com fonte; ao escalar, histórico vai junto.
3. Cliente descobre a peça por sintoma, modelo ou foto.
4. Operação acompanha vendas, chamados, custo de IA e qualidade sem ferramentas cruas.
5. Loja vende no Brasil com NF-e, arrependimento e LGPD desde o primeiro pedido.
6. UI/UX respeitam os pilares P16–P24 em todas as superfícies críticas (catálogo, PDP, checkout, chat, chamados, revisão, dashboard).
