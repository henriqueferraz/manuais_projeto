# Pilar 19 — Estados de interface (loading, vazio, erro)

> **Parte 3 — Experiência Visual e Qualidade de Design** · Fonte-mestre: [`pilares-app-ia-vendas-pecas.md`](../pilares-app-ia-vendas-pecas.md)

## Definição do pilar

Skeleton screens; empty states; erros amigáveis com recuperação — inclusive no chat.

## Requisitos

- **Loading:** skeleton em vez de spinner genérico; no chat, indicador “IA pensando”
- **Vazio:** ex.: “nenhum produto encontrado” + sugestão de busca / diagnóstico
- **Erro:** mensagem amigável + ação clara (tentar de novo, abrir chamado)
- Status badges com baixa saturação (“In Stock”, “Draft”, “SLA Breached”)

## No domínio de IA

Quando a IA falha ou não sabe: fallback explícito + caminho para humano (nunca deixar o usuário sem próximo passo).

## Fontes

- `pilares-app-ia-vendas-pecas.md` — Pilar 19
- `constitution.md` — Artigo 2.6
- `DESIGN.md` — Status Badges
