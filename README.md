# TechParts AI

E-commerce de peças de reposição com IA (extração de manuais, RAG, catálogo).

**Stack:** Python 3.13+ · Django 6 · htmx · Bootstrap 5.3.8 · PostgreSQL/pgvector · Celery · Redis

## Fase atual

**Fase 2 — Base do projeto** (monólito, Docker, CI, segurança, contas/2FA).

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
make test   # pytest + smoke
make lint   # ruff, black, bandit
make ci     # lint + test + check migrations
pre-commit install  # hooks + commitizen (Conventional Commits)
```

## Apps Django

`accounts`, `catalog`, `products`, `cart`, `checkout`, `orders`, `tickets`, `ai`, `manuals`, `compatibility`, `dashboard`, `notifications`, `core`

## Docs

- [`docs/plano-tarefas.md`](docs/plano-tarefas.md)
- [`design-system/`](design-system/) — Industrial Precision
- [`docs/fase-1-escopo-mvp.md`](docs/fase-1-escopo-mvp.md)
