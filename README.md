# TechParts AI

E-commerce de peças de reposição com IA: extração de manuais, catálogo, checkout, chamados, chat RAG e diagnóstico.

**Stack:** Python 3.13+ · Django 6 · htmx · Bootstrap · PostgreSQL/pgvector · Celery · Redis · LangChain/LangGraph

**Status:** fases F0–F8 e backlog pós-F8 (T-P.1–T-P.6) entregues em código. Detalhe: [`docs/plano-tarefas.md`](docs/plano-tarefas.md).

---

## Primeiros passos

### 1. Pré-requisitos

- Python **3.13+**
- `git`
- Opcional para stack completa: **Docker** + Docker Compose (Postgres, Redis, worker, Nginx)

### 2. Clonar e criar o ambiente

```bash
git clone <url-do-repo> manuais
cd manuais
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements/local.txt
```

### 3. Configurar variáveis de ambiente

A **única** fonte de exemplo é o arquivo na raiz:

```bash
cp .env.example .env
```

Para o primeiro start local, o `.env` já vem pronto (mock de IA/pagamento, SQLite, Axes desligado). Ajuste só se precisar:

| Variável | Local (default) | Quando mudar |
| --- | --- | --- |
| `SECRET_KEY` | valor de dev | Staging/prod: gere uma chave forte (≥50 chars) |
| `DEBUG` | `true` | Staging/prod: `false` |
| `DATABASE_URL` | (vazio → SQLite) | Postgres local ou Compose |
| `CELERY_TASK_ALWAYS_EAGER` | `true` | `false` com Redis + worker |
| `*_LLM_MODE` / `EMBEDDING_MODE` | `mock` | `openai` + `OPENAI_API_KEY` |
| `PAYMENT_PROVIDER` | `mock` | `stripe` / `mercadopago` em sandbox |
| `AI_TOKEN_BUDGET_DAILY` | `0` (off) | Staging/prod: valor > 0 |

Lista completa e comentada: [`.env.example`](.env.example). Índice dos docs: [`docs/README.md`](docs/README.md).

### 4. Subir o app (sem Docker)

```bash
cd backend
python3 manage.py migrate
python3 manage.py bootstrap_rbac
python3 manage.py seed_beta          # staff/tester + produtos demo + RAG
# python manage.py createsuperuser  # opcional
python3 manage.py runserver
# ou na raiz: make runserver
```

Abra **<http://127.0.0.1:8000/>**

| Conta demo (`seed_beta`) | Senha |
| --- | --- |
| `beta.staff@techparts.local` | `beta-local-only` |
| `beta.tester@techparts.local` | `beta-local-only` |

Rotas úteis no primeiro uso:

| URL | O quê |
| --- | --- |
| `/` | Home |
| `/catalogo/` | Catálogo |
| `/assistente/chat/` | Chat / diagnóstico |
| `/checkout/` | Checkout (carrinho com itens) |
| `/chamados/` | Chamados técnicos |
| `/manuais/revisao/` | Fila HITL (staff) |
| `/dashboard/` | Insights ops (staff) |
| `/health/` | Healthcheck |

### 5. Alternativa: Docker Compose

```bash
cp .env.example .env
make up
```

| Serviço | URL |
| --- | --- |
| App (gunicorn) | <http://localhost:8000> |
| Nginx | <http://localhost:8080> |
| Flower | <http://localhost:5555> |
| Postgres | `localhost:5432` |
| Redis | `localhost:6379` |

Depois do `make up`:

```bash
make migrate
make bootstrap
docker compose exec web python manage.py seed_beta
```

---

## Primeiras configurações (opcional)

### Dados extras

```bash
cd backend
python3 manage.py seed_scale_catalog   # catálogo amplo + traduções EN/ES
python3 manage.py smoke_live_integrations   # confere modos/credenciais (sem cobrança)
```

### Ativar IA de verdade (fora do CI)

No `.env`:

