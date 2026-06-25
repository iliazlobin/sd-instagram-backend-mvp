# ============================================================
# Builder stage — installs Python deps into a virtualenv
# ============================================================
FROM python:3.12-slim AS builder

ENV PYTHONUNBUFFERED=1

WORKDIR /build

# Install system deps needed for psycopg2/asyncpg build
RUN apt-get update -qq \
    && apt-get install -y -qq --no-install-recommends \
        gcc \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create and activate a virtualenv for isolation
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install runtime deps from requirements.txt (generated from pyproject.toml)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ============================================================
# Runtime stage — slim, no build tools, non-root user
# ============================================================
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1

# Only the libpq runtime library; no compiler, no curl
RUN apt-get update -qq \
    && apt-get install -y -qq --no-install-recommends \
        libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy the virtualenv from the builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Non-root user
RUN useradd --create-home --shell /bin/bash appuser
USER appuser

WORKDIR /app

# The app is a src-layout package copied as loose source (not pip-installed into
# the venv), so put src/ on the import path — required for `uvicorn instagram.main:app`
# and for alembic/env.py (which imports instagram.config / instagram.database).
ENV PYTHONPATH="/app/src"

# Copy application source
COPY --chown=appuser:appuser src/ src/
COPY --chown=appuser:appuser alembic.ini .
COPY --chown=appuser:appuser alembic/ alembic/
COPY --chown=appuser:appuser pyproject.toml .

# In-container app port
EXPOSE 8000

# Healthcheck — uses stdlib urllib (no curl needed in slim)
HEALTHCHECK --interval=10s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz')"

# Run migrations then start the server
CMD ["sh", "-c", "alembic upgrade head && uvicorn instagram.main:app --host 0.0.0.0 --port 8000"]
