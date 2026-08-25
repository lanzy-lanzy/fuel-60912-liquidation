#!/bin/bash
# Vercel build: migrate Supabase (if DATABASE_URL set) + collect static
# Dependencies handled via uv.lock by Vercel Python builder
set -e
if [ -n "$DATABASE_URL" ]; then
  echo "Running migrations on Supabase..."
  if command -v uv >/dev/null 2>&1; then
    uv run python manage.py migrate --noinput || python manage.py migrate --noinput || echo "migrate failed (check DATABASE_URL)"
  else
    python manage.py migrate --noinput || echo "migrate failed"
  fi
fi
if command -v uv >/dev/null 2>&1; then
  uv run python manage.py collectstatic --noinput || python manage.py collectstatic --noinput
else
  python manage.py collectstatic --noinput
fi
echo "Build complete"
