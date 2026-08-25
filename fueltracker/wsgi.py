"""
WSGI config for fueltracker project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os
import shutil
from pathlib import Path

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fueltracker.settings')

# On Vercel, filesystem is read-only except /tmp. Copy db.sqlite3 and media to /tmp for writable SQLite/media
if os.environ.get('VERCEL'):
    try:
        base_dir = Path(__file__).resolve().parent.parent
        src_db = base_dir / 'db.sqlite3'
        dst_db = Path('/tmp/db.sqlite3')
        if src_db.exists() and not dst_db.exists():
            shutil.copy(str(src_db), str(dst_db))
        # Ensure /tmp/media exists and copy existing rer_images for RER
        src_media = base_dir / 'media'
        dst_media = Path('/tmp/media')
        dst_media.mkdir(parents=True, exist_ok=True)
        if src_media.exists():
            # Copy rer_images folder if present
            src_rer = src_media / 'rer_images'
            dst_rer = dst_media / 'rer_images'
            if src_rer.exists() and not dst_rer.exists():
                shutil.copytree(str(src_rer), str(dst_rer), dirs_exist_ok=True)
    except Exception:
        pass

application = get_wsgi_application()
# Vercel expects `app` as well
app = application
