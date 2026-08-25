# Deploy Fuel Tracker (Django) to **Supabase (Postgres)** + **Vercel** (via GitHub)

Your GitHub account `lanzy-lanzy` is already linked to Vercel (Continue with GitHub). Your repo is **lanzy-lanzy/fuel-60912-liquidation** (branch `main` already pushed with `db.sqlite3`).

## 1) Supabase – Create Postgres

1. Go to https://supabase.com/dashboard → **New project** → choose region (e.g. `Southeast Asia - Singapore`), set DB password (save it), wait ~1 min.
2. Project → **Settings → Database → Connection string → URI** (or **Connection pooling**):
   - **POOLER** (recommended for Vercel serverless, port **6543** + `?pgbouncer=true`):
     ```
     postgres://postgres.PROJECT_ID:PASSWORD@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?pgbouncer=true&sslmode=require
     ```
   - Copy the **pooler** URI. Replace `PASSWORD` with your DB password. Keep `?pgbouncer=true`.
   - Also copy **Direct** URI (port 5432) for local migration if needed.

> The app now reads `DATABASE_URL` (or `SUPABASE_DB_URL`) via `dj-database-url` in `fueltracker/settings.py:99`. If unset, it falls back to SQLite for local dev.

## 2) Vercel – Import GitHub repo (Recommended, no CLI token needed)

1. Go to **https://vercel.com/new** → **Continue with GitHub** (use `lanzy-lanzy`).
2. **Import Git Repository** → search `fuel-60912-liquidation` → **Import**.
3. **Framework Preset**: Other (or Python). **Root Directory**: `./` (default).
4. **Environment Variables** → Add:
   ```
   DJANGO_SECRET_KEY=generate-a-strong-random-string-at-least-50-chars
   DJANGO_DEBUG=False
   DJANGO_ALLOWED_HOSTS=*
   DJANGO_CSRF_TRUSTED_ORIGINS=https://your-app.vercel.app,https://*.vercel.app
   DATABASE_URL=postgres://postgres.PROJECT_ID:PASSWORD@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?pgbouncer=true&sslmode=require
   # Optional
   # SUPABASE_DB_URL=postgres://...
   ```
   Generate `DJANGO_SECRET_KEY` via:
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```
5. **Deploy** → wait for build (`build_files.sh` runs `collectstatic`). Vercel will run `pip install -r requirements.txt` and `python manage.py collectstatic`.

## 3) Run migrations on Supabase

### Option A – From local (after Vercel env is set, or set `DATABASE_URL` locally)

```bash
# In your local terminal, set DATABASE_URL to Supabase pooler URI
$env:DATABASE_URL="postgres://postgres.PROJECT_ID:PASSWORD@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?pgbouncer=true&sslmode=require"
uv run python manage.py migrate
# Create superuser on Supabase
uv run python manage.py createsuperuser
```

### Option B – Via Vercel CLI (if you have `VERCEL_TOKEN`)

```bash
npx vercel --prod
# Or use Vercel's "Run" with `python manage.py migrate` via `vercel env pull` + local
```

### Option C – Via Supabase SQL editor

The `migrate` command creates all tables (`fuel_*`, `auth_*`, etc.). You can also run `python manage.py migrate --run-syncdb` locally with `DATABASE_URL` set.

## 4) Migrate data from SQLite (`db.sqlite3`) to Supabase

Your current `db.sqlite3` (24 PCVs, RERs, liquidation reports) is already committed. To copy to Supabase:

```bash
# 1. Dump from SQLite (default)
uv run python manage.py dumpdata --natural-foreign --natural-primary -e contenttypes -e auth.Permission --indent 2 > data.json

# 2. Switch to Supabase
$env:DATABASE_URL="postgres://..."  # pooler URI
uv run python manage.py migrate
uv run python manage.py loaddata data.json

# Alternative: use pgloader or supabase import
```

Or use the included script:

```bash
# Dump and load in one go (see scripts/migrate_sqlite_to_supabase.py if present)
python scripts/migrate_sqlite_to_supabase.py
```

> **Media files** (`media/rer_images/*`) are currently on local disk and ignored via `.gitignore: media/`. For Vercel/Supabase production, either:
> - Keep `MEDIA_ROOT` on Vercel's ephemeral `/tmp` (not persistent), or
> - Migrate to **Supabase Storage**: create bucket `rer_images` in Supabase Dashboard → Storage, then set `DEFAULT_FILE_STORAGE` to `storages.backends.s3boto3.S3Boto3Storage` with Supabase S3 credentials. Current setup will still work but images will be ephemeral on Vercel.

## 5) Vercel CLI Alternative (if you prefer CLI over dashboard)

```bash
# Install Vercel CLI (already via npx)
npx vercel --version  # 59.5.0

# Login via GitHub (opens browser)
npx vercel login

# Link project (choose `lanzy-lanzy/fuel-60912-liquidation`)
npx vercel link

# Add env vars
npx vercel env add DATABASE_URL
npx vercel env add DJANGO_SECRET_KEY
npx vercel env add DJANGO_DEBUG
npx vercel env add DJANGO_ALLOWED_HOSTS
npx vercel env add DJANGO_CSRF_TRUSTED_ORIGINS

# Deploy
npx vercel --prod
```

Or with token:

```bash
# Create token at vercel.com/account/tokens
$env:VERCEL_TOKEN="vercel_xxx"
npx vercel --prod --token $env:VERCEL_TOKEN
```

## 6) Verify

- Vercel URL: `https://your-app.vercel.app` → should show dashboard, PCV list (`/pcv/`), RER list, liquidation report.
- Check logs: `npx vercel logs <deployment-url> --prod`
- Supabase: Dashboard → **Table Editor** → verify `fuel_pettycashvoucher`, `fuel_reimbursementexpensereceipt`, etc.

## 7) Files added for deployment

- `vercel.json` – routes all to `fueltracker/wsgi.py` (`app` alias), static via `build_files.sh`
- `build_files.sh` – `pip install -r requirements.txt && collectstatic`
- `requirements.txt` – `django`, `openpyxl`, `reportlab`, `psycopg2-binary`, `whitenoise`, `dj-database-url`, `python-dotenv`, `gunicorn`, `Pillow`
- `fueltracker/settings.py` – `django-environ` + `dj-database-url` + `WhiteNoise`, `DATABASE_URL`/`SUPABASE_DB_URL`, `VERCEL_URL` handling
- `fueltracker/wsgi.py` – `app = application` for Vercel
- `.env.example` – env template
- `pyproject.toml` – added prod deps, `uv.lock` updated

## 8) Push (already done)

```bash
git add db.sqlite3 fuel/migrations/0016* 0017* 0018* fuel/*.py templates/ vercel.json build_files.sh requirements.txt .env.example
git commit -m "feat: ..."
git push new-origin main
# Vercel auto-deploys on push if GitHub integration is enabled
```

Your `main` is at `9933fc5`+`6bfa5d7` with DB. Next push will auto-deploy on Vercel if import is set to auto-deploy on push.

---

**Need help?** Provide your Supabase `DATABASE_URL` and Vercel token, and I can run `migrate` + `deploy` for you via CLI here.
