# Pilar 06 — Avaliação e testes contínuos

> **Parte 1 — Pilares Gerais para Apps de IA** · Fonte-mestre: [`pilares-app-ia-vendas-pecas.md`](../pilares-app-ia-vendas-pecas.md)

## Definição do pilar

Testes com casos reais e extremos; métricas de qualidade; loop de feedback do usuário.

## Qualidade da IA é medida, não presumida

- Feedback do cliente (👍/👎) + **golden set** de casos reais com resultado esperado
- Nenhuma mudança de prompt/lógica de extração sem confirmar que não piorou casos que já funcionavam
- Cobertura mínima obrigatória em checkout, pagamento e extração de IA
- Testes e2e (ex.: Playwright) nos fluxos críticos: checkout, abertura de chamado, chat

## Métricas de qualidade (não só “funciona”)

- Taxa de aprovação humana das extrações
- Taxa de “não encontrei resposta”
- Nota média do feedback 👍/👎
- Taxa de resolução sem intervenção humana
- Tempo médio de resposta

## Ferramentas

- Pytest (+ mocks LLM, testes Celery)
- pytest-cov (meta ex.: 80% em fluxos críticos)
- Golden set de manuais no CI
- Ruff, Black, Mypy, Bandit

## Fontes

- `constitution.md` — Artigos 2.5 e 5
- `plano-ecommerce-ia-pecas.md` — CI/CD, Qualidade de dados, Dashboard
- `plan.md` — Qualidade
