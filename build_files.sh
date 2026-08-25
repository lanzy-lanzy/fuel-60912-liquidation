#!/bin/bash
# Vercel build: install deps and collect static
pip install -r requirements.txt
python manage.py collectstatic --noinput
echo "Build complete"
