#!/usr/bin/env bash
set -e

echo "[entrypoint] waiting for MySQL at ${MYSQL_HOST}:${MYSQL_PORT}..."
python - <<'PY'
import os, socket, time
host = os.environ.get("MYSQL_HOST", "mysql")
port = int(os.environ.get("MYSQL_PORT", "3306"))
for i in range(60):
    try:
        with socket.create_connection((host, port), timeout=2):
            print("[entrypoint] MySQL is reachable")
            break
    except OSError:
        time.sleep(2)
else:
    raise SystemExit("[entrypoint] MySQL never came up")
PY

echo "[entrypoint] makemigrations + migrate"
python manage.py makemigrations --noinput || true
python manage.py migrate --noinput

echo "[entrypoint] collectstatic"
python manage.py collectstatic --noinput || true

echo "[entrypoint] launching: $@"
exec "$@"
