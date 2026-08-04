# Pilares — documentação separada por pilar

Consolidação do conteúdo de `docs/` organizado segundo `pilares-app-ia-vendas-pecas.md` (24 pilares).

Cada arquivo reúne a **definição do pilar** e o **conteúdo extraído** de constitution, specify, plan, plano-ecommerce, brief, design system e referências aos protótipos (HTML/`src`).

## Como usar

1. Leia o índice de pilares em [`../pilares-app-ia-vendas-pecas.md`](../pilares-app-ia-vendas-pecas.md)
2. Abra o arquivo do pilar em que for trabalhar
3. As seções **Fontes** apontam de volta aos documentos originais
4. Para executar o desenvolvimento, siga o plano de tarefas em [`../plano-tarefas.md`](../plano-tarefas.md) (fases 0–8, subtarefas, matriz pilar × fase e DoD visual/UX)

## Parte 1 — Gerais para Apps de IA

| # | Arquivo | Pilar |
|---|---------|-------|
| 01 | [01-proposito-e-escopo.md](01-proposito-e-escopo.md) | Propósito e escopo |
| 02 | [02-qualidade-dados-contexto.md](02-qualidade-dados-contexto.md) | Qualidade dos dados e do contexto |
| 03 | [03-ux-pensada-para-ia.md](03-ux-pensada-para-ia.md) | UX pensada para IA |
| 04 | [04-arquitetura-tecnica.md](04-arquitetura-tecnica.md) | Arquitetura técnica sólida |
| 05 | [05-seguranca-e-privacidade.md](05-seguranca-e-privacidade.md) | Segurança e privacidade |
| 06 | [06-avaliacao-e-testes.md](06-avaliacao-e-testes.md) | Avaliação e testes contínuos |
| 07 | [07-custo-e-performance.md](07-custo-e-performance.md) | Custo e performance |
| 08 | [08-transparencia-com-usuario.md](08-transparencia-com-usuario.md) | Transparência com o usuário |

## Parte 2 — Específicos do projeto

| # | Arquivo | Pilar |
|---|---------|-------|
| 09 | [09-pipeline-ingestao-manuais.md](09-pipeline-ingestao-manuais.md) | Pipeline de ingestão de manuais |
| 10 | [10-rag-duvidas-tecnicas.md](10-rag-duvidas-tecnicas.md) | RAG para dúvidas técnicas |
| 11 | [11-modelagem-de-dados.md](11-modelagem-de-dados.md) | Modelagem de dados |
| 12 | [12-frontend-htmx.md](12-frontend-htmx.md) | Frontend com htmx |
| 13 | [13-observabilidade.md](13-observabilidade.md) | Observabilidade |
| 14 | [14-cicd.md](14-cicd.md) | CI/CD |
| 15 | [15-seguranca-aplicada-dominio.md](15-seguranca-aplicada-dominio.md) | Segurança aplicada ao domínio |

## Parte 3 — Experiência visual e design

| # | Arquivo | Pilar |
|---|---------|-------|
| 16 | [16-design-system.md](16-design-system.md) | Design System |
| 17 | [17-hierarquia-visual-tipografia.md](17-hierarquia-visual-tipografia.md) | Hierarquia visual e tipografia |
| 18 | [18-fotografia-apresentacao-produto.md](18-fotografia-apresentacao-produto.md) | Fotografia e apresentação |
| 19 | [19-estados-de-interface.md](19-estados-de-interface.md) | Estados de interface |
| 20 | [20-microinteracoes-feedback.md](20-microinteracoes-feedback.md) | Microinterações e feedback |
| 21 | [21-responsividade-mobile-first.md](21-responsividade-mobile-first.md) | Responsividade mobile-first |
| 22 | [22-acessibilidade.md](22-acessibilidade.md) | Acessibilidade |
| 23 | [23-busca-e-filtros.md](23-busca-e-filtros.md) | Busca e filtros |
| 24 | [24-identidade-visual-marca.md](24-identidade-visual-marca.md) | Identidade visual da marca |

## Mapa rápido: documento original → pilares

| Documento original | Pilares principais |
|---|---|
| `constitution.md` | 1, 2, 5, 6, 7, 8, 13, 14, 15 |
| `specify.md` | 1, 2, 3, 8, 9, 10, 23 |
| `plan.md` | 4, 9, 10, 11, 12, 13, 14 |
| `plano-ecommerce-ia-pecas.md` | quase todos (plano mestre) |
| `techparts_ai_project_brief.md` | 1, 16, 23, 24 |
| `DESIGN.md` / `design.md` | 16–24 |
| `code*.html` / `src/` / `screen*.png` | 3, 9, 10, 12, 16–24 (protótipos) |

## O que não foi “partido” em pilares

Arquivos de tooling do protótipo React (`package.json`, `tsconfig.json`, `index.html`, `.env.example`, `metadata.json`) permanecem em `docs/` — não são requisitos de pilar, são suporte ao mock visual.
