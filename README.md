# TechParts AI

E-commerce de peças de reposição com IA (extração de manuais, RAG, catálogo).

**Stack:** Python 3.13+ · Django 6 · htmx · Bootstrap 5.3.8 · PostgreSQL/pgvector · Celery · Redis · LangChain

## Fase atual

**Pós-F8 — backlog concluído em código** (T-P.1–T-P.6). Ver [`docs/plano-tarefas.md`](docs/plano-tarefas.md#pós-f8--o-que-ainda-falta).

Rotas F8: `/assinaturas/` · `/assistencias/` · `/garantia/<uuid>/` · `/canais/whatsapp/webhook/`  
ADRs: [`docs/adr/`](docs/adr/) · Hardening: [`docs/security-hardening.md`](docs/security-hardening.md) · Deploy: [`docs/deploy.md`](docs/deploy.md) · Beta: [`docs/beta-script.md`](docs/beta-script.md)

## Bootstrap rápido (local sem Docker)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements/local.txt
cp .env.example .env
cd backend
python manage.py migrate
python manage.py bootstrap_rbac
python manage.py createsuperuser   # opcional se for usar seed_beta
python manage.py seed_beta         # T-P.1: staff/tester + VTE-02/CAP-35 + RAG
python manage.py seed_scale_catalog  # opcional: catálogo amplo (F8)
python manage.py runserver
```

Abra http://127.0.0.1:8000/ — shell Industrial Precision da F0.  
Beta: staff `beta.staff@techparts.local` / tester `beta.tester@techparts.local` (senha `beta-local-only`) — ver [`docs/beta-script.md`](docs/beta-script.md).  
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

### Staging / produção / backup (T-P.2)

```bash
cp .env.example .env.staging   # SECRET_KEY forte, ALLOWED_HOSTS, budget > 0
make up-staging                # overlay DEBUG=false
make backup                    # pg_dump → backups/ (RPO ≤ 24h)
# make restore FILE=backups/techparts-....sql.gz
```

Detalhes: [`docs/deploy.md`](docs/deploy.md) · checklist: [`docs/security-hardening.md`](docs/security-hardening.md).

## Integrações live (T-P.4)

CI permanece em mock. Em staging, ative provedores via `.env` (ver `.env.example`) e rode:

```bash
cd backend && python manage.py smoke_live_integrations
```

ADRs: pagamento [`0011`](docs/adr/0011-pagamento-sandbox.md) · NF-e [`0009`](docs/adr/0009-nfe-focusnfe.md) · frete [`0010`](docs/adr/0010-melhor-envio-live.md) · WhatsApp [`0002`](docs/adr/0002-whatsapp-rag.md) · assinatura [`0004`](docs/adr/0004-assinatura-manutencao.md).

## Qualidade

```bash
make test    # pytest
make e2e     # Playwright chromium (T-P.6)
make golden  # regressão golden set de extração
make lint    # ruff, black, bandit
make ci      # lint + test + golden + check migrations
pre-commit install
```

### E2E Playwright (T-P.6)

```bash
pip install -r requirements/e2e.txt
playwright install chromium
make e2e
```

Specs em `e2e/` (checkout mock, chamado, chat). Gate CI: nightly + PRs que tocam `e2e/**` — [`.github/workflows/e2e-nightly.yml`](.github/workflows/e2e-nightly.yml).

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
