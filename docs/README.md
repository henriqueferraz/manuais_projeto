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

## Decisões e arquitetura

| Documento | Uso |
|---|---|
| [`adr/`](adr/) | ADRs (decisões versionadas) |
| [`constitution.md`](constitution.md) | Princípios / restrições do projeto |
| [`specify.md`](specify.md) | Critérios de sucesso / especificação |
| [`plan.md`](plan.md) | Visão técnica de arquitetura (alto nível) |
| [`fase-1-escopo-mvp.md`](fase-1-escopo-mvp.md) · [`fase-1-schema-produto.md`](fase-1-schema-produto.md) | Escopo e schema do MVP |

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
| [`pilares/`](pilares/) · [`pilares-app-ia-vendas-pecas.md`](pilares-app-ia-vendas-pecas.md) | Os 24 pilares |
| [`plano-ecommerce-ia-pecas.md`](plano-ecommerce-ia-pecas.md) | Roadmap longo original |
| [`techparts_ai_project_brief.md`](techparts_ai_project_brief.md) | Brief inicial |

## O que **não** usar

- `docs/.env.example` — **removido** (era stub Gemini/AI Studio, não deste monólito).
- Credenciais em `.env` commitadas — só `.env.example` na raiz.
- `docs/design/design.md` como tokens vigentes — use `DESIGN.md`.
