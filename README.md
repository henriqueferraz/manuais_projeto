# TechParts AI

E-commerce de peças de reposição com IA (extração de manuais, RAG, catálogo).

**Stack:** Python 3.13+ · Django 6 · htmx · Bootstrap 5.3.8 · PostgreSQL/pgvector · Celery · Redis · LangChain

## Fase atual

**Pós-F8 — backlog.** Fases F0–F8 concluídas. Próximo: beta humana, DoD residual, hardening e integrações live — ver [`docs/plano-tarefas.md`](docs/plano-tarefas.md#pós-f8--o-que-ainda-falta).

Rotas F8: `/assinaturas/` · `/assistencias/` · `/garantia/<uuid>/` · `/canais/whatsapp/webhook/`  
ADRs: [`docs/adr/`](docs/adr/) · Hardening: [`docs/security-hardening.md`](docs/security-hardening.md) · Beta: [`docs/beta-relatorio.md`](docs/beta-relatorio.md)

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
python manage.py seed_scale_catalog
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

`accounts`, `catalog`, `products`, `cart`, `checkout`, `orders`, `tickets`, `ai`, `manuals`, `compatibility`, `dashboard`, `notifications`, `subscriptions`, `partners`, `channels`, `warranty`, `core`

## Docs

- [`docs/plano-tarefas.md`](docs/plano-tarefas.md)
- [`docs/adr/`](docs/adr/) — decisões F8
- [`design-system/`](design-system/) — Industrial Precision
- [`docs/fase-1-escopo-mvp.md`](docs/fase-1-escopo-mvp.md)
