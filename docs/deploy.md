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

```bash
cp .env.example .env.staging
# Editar .env.staging: SECRET_KEY (≥50 chars), ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS,
# SENTRY_DSN (opcional), AI_TOKEN_BUDGET_DAILY>0, AXES_ENABLED=true

docker compose -f docker-compose.yml -f docker-compose.staging.yml --env-file .env.staging up --build -d
docker compose -f docker-compose.yml -f docker-compose.staging.yml exec web python manage.py migrate
docker compose -f docker-compose.yml -f docker-compose.staging.yml exec web python manage.py bootstrap_rbac
docker compose -f docker-compose.yml -f docker-compose.staging.yml exec web python manage.py collectstatic --noinput
```

App: http://localhost:8000 · Nginx: http://localhost:8080 · Flower: http://localhost:5555

ClamAV (perfil opcional):

```bash
docker compose -f docker-compose.yml -f docker-compose.staging.yml --profile clamav up -d
# MANUAL_CLAMAV_ENABLED=true no .env.staging
```

## Produção (Compose + TLS no edge)

1. Provisionar Postgres + Redis gerenciados (ou volumes persistentes).
2. `.env.production` com todos os secrets; `DJANGO_SETTINGS_MODULE=config.settings.production`.
3. TLS no load balancer / Nginx edge; encaminhar `X-Forwarded-Proto: https`.
4. `ALLOWED_HOSTS` e `CSRF_TRUSTED_ORIGINS` = domínio real (`https://…`).
5. `SENTRY_DSN` obrigatório; `AI_TOKEN_BUDGET_DAILY` > 0; `AXES_ENABLED=true`.
6. Staff ops com 2FA (django-otp / two_factor) — `LOGIN_URL=two_factor:login`.
7. `make migrate` / bootstrap / collectstatic no release.

Alternativa host: qualquer PaaS que rode Gunicorn + worker Celery + beat (mesmas env vars).

## Backup Postgres e RPO

| Item | Valor |
|---|---|
| Método | `pg_dump` lógico (`scripts/backup_postgres.sh`) |
| **RPO** | **≤ 24 horas** (cron diário recomendado) |
| Retenção local | 7 dias (script remove dumps mais antigos) |
| Restore | `scripts/restore_postgres.sh <dump.sql.gz>` |

```bash
chmod +x scripts/backup_postgres.sh scripts/restore_postgres.sh
make backup     # com stack Compose no ar
# crontab exemplo (03:00 UTC):
# 0 3 * * * cd /opt/techparts && make backup >> /var/log/techparts-backup.log 2>&1
```

Testar restore em staging ao menos uma vez por trimestre.

## Checklist pré-go-live

Ver [`security-hardening.md`](security-hardening.md). Em staging/prod: `DEBUG=false`, cookies SSL, Axes, budget de tokens, Sentry, backups agendados, secrets fora do git.
