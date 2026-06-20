#!/usr/bin/env bash
set -euo pipefail

# Postgres readiness is guaranteed by the Compose healthcheck (depends_on:
# service_healthy), so we can apply migrations immediately and then run the app.
echo "Applying database migrations..."
python manage.py migrate --noinput

exec "$@"
