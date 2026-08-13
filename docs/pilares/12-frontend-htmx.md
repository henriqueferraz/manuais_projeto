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

## Telas do domínio

Inventário atualizado (rota → template → função): [`../pages/inventory.md`](../pages/inventory.md).  
Formulário de produto (multi-categoria): [`../pages/dashboard-produto.md`](../pages/dashboard-produto.md).

| Tela | Rota / template |
|---|---|
| Home | `/` → `core/home.html` |
| Catálogo | `/catalogo/` → `catalog/product_list.html` |
| Produto (PDP) | `/catalogo/<slug>/` → `catalog/product_detail.html` |
| Checkout | `/checkout/…` → `checkout/step_*.html` |
| Diagnóstico / chat | `/assistente/chat/` → `ai/chat.html` |
| Chamados | `/chamados/` → `tickets/list.html` |
| HITL manuais | `/manuais/revisao/` → `manuals/review_queue.html` |
| Dashboard ops | `/dashboard/` → `dashboard/insights.html` |
| Editar produto | `/dashboard/produtos/<id>/` → `dashboard/products_form.html` |

> Protótipos HTML/React antigos (se existirem em rascunhos) **não** são a implementação. Fonte de verdade: templates em `backend/templates/` + inventário acima.

## Fontes

- `plan.md` — Frontend
- `plano-ecommerce-ia-pecas.md` — Frontend (loja)
- `pages/inventory.md` — mapa de telas
- `design/DESIGN.md` — tokens vigentes