```bash
OPENAI_API_KEY=sk-...
OPENAI_CHAT_MODEL=gpt-4o-mini
CHAT_LLM_MODE=openai
EXTRACTION_LLM_MODE=openai
DIAGNOSIS_LLM_MODE=openai
PHOTO_LLM_MODE=openai
EMBEDDING_MODE=openai
EMBEDDING_DIMS=1536          # alinhar ao modelo (ex.: text-embedding-3-small)
```

Reinicie o `runserver` / containers.

### Cloudflare R2 (manuais, fotos, produtos e branding)

Com `USE_R2_STORAGE=true`, **todo** `FileField`/`ImageField` (manuais, fotos de diagnóstico, imagens de produto) e os assets da home (`branding/home-*.jpg`) usam o bucket R2 — não há cópia em `backend/media/` nem `backend/static/img/`.

Para reenviar arquivos locais (se existirem) para o bucket:

```bash
cd backend && python manage.py sync_media_to_r2
```

No `.env` (token em **R2 → Manage R2 API Tokens**):

```bash
USE_R2_STORAGE=true
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET_NAME=projeto-manuais
R2_ENDPOINT_URL=https://<ACCOUNT_ID>.r2.cloudflarestorage.com
R2_REGION_NAME=auto
```

O `R2_ENDPOINT_URL` deve ser **só o host** (sem `/nome-do-bucket`). Em local, o settings respeita R2 quando a flag está ligada.

### Pagamento / frete / NF-e (sandbox)

Ver [`.env.example`](.env.example) seção checkout e ADRs:

- Pagamento: [`docs/adr/0011-pagamento-sandbox.md`](docs/adr/0011-pagamento-sandbox.md)
- NF-e: [`docs/adr/0009-nfe-focusnfe.md`](docs/adr/0009-nfe-focusnfe.md)
- Frete: [`docs/adr/0010-melhor-envio-live.md`](docs/adr/0010-melhor-envio-live.md)

CI e local continuam em **mock** por padrão.

### Staging / produção / backup

```bash
cp .env.example .env.staging
# SECRET_KEY forte, ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS (portas 8001/8081),
# AI_TOKEN_BUDGET_DAILY>0, AXES_ENABLED=true, DATABASE_URL (Neon ou Compose)
make up-staging
# App http://localhost:8001 · Nginx http://localhost:8081 · Flower http://localhost:5556
make backup   # precisa de Postgres Compose (--profile local-db) ou DATABASE_URL exportada no host
```

Runbook: [`docs/deploy.md`](docs/deploy.md) · checklist: [`docs/security-hardening.md`](docs/security-hardening.md).

---

## Qualidade

```bash
make test     # pytest
make lint     # ruff + black + bandit
make golden   # golden set extração
make golden-rag  # golden set RAG
make ci       # lint + test + golden + golden-rag + check migrations
```

E2E (Playwright):

```bash
pip install -r requirements/e2e.txt
playwright install chromium
make e2e
```

---

## Mapa da documentação

| Doc | Para quê |
| --- | --- |
| [`docs/README.md`](docs/README.md) | Índice (canônico × obsoleto) |
| [`docs/plano-tarefas.md`](docs/plano-tarefas.md) | Fases e aceite |
| [`docs/adr/`](docs/adr/) | Decisões de arquitetura |
| [`docs/deploy.md`](docs/deploy.md) | Deploy / backup |
| [`docs/beta-script.md`](docs/beta-script.md) | Roteiro beta |
| [`design-system/`](design-system/) | Design system Industrial Precision |
| [`docs/design/DESIGN.md`](docs/design/DESIGN.md) | Tokens (fonte de verdade) |

**Não use** `docs/design/design.md` (rascunho obsoleto) nem um segundo `.env.example` em `docs/` (removido).

## Apps Django

`accounts`, `catalog`, `products`, `cart`, `checkout`, `orders`, `tickets`, `ai`, `manuals`, `compatibility`, `dashboard`, `notifications`, `subscriptions`, `partners`, `channels`, `warranty`, `core`
