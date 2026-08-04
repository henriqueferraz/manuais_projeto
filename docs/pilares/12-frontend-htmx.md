# Pilar 12 — Frontend com htmx

> **Parte 2 — Pilares Específicos do Projeto** · Fonte-mestre: [`pilares-app-ia-vendas-pecas.md`](../pilares-app-ia-vendas-pecas.md)

## Definição do pilar

Streaming SSE; hx-indicator; feedback 👍/👎; Bootstrap.

## Abordagem

- Django Templates + htmx (SSR, um deploy, SEO nativo)
- Bootstrap 5 para componentes padrão
- Alpine.js / JS pontual onde htmx não basta (chat, verificador interativo)
- DRF só onde precisar de API real (chat JS, WhatsApp futuro, mobile)

## Interações htmx previstas

- Busca e filtros em tempo real
- Adicionar ao carrinho
- Indicadores de carregamento (`hx-indicator`)
- Feedback 👍/👎 em respostas técnicas
- Streaming de chat via SSE

## Telas do domínio (protótipos)

| Tela | Arquivo / componente |
|---|---|
| Home / catálogo | `code (cópia 3|4).html`, `CatalogView`, `HeroSection` |
| Produto | `code (cópia 6|7|11).html`, `ProductDetailView` |
| Checkout | `code (cópia 1|8).html`, `CartCheckoutView` |
| Diagnóstico | `code.html`, `code (cópia 9).html`, `DiagnosticChatView` |
| Chamados | `code (cópia 5).html`, `TicketsView` |
| Admin manuais | `code (cópia 2).html`, `AdminManualsView` |
| Dashboard | `DashboardSection` |

> Os HTML em `docs/` e o app React em `docs/src/` são **protótipos de UX/visual**. A implementação alvo permanece Django + htmx + Bootstrap.

## Fontes

- `plan.md` — Frontend
- `plano-ecommerce-ia-pecas.md` — Frontend (loja)
- `design.md` — Implementation Notes
