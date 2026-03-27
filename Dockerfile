# ── Dockerfile ─────────────────────────────────────────────────────────────────
# Targets both amd64 (dev machine) and arm64/arm/v7 (Raspberry Pi).
# python:3.12-slim is available for all three via Docker's multi-platform images.

FROM python:3.12-slim

# Non-root user for safety
RUN addgroup --system app && adduser --system --ingroup app app

# Install sqlite3 CLI for manual DB inspection / fixes
RUN apt-get update && apt-get install -y --no-install-recommends sqlite3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies first (layer-cached)
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ .

# Entrypoint needs execute permission
RUN chmod +x entrypoint.sh

# Data directory (will be overridden by the Docker volume)
RUN mkdir -p /data && chown app:app /data

USER app

EXPOSE 5000

ENTRYPOINT ["./entrypoint.sh"]
