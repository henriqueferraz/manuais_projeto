# ADR 0003 — Hardening de segurança pré-escala

- **Status:** Aceito
- **Data:** 2026-08-06
- **Pilares:** P05, P15

## Contexto

Antes de tráfego maior: rate limits, budget de tokens, checklist de produção.

## Decisão

1. Introduzir `AI_TOKEN_BUDGET_DAILY` e `AI_TOKEN_BUDGET_PER_REQUEST` (guardrails além do rate limit).
2. Checklist `docs/security-hardening.md` (secrets, HSTS, Axes, webhooks, uploads).
3. Manter CSP/Axes/SSL já existentes; documentar valores mínimos de produção.
4. WhatsApp/warranty webhooks só com secret em produção.

## Consequências

+ Limites explícitos de custo/abuso.  
− Budget diário requer Redis/cache consistente entre workers.

## Atualização T-P.2 (2026-08-07)

- `settings.production` / `staging` validam `SECRET_KEY`, `ALLOWED_HOSTS`, CSRF, Axes e budget.
- Checklist [`security-hardening.md`](../security-hardening.md) marcado; runbook [`deploy.md`](../deploy.md).
- Backup `scripts/backup_postgres.sh` com RPO ≤ 24h; ClamAV via Compose profile + `clamd`.
- Alertas ops em 80%/100% do budget diário de tokens.
