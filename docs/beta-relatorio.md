# Relatório de beta — TechParts AI (F7 / T-7.3 + DoD pós-F8)

**Status:** auditoria DoD visual/UX por checklist (templates + design system); sessões com usuários reais ainda pendentes.  
**Data:** 2026-08-07  
**Participantes:** 0 testers externos · 2 revisões de código/UI ([checklist](../design-system/docs/VISUAL-REVIEW-CHECKLIST.md))  
**Branch/base:** `main` @ F8 (`#15`) + T-P.3 (fechamento DoD residual)

## Resumo executivo

- Escopo auditado: catálogo/PDP, checkout, chat/diagnóstico, chamados, dashboard, assinaturas, assistências, garantia QR.
- Resultado geral: **aprovado** nas telas do T-P.3 — componentes `tp-*` em ops/F8; skeleton no checkout; empty de foto; confronto documentado.
- Débito consciente: home marketing vs protótipo hero (fora do T-P.3); beta humana ainda pendente (T-P.1).

## Issues priorizadas

| ID | Severidade | Área | Descrição | Ação |
|---|---|---|---|---|
| B-001 | P1 | Dashboard | ~~Widgets `card`/`table` Bootstrap~~ | **Corrigido** — `tp-stat` / `tp-panel` / `tp-table` / `tp-ops-hero` |
| B-002 | P2 | Catálogo | ~~Specs acima do preço no card~~ | **Corrigido** — título > preço > specs |
| B-003 | P2 | Checkout | ~~Sem skeleton nas etapas~~ | **Corrigido** — `hx-boost` + `#checkout-skeleton` |
| B-004 | P2 | Chat | ~~Empty foto sem `tp-empty`~~ | **Corrigido** — `tp-empty` + CTAs assistente/catálogo |
| B-005 | P2 | F8 | ~~Cards genéricos~~ | **Corrigido** — `tp-plan-card` / `tp-partner-card` |
| B-006 | P2 | Geral | ~~Confronto informal~~ | **Corrigido** — [`PROTOTYPE-CONFRONTATION.md`](design/PROTOTYPE-CONFRONTATION.md) |
| HOME | P2 | Home | Hero loja vs shell técnico | Adiado — fora do aceite T-P.3 |

~~B-000 P0~~ Cyan em chamados/monitoramento — **corrigido** em revisão anterior.

## Qualidade das respostas (RAG / diagnóstico)

- Taxa percebida de citação correta: _n/d (sem beta humano)_
- Casos de alucinação / fallback: fallback de diagnóstico presente (`Não encontrei isso no manual indexado.` / ask_details)
- Golden set atualizado? [x] sim — CI `make golden` / `make golden-rag` verdes na F8

## DoD visual (telas críticas)

Critério: [VISUAL-REVIEW-CHECKLIST.md](../design-system/docs/VISUAL-REVIEW-CHECKLIST.md)

| Tela | Passou checklist? | Notas |
|---|---|---|
| Catálogo / PDP | [x] **sim** | Hierarquia título > preço > ação > specs |
| Chat / diagnóstico | [x] **sim** | Empty foto com `tp-empty` + CTA |
| Checkout | [x] **sim** | Skeleton HTMX nas steps; `tp-checkout-option` |
| Chamados | [x] **sim** | `tp-ops-hero` + `tp-panel` (sem cyan) |
| Dashboard insights/monitoramento | [x] **sim** | `tp-stat` / `tp-panel` / `tp-table` |
| Assinaturas (F8) | [x] **sim** | `tp-plan-card` |
| Assistências (F8) | [x] **sim** | `tp-partner-card` |
| Garantia QR (F8) | [x] **sim** | Tipografia + mono em SKU |

### Checklist global (pós T-P.3)

- [x] **Marca:** navy/Inter; cyan restrito a IA (home marketing ainda parcial — HOME)
- [x] **Hierarquia:** PDP/chat/card catálogo
- [x] **Whitespace:** `tp-section` / painéis DS
- [x] **Estados:** skeleton catálogo + checkout; empties críticos com CTA
- [x] **Feedback:** transitions DS (~200ms); chat stream + typing
- [x] **Mobile:** grids responsivos; chat com `enterkeyhint`
- [x] **A11y:** skip-link, `aria-hidden`, `alt` PDP
- [x] **IA:** rótulo, citação, fallback, typing, feedback
- [x] **Protótipo:** [`PROTOTYPE-CONFRONTATION.md`](design/PROTOTYPE-CONFRONTATION.md)

## Critérios de sucesso (specify)

| Critério | Met? | Evidência |
|---|---|---|
| Operação vê chat/chamados/vendas IA/custo no dashboard | [x] código | `/dashboard/` (F7) — validação humana pendente |
| Incidente aparece no monitoramento + alerta | [x] código | `/dashboard/monitoramento/` + simular incidente |
| Cliente compra e acompanha sem “ficar no escuro” | [x] parcial | E-mails/status em F4b; beta humano pendente |
| HITL impede publicação automática | [x] código | `/manuais/revisao/` |

## Próximos passos

1. Rodar **sessão de beta humana** (script em [`beta-script.md`](beta-script.md)) e atualizar taxa RAG / issues reais.
2. Opcional: reforçar home marketing (HOME) e E2E Playwright (T-P.6).
