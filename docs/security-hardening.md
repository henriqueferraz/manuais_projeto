# Hardening de segurança pré-escala (F8 / ADR-0003 / T-P.2)

Checklist mínimo antes de tráfego maior. Completar em staging/produção.
Runbook: [`deploy.md`](deploy.md).

## Secrets e configuração

- [x] `SECRET_KEY` forte e único (não default) — validado em `settings.production` / `staging`
- [x] `DEBUG=false` em staging/produção — hardcoded nos settings
- [x] Credenciais só via env / secret manager (nunca no git) — `.env` no `.gitignore`
- [x] `PAYMENT_WEBHOOK_SECRET`, `WHATSAPP_APP_SECRET`, Stripe/MP secrets rotacionáveis — documentados em `.env.example`
- [x] `AI_TOKEN_BUDGET_DAILY` > 0 em produção (custo) — obrigatório em `production.py`; default staging 500k

## Transporte e cookies

- [x] `SECURE_SSL_REDIRECT=true` — produção; staging configurável
- [x] `SESSION_COOKIE_SECURE` / `CSRF_COOKIE_SECURE=true` — staging/produção
- [x] HSTS habilitado no proxy/Nginx — Django `SECURE_HSTS_*` + header condicional em `docker/nginx/nginx.conf`
- [x] `ALLOWED_HOSTS` e `CSRF_TRUSTED_ORIGINS` explícitos — validados ao boot em staging/produção

## Abuso e autenticação

- [x] `AXES_ENABLED=true` — obrigatório em produção; default staging true
- [x] Rate limit IA (`AI_RATE_LIMIT`) adequado ao tráfego — env + `ai_rate_limit`
- [x] Budget diário de tokens + alertas LangSmith/Sentry — `record_token_usage` + `scan_and_emit_alerts` (80%/100%)
- [x] 2FA staff (django-otp) obrigatório para ops — `LOGIN_URL=two_factor:login` + `TWO_FACTOR_PATCH_ADMIN`

## Uploads e webhooks

- [x] ClamAV ou AV em produção para PDFs (`MANUAL_CLAMAV_ENABLED`) — default prod true; serviço Compose `--profile clamav`; dep `clamd`
- [x] Limites `MANUAL_MAX_UPLOAD_BYTES` / `PHOTO_MAX_UPLOAD_BYTES` — em settings
- [x] WhatsApp: verificar token + HMAC; `WHATSAPP_MODE=live` só com BSP homologado (ADR-0002)
- [x] Webhooks de pagamento com assinatura validada — `checkout/payments.py`

## Observabilidade

- [x] Sentry DSN ativo — obrigatório em produção
- [x] Flower / Grafana / alertas Slack ou e-mail ops — `FLOWER_URL`, `OPS_ALERT_EMAILS`, `SLACK_WEBHOOK_URL`
- [x] Logs sem PII (masking structlog) — `apps.core.logging.mask_pii`

## Dados

- [x] Backup Postgres + RPO definido — `scripts/backup_postgres.sh`, RPO ≤ 24h em [`deploy.md`](deploy.md)
- [ ] Avaliar `DATABASE_READ_REPLICA_URL` quando leitura > escrita no catálogo — T-P.5
- [ ] Revisar índices (Product/Order/Ticket) após volume real — T-P.5
