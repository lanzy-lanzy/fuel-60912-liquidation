#!/bin/bash
# Vercel build: collect static (dependencies handled via uv.lock / requirements.txt by Vercel Python builder)
python manage.py collectstatic --noinput
echo "Build complete"
