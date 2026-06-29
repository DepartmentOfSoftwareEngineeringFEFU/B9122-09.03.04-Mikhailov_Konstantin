FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/


COPY pyproject.toml uv.lock ./
COPY main-backend/pyproject.toml main-backend/pyproject.toml
COPY forecasting-service/pyproject.toml forecasting-service/pyproject.toml
COPY auth-service/pyproject.toml auth-service/pyproject.toml


RUN uv sync \
    --package auth-service \
    --frozen \
    --no-dev \
    --no-install-workspace


FROM python:3.12-slim AS runtime

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && addgroup --system appgroup \
    && adduser --system --ingroup appgroup appuser

COPY --from=builder --chown=appuser:appgroup /build/.venv /app/.venv

COPY --chown=appuser:appgroup auth-service/ .

RUN mkdir -p /app/logs

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

USER appuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

EXPOSE 8001

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8001"]