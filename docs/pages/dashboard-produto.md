# Dashboard — criar / editar produto

| | |
|---|---|
| **URLs** | `/dashboard/produtos/novo/` · `/dashboard/produtos/<id>/` |
| **Names** | `dashboard:products_create` · `dashboard:products_edit` |
| **Template** | `backend/templates/dashboard/products_form.html` |
| **Form** | `apps.products.forms.InternalProductForm` |
| **View** | `apps.dashboard.views.products_edit` |
| **Auth** | staff |

## Objetivo

Cadastro interno de produto (SKU, marca, modelo, preço, estoque, specs, imagens) com assistência de IA (manual PDF) e fotos da web. Alimenta o catálogo público após publicação.

## Categorias (múltiplas)

O campo **Categorias** é multi-seleção (checkboxes), não um select único.

| Modelo | Papel |
|---|---|
| `Product.categories` (M2M) | Todas as categorias do item (ex.: *Peça de reposição* + *Móveis*) |
| `Product.category` (FK) | Categoria **principal** — primeira da lista marcada (ordem alfabética do queryset). Usada por IA/RAG, cupons legados e histórico |

### Comportamento ao salvar

1. `product.categories.set(selecionadas)`
2. `product.category = selecionadas[0]` (ou `None` se vazio)

### Catálogo e promoções

- Filtro `?category=` em `/catalogo/` encontra o produto se a categoria estiver na FK **ou** no M2M.
- Promoções por categoria (`ProductPromotion.category`) também batem em `product.categories`.

### UI / JS

- Checkboxes em `.tp-category-checks` (estilo em `design-system/components.css`).
- Assistente IA (`product_ai_assist.js`): ao sugerir categoria, marca o checkbox correspondente (`name="categories"`).
- Busca de fotos web (`product_web_images.js`): usa a primeira categoria marcada.

## Outras seções do formulário

| Seção | Notas |
|---|---|
| Identificação | SKU (normalizado), marca (`brand_ref`), modelo (`equipment_model`) |
| Comercial | Preço, voltagem, tipo (`finished_good` / `spare_part`), status |
| Specs | Potência, peso, dimensões, material, etc. — regra de ouro em [`../regra-ouro-campos-produto.md`](../regra-ouro-campos-produto.md) |
| Estoque | Disponível + alerta mínimo |
| Galeria | Até N fotos; upload local e/ou URLs da busca web |
| IA | Upload de PDF → extração → aplicar sugestões (HITL) |

## Lista e exclusão

| URL | Template | Função |
|---|---|---|
| `/dashboard/produtos/` | `dashboard/products.html` | Listagem / filtros ops |
| `/dashboard/produtos/<id>/excluir/` | POST | Exclui o produto |

Alias legado: `/compatibilidade/ops/produtos/` aponta para as mesmas views do dashboard.
