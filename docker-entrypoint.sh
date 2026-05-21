#!/usr/bin/env sh
set -eu

if [ -n "${DATABASE_URL:-}" ]; then
  python - <<'PY'
import os
import socket
import time
from urllib.parse import urlparse

url = urlparse(os.environ["DATABASE_URL"])
host = url.hostname
port = url.port or 5432

if host:
    deadline = time.time() + int(os.environ.get("DATABASE_WAIT_TIMEOUT", "60"))
    while True:
        try:
            with socket.create_connection((host, port), timeout=2):
                break
        except OSError:
            if time.time() >= deadline:
                raise
            time.sleep(1)
PY
fi

python manage.py migrate --noinput

if [ "${RUN_COLLECTSTATIC:-1}" = "1" ]; then
  python manage.py collectstatic --noinput
fi

if [ "${BOOTSTRAP_DATA:-1}" = "1" ]; then
  python manage.py bootstrap_render_data
fi

if [ "${SEED_DATA:-0}" = "1" ]; then
  python manage.py seed_data
fi

exec "$@"
