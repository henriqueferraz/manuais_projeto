# Pilar 14 — CI/CD

> **Parte 2 — Pilares Específicos do Projeto** · Fonte-mestre: [`pilares-app-ia-vendas-pecas.md`](../pilares-app-ia-vendas-pecas.md)

## Definição do pilar

Testes de prompts/grafos; migrations + pgvector; ambientes staging/prod isolados.

## Pipeline (GitHub Actions)

Em cada push/PR:

1. Lint (ruff + black check)
2. Tipos (mypy, se adotado)
3. Testes (pytest + mocks OpenAI / `*_LLM_MODE=mock` + golden set de manuais)
4. Migrations pendentes do Django
5. SAST (bandit), pip-audit/Dependabot
6. Cobertura mínima nos fluxos críticos

## Qualidade de processo

- Conventional Commits (commitlint)
- Pre-commit: black, ruff, detect-secrets
- Migrations como etapa explícita do deploy (não no boot)
- Plano de rollback documentado antes de migration em produção
- Staging com projeto LangSmith próprio, isolado da produção
- Docker: Django, Postgres, Redis, Celery Worker/Beat, Flower, Nginx
- ADRs para decisões relevantes

## Fontes

- `constitution.md` — Artigo 5
- `plano-ecommerce-ia-pecas.md` — CI/CD
- `plan.md` — CI/CD, Docker, Qualidade
