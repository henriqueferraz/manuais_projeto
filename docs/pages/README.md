# Documentação de páginas (telas)

Inventário das telas Django (rota → template → função). Complementa o índice geral em [`../README.md`](../README.md).

| Documento | Uso |
|---|---|
| [`inventory.md`](inventory.md) | Mapa completo de rotas e templates |
| [`dashboard-produto.md`](dashboard-produto.md) | Criar / editar produto (staff), multi-categoria, IA e fotos |
| [`assistente-chat.md`](assistente-chat.md) | Chat RAG / diagnóstico, confiança e contexto de produto |
| [`checkout.md`](checkout.md) | Checkout e Preference Mercado Pago |

## Convenções

- **Público:** storefront sem login (ou sessão anônima).
- **Cliente:** autenticado (2FA quando exigido).
- **Staff:** `is_staff` / permissões de dashboard e HITL.
- Partials HTMX ficam em `backend/templates/**/partials/`.
