#!/bin/bash
set -euo pipefail

echo "Waiting for database..."
python - <<'PY'
import os, time
import psycopg

url = os.environ.get("DATABASE_URL", "")
if url.startswith("postgres"):
    # psycopg connection from URL
    for i in range(30):
        try:
            with psycopg.connect(url) as conn:
                conn.execute("SELECT 1")
            print("Database ready")
            break
        except Exception as exc:
            print(f"DB not ready ({exc}); retry {i+1}/30")
            time.sleep(2)
    else:
        raise SystemExit("Database unavailable")
else:
    print("Non-postgres DATABASE_URL; skip wait")
PY

python manage.py migrate --noinput
python manage.py bootstrap_rbac
exec "$@"
