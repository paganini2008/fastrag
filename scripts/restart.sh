#!/usr/bin/env bash
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "==> Stopping Django..."
pkill -f "manage.py runserver" 2>/dev/null && echo "    stopped" || echo "    (not running)"

echo "==> Starting Django..."
cd "$ROOT/backend"
uv run python src/manage.py runserver > /tmp/django.log 2>&1 &

echo "==> Waiting for server..."
for i in $(seq 1 10); do
  if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/docs/ | grep -q "200"; then
    echo "==> Ready at http://localhost:8000"
    exit 0
  fi
  sleep 1
done

echo "==> ERROR: server did not start in time. Check /tmp/django.log"
exit 1
