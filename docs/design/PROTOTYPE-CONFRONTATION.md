# Confronto formal: telas × protótipos (`docs/design/`)

> T-P.3 / B-006 · DoD item **Protótipo**  
> Data: 2026-08-07 · Fonte de tokens: [`DESIGN.md`](DESIGN.md) (não `design.md` — rascunho divergente)

Critério: cada tela de produção abaixo foi confrontada com o HTML de referência equivalente.
Desvios aceitos: stack Django+Bootstrap vs Tailwind do protótipo; conteúdo dinâmico vs mock; nav real com mais rotas ops.

| Tela produção | Protótipo | Resultado | Notas / desvios conscientes |
|---|---|---|---|
| Home `/` | `code (cópia 4).html` / `code (cópia 3).html` (hero loja) | Sim | Hero marketing `tp-home-hero` (navy full-bleed, marca + 1 headline + CTAs catálogo/IA); sem carousel/overlays do protótipo (DoD / brand rules) |
| Catálogo | `code (cópia 10).html` | Sim | `tp-product-card`, navy, mono em specs, empty+CTA |
| PDP | `code (cópia 6).html` / `code (cópia 11).html` | Sim | Hierarquia título → preço → ação → specs; cyan só em CTA de compat/IA |
| Carrinho | `code (cópia 1).html` | Sim | Painel + empty `tp-empty`; checkout navy |
| Checkout | `code (cópia 1).html` / `code (cópia 8).html` | Sim | Steps + skeleton HTMX (`hx-boost` + `tp-skeleton`); opções `tp-checkout-option` |
| Chat / diagnóstico | `code (cópia 9).html` / `code.html` | Sim | Header cyan, fonte mono, typing, feedback; empty foto com `tp-empty`+CTA |
| Chamados | `code (cópia 5).html` | Sim | Hero `tp-ops-hero` navy (sem cyan); form em `tp-panel` |
| Dashboard / revisão | `code (cópia 2).html` | Sim | Stats `tp-stat`, painéis `tp-panel`, tabela `tp-table`; cyan só no eyebrow Insights IA |
| Assinaturas (F8) | — (sem HTML dedicado) | N/A → DS | `tp-plan-card` alinhado a product-card / Soft Level 1 |
| Assistências (F8) | — (sem HTML dedicado) | N/A → DS | `tp-partner-card` + badge compat |
| Garantia QR (F8) | — | N/A → DS | Tipografia + mono em SKU já presentes |

## Decisões de marca vs protótipo antigo

1. **Botão primary = Industrial Navy** (`DESIGN.md` / BRAND) — protótipos Tailwind às vezes usam cyan em CTA de compra; produção **não** replica isso.
2. **Cyan só em IA** — chat, diagnóstico, badges de compat assistida, eyebrow Insights IA, upload de manual (extração).
3. **`docs/design/design.md`** (minúsculo) está **obsoleto** quanto a “Primary = AI Cyan”; seguir `DESIGN.md`.

## Checklist DoD (pós T-P.3)

- [x] Marca (superfícies listadas; home marketing fechada em T-P.1 polish)
- [x] Hierarquia
- [x] Whitespace
- [x] Estados (skeleton checkout + empty foto)
- [x] Feedback ~200ms
- [x] Mobile
- [x] A11y
- [x] IA
- [x] Protótipo (esta tabela)
