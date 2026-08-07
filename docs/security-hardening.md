# Hardening de segurança pré-escala (F8 / ADR-0003)

Checklist mínimo antes de tráfego maior. Completar em staging/produção.

## Secrets e configuração

- [ ] `SECRET_KEY` forte e único (não default)
- [ ] `DEBUG=false` em staging/produção
- [ ] Credenciais só via env / secret manager (nunca no git)
- [ ] `PAYMENT_WEBHOOK_SECRET`, `WHATSAPP_APP_SECRET`, Stripe/MP secrets rotacionáveis
- [ ] `AI_TOKEN_BUDGET_DAILY` > 0 em produção (custo)

## Transporte e cookies

- [ ] `SECURE_SSL_REDIRECT=true`
- [ ] `SESSION_COOKIE_SECURE` / `CSRF_COOKIE_SECURE=true`
- [ ] HSTS habilitado no proxy/Nginx
- [ ] `ALLOWED_HOSTS` e `CSRF_TRUSTED_ORIGINS` explícitos

## Abuso e autenticação

- [ ] `AXES_ENABLED=true`
- [ ] Rate limit IA (`AI_RATE_LIMIT`) adequado ao tráfego
- [ ] Budget diário de tokens + alertas LangSmith/Sentry
- [ ] 2FA staff (django-otp) obrigatório para ops

## Uploads e webhooks

- [ ] ClamAV ou AV em produção para PDFs (`MANUAL_CLAMAV_ENABLED`)
- [ ] Limites `MANUAL_MAX_UPLOAD_BYTES` / `PHOTO_MAX_UPLOAD_BYTES`
- [ ] WhatsApp: verificar token + HMAC; `WHATSAPP_MODE=live` só com BSP homologado
- [ ] Webhooks de pagamento com assinatura validada

## Observabilidade

- [ ] Sentry DSN ativo
- [ ] Flower / Grafana / alertas Slack ou e-mail ops
- [ ] Logs sem PII (masking structlog)

## Dados

- [ ] Backup Postgres + RPO definido
- [ ] Avaliar `DATABASE_READ_REPLICA_URL` quando leitura > escrita no catálogo
- [ ] Revisar índices (Product/Order/Ticket) após volume real
