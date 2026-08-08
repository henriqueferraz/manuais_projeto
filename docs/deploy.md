# Deploy, staging e backup — TechParts AI (T-P.2)

Runbook mínimo para subir staging/produção com Compose e cumprir o checklist de [`security-hardening.md`](security-hardening.md).

## Ambientes

| Ambiente | Settings | DEBUG | SSL cookies | HSTS |
|---|---|---|---|---|
| Local | `config.settings.local` | true | false | off |
| Staging | `config.settings.staging` | **false** | true | 1h |
| Produção | `config.settings.production` | **false** | true | 1 ano + preload |

Secrets **nunca** no git — só `.env` / secret manager.  
Template de variáveis: [`.env.example`](../.env.example) na **raiz** do repositório (fonte única).

## Staging com Compose

Pré-requisitos locais:

1. Usuário no grupo `docker` (`sudo usermod -aG docker $USER` + re-login) **ou** `sudo docker …`.
2. Arquivo `.env.staging` na raiz (não versionado). Pode partir de `.env` / `.env.example`.
   - **Banco:** use o mesmo `DATABASE_URL` Neon do `.env` (Compose **não** sobrescreve em staging).
   - Postgres Docker só se precisar: `--profile local-db` (e aí aponte `DATABASE_URL` para `postgres://techparts:techparts@db:5432/techparts`).
3. Para o critério specify 5 (venda BR): `PAYMENT_PROVIDER=stripe|mercadopago` + chave sandbox **e** `NFE_PROVIDER=notaas` + `API_KEY_NOTAAS` (ou Focus, se aplicável).
4. Portas do overlay (`docker-compose.staging.yml`): web **8001**, nginx **8081**, flower **5556**, redis host **6380**. `CSRF_TRUSTED_ORIGINS` no Compose já aponta para 8001/8081 — se mudar `WEB_PUBLISH_PORT` / `NGINX_PUBLISH_PORT`, alinhe CSRF.

```bash
cp .env.example .env.staging
# Editar .env.staging: SECRET_KEY (≥50 chars), ALLOWED_HOSTS (incluir web/nginx/staging.local),
# CSRF_TRUSTED_ORIGINS (8001/8081), AI_TOKEN_BUDGET_DAILY>0, AXES_ENABLED=true,
# SECURE_SSL_REDIRECT=false se HTTP local sem TLS no edge,
# DATABASE_URL=postgres://…@….neon.tech/…?sslmode=require,
# + secrets de pagamento/NF-e quando disponíveis.

make up-staging
# equivalente:
# docker compose -f docker-compose.yml -f docker-compose.staging.yml --env-file .env.staging up --build -d

STAGING="docker compose -f docker-compose.yml -f docker-compose.staging.yml --env-file .env.staging"
$STAGING exec web python manage.py migrate
$STAGING exec web python manage.py bootstrap_rbac
$STAGING exec web python manage.py collectstatic --noinput
$STAGING exec web python manage.py smoke_live_integrations
```

| Serviço | URL / porta |
|---|---|
| App (gunicorn) | http://localhost:8001 |
| Nginx | http://localhost:8081 |
| Flower | http://localhost:5556 |
| Redis (host) | `localhost:6380` |
| ClamAV (perfil) | `localhost:3310` |

Banco padrão = **Neon** via `DATABASE_URL`. Flower usa `config.settings.local` de propósito (só precisa do broker Celery).

ClamAV (perfil opcional):

```bash
docker compose -f docker-compose.yml -f docker-compose.staging.yml --env-file .env.staging --profile clamav up -d
# MANUAL_CLAMAV_ENABLED=true no .env.staging
```

> Nota: `settings.staging` defaulta ClamAV ligado; o overlay Compose sobrescreve com `MANUAL_CLAMAV_ENABLED=false` até o perfil `clamav` estar no ar.

## Produção (Compose + TLS no edge)

1. Provisionar Postgres + Redis gerenciados (ou volumes persistentes).
2. `.env.production` com todos os secrets; `DJANGO_SETTINGS_MODULE=config.settings.production`.
3. TLS no load balancer / Nginx edge; encaminhar `X-Forwarded-Proto: https`.
4. `ALLOWED_HOSTS` e `CSRF_TRUSTED_ORIGINS` = domínio real (`https://…`).
5. `SENTRY_DSN` obrigatório; `AI_TOKEN_BUDGET_DAILY` > 0; `AXES_ENABLED=true`.
6. Staff ops com 2FA (django-otp / two_factor) — `LOGIN_URL=two_factor:login`.
7. No release, rode migrate/bootstrap/collectstatic **no mesmo projeto Compose** do ambiente (não use o `make migrate` do stack local sem o overlay/env corretos):

```bash
# Exemplo com overlay staging; em produção use o mesmo padrão com --env-file .env.production
# e DJANGO_SETTINGS_MODULE=config.settings.production no serviço web.
COMPOSE="docker compose -f docker-compose.yml -f docker-compose.staging.yml --env-file .env.staging"
$COMPOSE exec web python manage.py migrate
$COMPOSE exec web python manage.py bootstrap_rbac
$COMPOSE exec web python manage.py collectstatic --noinput
```

Não há `docker-compose.production.yml` versionado ainda — produção pode reutilizar o overlay staging com `.env.production` + `config.settings.production`, ou um overlay próprio no host.

Alternativa host: qualquer PaaS que rode Gunicorn + worker Celery + beat (mesmas env vars). Este repositório documenta **Compose**; não há runbook Vercel para o monólito Django.

## Backup Postgres e RPO

| Item | Valor |
|---|---|
| Método | `pg_dump` lógico (`scripts/backup_postgres.sh`) |
| **RPO** | **≤ 24 horas** (cron diário recomendado) |
| Retenção local | 7 dias (script remove dumps mais antigos) |
| Restore | `scripts/restore_postgres.sh <dump.sql.gz>` |

```bash
chmod +x scripts/backup_postgres.sh scripts/restore_postgres.sh
make backup     # com stack Compose no ar (serviço db) OU DATABASE_URL exportada no host
# crontab exemplo (03:00 UTC):
# 0 3 * * * cd /opt/techparts && make backup >> /var/log/techparts-backup.log 2>&1
```

Com Neon (sem `--profile local-db`), exporte `DATABASE_URL` no shell antes do `make backup`, ou o script não encontra o Postgres.

Testar restore em staging ao menos uma vez por trimestre.

## Checklist pré-go-live

Ver [`security-hardening.md`](security-hardening.md). Em staging/prod: `DEBUG=false`, cookies SSL, Axes, budget de tokens, Sentry, backups agendados, secrets fora do git.
