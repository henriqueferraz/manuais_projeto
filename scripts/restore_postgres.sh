#!/usr/bin/env bash
# Restore de dump gerado por backup_postgres.sh (T-P.2).
# Uso: ./scripts/restore_postgres.sh backups/techparts-YYYYMMDDTHHMMSSZ.sql.gz
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DUMP="${1:-}"

if [[ -z "$DUMP" || ! -f "$DUMP" ]]; then
  echo "Uso: $0 <arquivo.sql.gz>" >&2
  exit 1
fi

echo "ATENÇÃO: isto substitui o banco techparts. Ctrl+C em 5s para abortar."
sleep 5

if docker compose -f "$ROOT/docker-compose.yml" ps db --status running 2>/dev/null | grep -q db; then
  gunzip -c "$DUMP" | docker compose -f "$ROOT/docker-compose.yml" exec -T db \
    psql -U techparts -d techparts
  echo "Restore OK a partir de $DUMP"
  exit 0
fi

if [[ -n "${DATABASE_URL:-}" ]]; then
  gunzip -c "$DUMP" | psql "$DATABASE_URL"
  echo "Restore OK a partir de $DUMP"
  exit 0
fi

echo "Nenhum Postgres disponível." >&2
exit 1
