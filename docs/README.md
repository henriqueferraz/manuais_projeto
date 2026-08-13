# Índice da documentação — TechParts AI

Guia rápido de **quais documentos usar**. Evita ler rascunhos obsoletos ou fontes duplicadas.

## Começar pelo produto

| Documento | Uso |
|---|---|
| [`../README.md`](../README.md) | **Primeiros passos**, bootstrap local/Docker e configuração inicial |
| [`.env.example`](../.env.example) (raiz) | **Única** fonte de variáveis de ambiente de exemplo |
| [`deploy.md`](deploy.md) | Staging, produção, backup (RPO) |
| [`security-hardening.md`](security-hardening.md) | Checklist de segurança pré-go-live |
| [`plano-tarefas.md`](plano-tarefas.md) | Status das fases F0–F8 e pós-F8 |
| [`regra-ouro-campos-produto.md`](regra-ouro-campos-produto.md) | Normalização de campos no cadastro / IA |
| [`regra-ouro-documentacao.md`](regra-ouro-documentacao.md) | **Obrigatório:** atualizar docs + docstrings após cada mudança |

## Decisões e arquitetura

| Documento | Uso |
|---|---|
| [`adr/`](adr/) | ADRs (decisões versionadas) |
| [`constitution.md`](constitution.md) | Princípios / restrições do projeto |
| [`specify.md`](specify.md) | Critérios de sucesso / especificação |
| [`plan.md`](plan.md) | Visão técnica de arquitetura (alto nível; LLM vigente = OpenAI) |
| [`fase-1-escopo-mvp.md`](fase-1-escopo-mvp.md) | Escopo do MVP |
| [`fase-1-schema-produto.md`](fase-1-schema-produto.md) | Schema inicial F1 (**evoluiu**: multi-categoria — ver nota no doc + [`pages/dashboard-produto.md`](pages/dashboard-produto.md)) |

## Páginas (telas)

| Documento | Uso |
|---|---|
| [`pages/`](pages/) | Índice das docs de tela |
| [`pages/inventory.md`](pages/inventory.md) | Rota → template → função (storefront + ops) |
| [`pages/dashboard-produto.md`](pages/dashboard-produto.md) | Criar/editar produto (multi-categoria, IA, fotos) |
| [`pages/assistente-chat.md`](pages/assistente-chat.md) | Chat / diagnóstico (confiança, contexto) |
| [`pages/checkout.md`](pages/checkout.md) | Checkout + Preference Mercado Pago |

## API interna (código)

| Documento | Uso |
|---|---|
| [`api/`](api/) | Índice MkDocs / mkdocstrings |
| [`../mkdocs.yml`](../mkdocs.yml) | Site local: `pip install -r requirements/docs.txt && mkdocs serve` |
| Gate CI | `interrogate` nos models/services (meta 80%) |

## Design

| Documento | Uso |
|---|---|
| [`design/DESIGN.md`](design/DESIGN.md) | **Fonte de verdade** dos tokens (Industrial Precision) |
| [`../design-system/`](../design-system/) | Tokens CSS, componentes, BRAND, preview |
| [`design/design.md`](design/design.md) | **Obsoleto** (rascunho; cyan como CTA — não seguir) |
| [`design/PROTOTYPE-CONFRONTATION.md`](design/PROTOTYPE-CONFRONTATION.md) | Confronto protótipo × produção |

## Beta e qualidade

| Documento | Uso |
|---|---|
| [`beta-script.md`](beta-script.md) | Roteiro de sessão beta |
| [`beta-relatorio.md`](beta-relatorio.md) | Relatório / issues do beta |

## Pilares e histórico (referência)

| Documento | Uso |
|---|---|
| [`pilares/`](pilares/) · [`pilares-app-ia-vendas-pecas.md`](pilares-app-ia-vendas-pecas.md) | Os 24 pilares (alguns trechos históricos; ver notas OpenAI / `pages/`) |
| [`plano-ecommerce-ia-pecas.md`](plano-ecommerce-ia-pecas.md) | Roadmap longo original (**histórico**) |
| [`techparts_ai_project_brief.md`](techparts_ai_project_brief.md) | Brief inicial (**histórico**; stack LLM não é a vigente) |

## O que **não** usar

- `docs/.env.example` — **removido** (era stub Gemini/AI Studio, não deste monólito).
- Credenciais em `.env` commitadas — só `.env.example` na raiz.
- `docs/design/design.md` como tokens vigentes — use `DESIGN.md`.
- Protótipos React/`src/components/*.tsx` ou HTML `code (cópia N).html` como UI — use `backend/templates/` + [`pages/inventory.md`](pages/inventory.md).
- Claude/Anthropic como provedor default — use OpenAI via `*_LLM_MODE` (CI = `mock`).
