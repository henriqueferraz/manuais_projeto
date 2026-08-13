# Inventário de páginas

Mapa das URLs → template → o que a tela faz.  
Código: `backend/config/urls.py` e apps `*/urls.py`. Templates em `backend/templates/`.

Atualizado em 2026-08-13.

## Storefront (público)

| URL | Name | Template | Função | Auth |
|---|---|---|---|---|
| `/` | `core:home` | `core/home.html` | Home: hero, filtros, atalhos | — |
| `/health/` | `core:health` | JSON | Healthcheck | — |
| `/sw.js` | `core:service_worker` | JS | Service worker PWA | — |
| `/catalogo/` | `catalog:list` | `catalog/product_list.html` (+ `partials/product_grid.html`) | Lista/filtra produtos (categoria FK ou M2M) | — |
| `/catalogo/autocomplete/` | `catalog:autocomplete` | `catalog/partials/autocomplete.html` | Sugestões de busca | — |
| `/catalogo/<slug>/` | `catalog:detail` | `catalog/product_detail.html` | PDP | — |
| `/catalogo/<slug>/manual/` | `catalog:manual_download` | arquivo | Download do PDF | — |
| `/carrinho/` | `cart:detail` | `cart/cart.html` (+ `partials/cart_panel.html`) | Carrinho | sessão |
| `/carrinho/adicionar/` | `cart:add` | toast / redirect | Adicionar item | sessão |
| `/carrinho/atualizar/` | `cart:update` | redirect | Atualizar qty | sessão |
| `/carrinho/remover/` | `cart:remove` | redirect | Remover item | sessão |
| `/carrinho/cupom/` | `cart:apply_coupon` | redirect | Aplicar cupom | sessão |
| `/carrinho/cupom/remover/` | `cart:remove_coupon` | redirect | Remover cupom | sessão |
| `/checkout/` | `checkout:start` | `checkout/step_address.html` | Endereço | sessão |
| `/checkout/frete/` | `checkout:shipping` | `checkout/step_shipping.html` | Frete | sessão |
| `/checkout/pagamento/` | `checkout:payment` | `checkout/step_payment.html` | Pagamento (Pro / Transparente / token) | sessão |
| `/checkout/sucesso/<uuid>/` | `checkout:success` | `checkout/success.html` | Pedido criado | sessão |
| `/assistente/chat/` | `ai:chat` | `ai/chat.html` | Chat / diagnóstico — [`assistente-chat.md`](assistente-chat.md) | sessão |
| `/assistente/foto/` | `ai:photo_upload` | JSON / partial | Busca por foto | sessão |
| `/assistente/foto/<uuid>/` | `ai:photo_status` | partial candidatos | Status da busca | sessão |
| `/compatibilidade/verificar/` | `compatibility:checker` | `compatibility/checker.html` | Verificador peça × modelo | — |
| `/chamados/` | `tickets:list` | `tickets/list.html` | Chamados do usuário | login |
| `/chamados/<code>/` | `tickets:detail` | `tickets/detail.html` | Detalhe | login |
| `/devolucoes/` | `returns:list` | `returns/list.html` | Devoluções | login |
| `/devolucoes/<uuid>/` | `returns:detail` | `returns/detail.html` | Detalhe | login |
| `/assinaturas/` | `subscriptions:plans` | `subscriptions/plans.html` | Planos | — |
| `/assistencias/` | `partners:list` | `partners/list.html` | Rede de assistências | — |
| `/garantia/<uuid>/` | `warranty:claim` | `warranty/claim.html` | Garantia via QR | — |
| `/garantia/<uuid>/qr.png` | `warranty:qr_png` | PNG | Imagem do QR | — |
| `/account/login/` | `two_factor:login` | `two_factor/core/login.html` | Login 2FA | — |
| `/account/logout/` | `logout` | redirect | Logout | login |

Demais rotas `django-two-factor` (setup/profile/QR) usam templates em `two_factor/` + `auth.css`.

## Operação (staff)

