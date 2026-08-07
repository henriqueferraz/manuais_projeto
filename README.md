# TechParts AI

E-commerce de peças de reposição com IA (extração de manuais, RAG, catálogo).

**Stack:** Python 3.13+ · Django 6 · htmx · Bootstrap 5.3.8 · PostgreSQL/pgvector · Celery · Redis · LangChain

## Fase atual

**Fase 7 — Beta, dashboard e monitoramento.** Insights + painel de ops + script de beta.

Rotas staff: `/dashboard/` · `/dashboard/monitoramento/`

## Bootstrap rápido (local sem Docker)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements/local.txt
cp .env.example .env
cd backend
python manage.py migrate
python manage.py bootstrap_rbac
python manage.py createsuperuser
python manage.py runserver
```

Abra http://127.0.0.1:8000/ — shell Industrial Precision da F0.  
Fila de revisão (staff): http://127.0.0.1:8000/manuais/revisao/

## Docker (`make up`)

```bash
cp .env.example .env
make up
```

| Serviço | URL |
|---|---|
| App (gunicorn) | http://localhost:8000 |
| Nginx | http://localhost:8080 |
| Flower | http://localhost:5555 |
| Postgres | localhost:5432 |
| Redis | localhost:6379 |

## Qualidade

```bash
make test    # pytest
make golden  # regressão golden set de extração
make lint    # ruff, black, bandit
make ci      # lint + test + check migrations
pre-commit install
```

## Extração (F3)

- `EXTRACTION_LLM_MODE=mock` (default CI/local) ou `anthropic`
- R2: `USE_R2_STORAGE=true` + credenciais AWS/R2 no `.env`
- Prompt versionado: `backend/apps/manuals/prompts/extraction_v1.md`

## Apps Django

`accounts`, `catalog`, `products`, `cart`, `checkout`, `orders`, `tickets`, `ai`, `manuals`, `compatibility`, `dashboard`, `notifications`, `core`

## Docs

- [`docs/plano-tarefas.md`](docs/plano-tarefas.md)
- [`design-system/`](design-system/) — Industrial Precision
- [`docs/fase-1-escopo-mvp.md`](docs/fase-1-escopo-mvp.md)
