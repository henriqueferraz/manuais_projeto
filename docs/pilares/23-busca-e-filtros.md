# Pilar 23 — Design da experiência de busca e filtros

> **Parte 3 — Experiência Visual e Qualidade de Design** · Fonte-mestre: [`pilares-app-ia-vendas-pecas.md`](../pilares-app-ia-vendas-pecas.md)

## Definição do pilar

Filtros técnicos claros; autocomplete visual; diferencial “busca por sintoma”.

## Requisitos

- Filtros técnicos: compatibilidade, modelo, voltagem, categoria
- Autocomplete/sugestões com miniatura do produto
- **Busca por sintoma** (diferencial): “minha geladeira não gela” → IA sugere peças
- Verificador de compatibilidade com badge visual (“COMPATIBILIDADE GARANTIDA”)
- Busca full-text Postgres no início; upgrade opcional depois

## UI de referência

- `code (cópia 3|4|10).html` — catálogo / hero / “Dúvidas sobre compatibilidade?”
- `src/components/CatalogView.tsx`, `HeroSection.tsx`
- Badge de compatibilidade em `Product` (`src/types.ts`)

## Fontes

- `pilares-app-ia-vendas-pecas.md` — Pilar 23
- `specify.md` — §§4.1–4.2
- `techparts_ai_project_brief.md` — AI-Powered Search, Compatibility Badge
