#!/usr/bin/env bash
# Backup lógico do Postgres (T-P.2).
# RPO alvo documentado: ≤ 24h (cron diário) — ver docs/deploy.md.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT_DIR="${BACKUP_DIR:-$ROOT/backups}"
mkdir -p "$OUT_DIR"

# Prefer Compose service; fallback DATABASE_URL local
if docker compose -f "$ROOT/docker-compose.yml" ps db --status running 2>/dev/null | grep -q db; then
  FILE="$OUT_DIR/techparts-${STAMP}.sql.gz"
  docker compose -f "$ROOT/docker-compose.yml" exec -T db \
    pg_dump -U techparts -d techparts --no-owner --no-acl \
    | gzip -c > "$FILE"
  echo "Backup OK: $FILE"
  # Retenção padrão: 7 dias
  find "$OUT_DIR" -name 'techparts-*.sql.gz' -mtime +7 -delete 2>/dev/null || true
  exit 0
fi

if [[ -n "${DATABASE_URL:-}" ]]; then
  FILE="$OUT_DIR/techparts-${STAMP}.sql.gz"
  # shellcheck disable=SC2086
  pg_dump "$DATABASE_URL" --no-owner --no-acl | gzip -c > "$FILE"
  echo "Backup OK: $FILE"
  exit 0
fi

echo "Nenhum Postgres disponível (Compose db parado e DATABASE_URL vazio)." >&2
exit 1
