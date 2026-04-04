# ── Stage 1: base ─────────────────────────────────────────────────
FROM python:3.11-slim AS base

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY frontend/ ./frontend/

ENV PYTHONPATH=/app/backend

EXPOSE 8000


# ── Stage 2: development ──────────────────────────────────────────
FROM base AS development

COPY backend/requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]


# ── Stage 3: production ───────────────────────────────────────────
FROM base AS production

# Run as non-root user for security
RUN adduser --disabled-password --gecos "" appuser
USER appuser

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]

# docker buildx build --platform linux/amd64,linux/arm64 -t anshulkumar1997/roast-my-code:latest --push .