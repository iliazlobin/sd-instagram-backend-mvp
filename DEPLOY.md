# Instagram MVP — Deployment Guide

Minimal host deploy walkthrough. Requires: **Docker** (Engine 24+), **docker compose** (v2).

## Quick start (host)

```bash
# 1. Clone the repo
git clone <repo-url> instagram-mvp
cd instagram-mvp

# 2. Create your env from the example (edit if needed)
cp .env.example .env

# 3. Bring the stack up (builds image, starts db + app)
docker compose up -d

# 4. Wait for healthy — migrations run automatically in the container.
#    Check with:
curl http://localhost:8010/healthz
# Expected: {"status":"ok","db":"connected"}

# 5. Run the acceptance suite (optional, from host)
source verify/manifest.env
API_BASE_URL=http://localhost:8010 $TEST_DEPS
API_BASE_URL=http://localhost:8010 $ACCEPTANCE
```

## Sandbox verification (no Docker required)

If Docker is unavailable, verify the app directly:

```bash
# Create a virtualenv
python -m venv .venv && source .venv/bin/activate

# Install the app + dev deps
pip install -e ".[dev]"

# Run migrations (against a local Postgres or host.docker.internal)
export DATABASE_URL="postgresql+asyncpg://instagram:instagram@host.docker.internal:5432/instagram"
alembic upgrade head

# Start the server
python -m uvicorn instagram.main:app --host 0.0.0.0 --port 8000 &

# Verify
curl http://localhost:8000/healthz
# Expected: {"status":"ok","db":"connected"}

# Run unit tests
pytest tests/ -v

# Run acceptance tests (against the running app)
API_BASE_URL=http://localhost:8000 pytest verify/acceptance/ -v
```

## Ports

| Service | Container port | Host port (via env) | Notes |
|---------|---------------|---------------------|-------|
| app     | 8000          | `${APP_PORT:-8010}` | Change `APP_PORT` in `.env` if 8010 is taken |
| db      | 5432          | **not published**   | Internal compose network only |

## Teardown

```bash
# Stop containers, remove them, and delete the named volume
docker compose down -v
```

## Environment reference

All variables are documented with safe defaults in `.env.example`. The app reads them via
`pydantic-settings` (see `src/instagram/config.py`). Required variables:

| Variable            | Default (compose)                                              | Purpose                    |
|---------------------|----------------------------------------------------------------|----------------------------|
| `DATABASE_URL`      | `postgresql+asyncpg://instagram:instagram@db:5432/instagram`   | Database connection        |
| `APP_PORT`          | `8010`                                                         | Host port mapping          |
| `MEDIA_DIR`         | `media`                                                        | Upload storage directory   |
| `MAX_UPLOAD_BYTES`  | `10485760`                                                     | Max upload size (10 MB)    |
| `HOST`              | `0.0.0.0`                                                      | Server bind address        |
| `PORT`              | `8000`                                                         | Server listen port         |

Feed and search pagination defaults are also configurable — see `.env.example` for all options.