| URL | Name | Template | Função |
|---|---|---|---|
| `/dashboard/` | `dashboard:insights` | `dashboard/insights.html` | Insights / KPIs |
| `/dashboard/monitoramento/` | `dashboard:monitoring` | `dashboard/monitoring.html` | Alertas |
| `/dashboard/alertas/<uuid>/ack/` | `dashboard:ack_alert` | redirect | Acknowledge alerta |
| `/dashboard/incidentes/simular/` | `dashboard:simulate_incident` | redirect | Simular incidente |
| `/dashboard/produtos/` | `dashboard:products` | `dashboard/products.html` | Estoque e produtos |
| `/dashboard/produtos/novo/` | `dashboard:products_create` | `dashboard/products_form.html` | Criar — [`dashboard-produto.md`](dashboard-produto.md) |
| `/dashboard/produtos/<id>/` | `dashboard:products_edit` | `dashboard/products_form.html` | Editar (multi-categoria) |
| `/dashboard/produtos/<id>/excluir/` | `dashboard:products_delete` | POST | Excluir |
| `/dashboard/home-hero/` | `dashboard:home_hero` | `dashboard/home_hero.html` | Slides do hero |
| `/dashboard/home-hero/novo/` | `dashboard:home_hero_create` | `dashboard/home_hero_form.html` | Novo slide |
| `/dashboard/home-hero/<id>/` | `dashboard:home_hero_edit` | `dashboard/home_hero_form.html` | Editar slide |
| `/dashboard/home-hero/<id>/toggle/` | `dashboard:home_hero_toggle` | POST | Ativar/desativar |
| `/dashboard/home-hero/<id>/excluir/` | `dashboard:home_hero_delete` | POST | Excluir slide |
| `/manuais/revisao/` | `manuals:review_queue` | `manuals/review_queue.html` | Fila HITL |
| `/manuais/revisao/<id>/` | `manuals:review_detail` | `manuals/review_detail.html` | Revisar extração |
| `/chamados/suporte/` | `tickets:support` | `tickets/support_panel.html` | Painel suporte |
| `/chamados/<code>/status/` | `tickets:update_status` | POST | Atualizar status |
| `/devolucoes/operacao/` | `returns:ops` | `returns/ops_panel.html` | Painel devoluções |
| `/devolucoes/<uuid>/processar/` | `returns:process` | POST | Processar devolução |
| `/compatibilidade/ops/compatibilidades/` | `compatibility:ops_compat` | `compatibility/ops_compat.html` | Cadastro compat |
| `/compatibilidade/ops/produtos/` | legado | → dashboard produtos | Alias |

## APIs / webhooks (sem página HTML)

| URL | Uso |
|---|---|
| `/assistente/chat/stream/` | SSE do chat |
| `/assistente/chat/feedback/` | 👍/👎 |
| `/checkout/api/frete/` | Cotação de frete |
| `/checkout/webhooks/pagamento/` | Webhook pagamento (Stripe/mock assinatura; MP IPN) |
| `/canais/whatsapp/webhook/` | WhatsApp |
| `/dashboard/produtos/ia/extrair-manual/` | Extração IA (JSON) |
| `/dashboard/produtos/ia/extrair-manual/<id>/descartar/` | Descartar extração |
| `/dashboard/produtos/ia/buscar-fotos/` | Busca fotos web (JSON) |
| `/admin/` | Django Admin |

## Partials e includes compartilhados

| Path | Uso |
|---|---|
| `base.html`, `includes/header.html`, `includes/footer.html` | Shell da loja |
| `checkout/partials/steps.html` | Stepper do checkout |
| `ai/partials/diagnostic_card.html` | Card de diagnóstico |
| `ai/partials/photo_candidates.html` | Candidatos da busca por foto |
| `two_factor/_base*.html`, `_wizard_*.html` | Layout do login 2FA |

## Fonte de verdade

Implementação = templates em `backend/templates/` + este inventário. Protótipos HTML/React antigos não são a UI vigente.
