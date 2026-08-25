# Pipeline CI e análise de logs (duas etapas)

**Workflow:** [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml) — job `quality` (Ruff, Black, Bandit, interrogate, pip-audit, Pytest, golden extração+RAG, check migrations).

**Run de referência (sucesso):** Dependabot boto3, 2026-08-18  
https://github.com/henriqueferraz/manuais_projeto/actions/runs/32136093218  
Job `Lint, tests, migrations` — **success** (~1 min 35 s).  
SHA/head do PR Dependabot; o mesmo job roda em `push`/`pull_request` para `main`.

## Etapa 1 — Ruff (lint)

O step `Ruff` executa `ruff check backend`. No run acima concluiu **verde** (exit 0). Falhas históricas no histórico `fix(ci):` (`f86b243`, `1006553`) mostram o padrão: falso positivo Bandit B106 em Preference de pagamento; correção no código, não desligar o gate.

**Leitura com IA:** lint vermelho neste repo costuma ser **formatação/import** ou **nosec pontual**, não falha de domínio. Risco de merge bloqueado é alto e imediato; risco de peça errada no cliente é baixo nessa etapa.

## Etapa 2 — Pytest

Step `Pytest` com `DJANGO_SETTINGS_MODULE=config.settings.test` e `--cov=apps`. No mesmo run: **success**. Inclui testes de diagnóstico, sanitização, low-code (`test_lowcode_*`) e extração.

**Leitura com IA:** pytest verde valida regras determinísticas (HITL, injection, schema). Não substitui o nightly Playwright (outro workflow). Separar “CI de qualidade” de “E2E de UI” evita tratar um gate como o outro.

## Golden

`run_golden_set` e `run_rag_golden_set` com `--min-score 0.66` no mesmo job. São regressões de extração/RAG, não de layout.

## Como reproduzir local

```bash
make lint
make test
make golden
make golden-rag
# ou
make ci
```
