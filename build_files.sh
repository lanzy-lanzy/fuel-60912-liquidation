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
  # Populate Supabase from data.json if DB is empty (first deploy)
  if [ -f "data.json" ]; then
    echo "Checking if Supabase needs data seeding..."
    if command -v uv >/dev/null 2>&1; then
      uv run python -c "import os, django; os.environ.setdefault('DJANGO_SETTINGS_MODULE','fueltracker.settings'); django.setup(); from fuel.models import PettyCashVoucher; print(PettyCashVoucher.objects.count())" 2>&1 | grep -q "0" && echo "Seeding Supabase from data.json..." && (uv run python manage.py loaddata data.json || python manage.py loaddata data.json || echo "loaddata failed") || echo "Supabase already has data, skipping loaddata"
    else
      python -c "import os, django; os.environ.setdefault('DJANGO_SETTINGS_MODULE','fueltracker.settings'); django.setup(); from fuel.models import PettyCashVoucher; print(PettyCashVoucher.objects.count())" 2>&1 | grep -q "0" && echo "Seeding..." && (python manage.py loaddata data.json || echo "loaddata failed") || echo "already has data"
    fi
  fi
fi
if command -v uv >/dev/null 2>&1; then
  uv run python manage.py collectstatic --noinput || python manage.py collectstatic --noinput
else
  python manage.py collectstatic --noinput
fi
echo "Build complete"
