# Pilar 23 — Design da experiência de busca e filtros

> **Parte 3 — Experiência Visual e Qualidade de Design** · Fonte-mestre: [`pilares-app-ia-vendas-pecas.md`](../pilares-app-ia-vendas-pecas.md)

## Definição do pilar

Filtros técnicos claros; autocomplete visual; diferencial “busca por sintoma”.

## Requisitos

- Filtros técnicos: compatibilidade, modelo, voltagem, **categoria**
- Autocomplete/sugestões com miniatura do produto
- **Busca por sintoma** (diferencial): “minha geladeira não gela” → IA sugere peças
- Verificador de compatibilidade com badge visual (“COMPATIBILIDADE GARANTIDA”)
- Busca full-text Postgres no início; upgrade opcional depois

## Categoria no filtro (código vigente)

`filter_catalog(?category=)` em `apps.catalog.services` casa:

- `Product.category` (FK principal), **ou**
- `Product.categories` (M2M)

Um produto em *Peça de reposição* e *Móveis* aparece nos dois filtros.  
Detalhe do cadastro: [`../pages/dashboard-produto.md`](../pages/dashboard-produto.md).

## UI vigente

- `/catalogo/` → `catalog/product_list.html` (+ `partials/product_grid.html` HTMX)
- `/` → filtros na home (`core/home.html`)
- Inventário: [`../pages/inventory.md`](../pages/inventory.md)

## Fontes

- `pilares-app-ia-vendas-pecas.md` — Pilar 23
- `specify.md` — §§4.1–4.2
- `techparts_ai_project_brief.md` — AI-Powered Search (histórico)
