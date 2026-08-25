#!/bin/bash
# Vercel build: collect static (dependencies handled via uv.lock by Vercel Python builder)
# Use uv run to ensure venv is used if available, fallback to python
if command -v uv >/dev/null 2>&1; then
  uv run python manage.py collectstatic --noinput || python manage.py collectstatic --noinput
else
  python manage.py collectstatic --noinput
fi
echo "Build complete"
