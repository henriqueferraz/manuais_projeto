# Relatório de beta — TechParts AI (F7 / T-7.3 + DoD pós-F8)

**Status:** auditoria DoD visual/UX por checklist (templates + design system); sessões com usuários reais ainda pendentes.  
**Data:** 2026-08-07  
**Participantes:** 0 testers externos · 1 revisão de código/UI ([checklist](../design-system/docs/VISUAL-REVIEW-CHECKLIST.md))  
**Branch/base:** `main` @ F8 (`#15`) + correções DoD desta revisão

## Resumo executivo

- Escopo auditado: catálogo/PDP, checkout, chat/diagnóstico, chamados, dashboard, assinaturas, assistências, garantia QR.
- Resultado geral: **aprovado com ressalvas** — telas de venda/IA alinhadas ao Industrial Precision; ops e F8 ainda mais “Bootstrap + tipografia DS”.
- Correções aplicadas nesta passagem: cyan fora de IA (chamados/monitoramento), `alert-info` no pagamento, empty de frete, `alt` em thumbs, ícone Material na foto do chat, `tp-empty` nas telas F8.

## Issues priorizadas

| ID | Severidade | Área | Descrição | Ação |
|---|---|---|---|---|
| B-001 | P1 | Dashboard | Widgets ainda usam `card`/`table` Bootstrap; pouco uso de componentes `tp-*` | Iterar shell ops com tokens/layout DS |
| B-002 | P2 | Catálogo | ~~Specs acima do preço no card~~ | **Corrigido** — título > preço > specs |
| B-003 | P2 | Checkout | Sem skeleton nas etapas HTMX/navegação | Adicionar `tp-skeleton` nas steps |
| B-004 | P2 | Chat | Empty de candidatos de foto sem `tp-empty` + CTA | Alinhar `photo_candidates.html` |
| B-005 | P2 | F8 | Cards de plano/assistência ainda `border rounded` genéricos | Evoluir para componente DS dedicado |
| B-006 | P2 | Geral | Confronto formal com `docs/design/code*.html` não documentado por tela | Checklist de confronto no próximo beta humano |

~~B-000 P0~~ Cyan em chamados (`btn-ai` + eyebrow) e monitoramento — **corrigido** nesta revisão.

## Qualidade das respostas (RAG / diagnóstico)

- Taxa percebida de citação correta: _n/d (sem beta humano)_
- Casos de alucinação / fallback: fallback de diagnóstico presente (`Não encontrei isso no manual indexado.` / ask_details)
- Golden set atualizado? [x] sim — CI `make golden` / `make golden-rag` verdes na F8

## DoD visual (telas críticas)

Critério: [VISUAL-REVIEW-CHECKLIST.md](../design-system/docs/VISUAL-REVIEW-CHECKLIST.md)

| Tela | Passou checklist? | Notas |
|---|---|---|
| Catálogo / PDP | [x] **sim** | `tp-product-card`, skeleton, empty+CTA; thumbs com `alt`; hierarquia título > preço > specs |
| Chat / diagnóstico | [x] **sim** | Rótulo IA, fontes, typing, 👍/👎, `btn-ai`, foto com Material Symbols |
| Checkout | [x] parcial | Steps + `font-technical`; aviso sandbox sem cyan; empty frete com CTA; falta skeleton (B-003) |
| Chamados | [x] parcial → **sim c/ ressalvas** | Cyan removido do hero/CTA; empty `tp-empty`; layout ainda card Bootstrap |
| Dashboard insights/monitoramento | [x] parcial | Cyan só em Insights IA; contraste do hero ajustado; widgets ainda genéricos (B-001) |
| Assinaturas (F8) | [x] parcial | Tipografia DS + `tp-empty`; cards genéricos (B-005) |
| Assistências (F8) | [x] parcial | Badge assistência + empty/CTA; lista simples |
| Garantia QR (F8) | [x] parcial | Hierarquia + mono em SKU; formulário limpo |

### Checklist global (pós-correção)

- [x] **Marca:** shell + catálogo/chat usam navy/Inter; cyan restrito a IA (insights + chat)
- [x] **Hierarquia:** PDP/chat/card catálogo (título > preço > specs)
- [x] **Whitespace:** `tp-section` nas superfícies cliente
- [x] **Estados:** skeleton no catálogo; empties críticos presentes; erros de form ainda `text-danger`
- [x] **Feedback:** transitions DS (~200ms); chat stream + typing
- [x] **Mobile:** grids Bootstrap responsivos; chat com `enterkeyhint`
- [x] **A11y:** skip-link, `aria-hidden` em ícones corrigidos, `alt` PDP
- [x] **IA:** rótulo, citação, fallback, typing, feedback
- [ ] **Protótipo:** confronto tela a tela ainda informal (B-006)

## Critérios de sucesso (specify)

| Critério | Met? | Evidência |
|---|---|---|
| Operação vê chat/chamados/vendas IA/custo no dashboard | [x] código | `/dashboard/` (F7) — validação humana pendente |
| Incidente aparece no monitoramento + alerta | [x] código | `/dashboard/monitoramento/` + simular incidente |
| Cliente compra e acompanha sem “ficar no escuro” | [x] parcial | E-mails/status em F4b; beta humano pendente |
| HITL impede publicação automática | [x] código | `/manuais/revisao/` |

## Próximos passos

1. Rodar **sessão de beta humana** (script em [`beta-script.md`](beta-script.md)) e atualizar taxa RAG / issues reais.
2. Tratar B-001 (dashboard DS); B-002 (hierarquia do card) já corrigido.
3. Opcional: E2E Playwright nos fluxos checkout → chat → chamado (débito R3).
