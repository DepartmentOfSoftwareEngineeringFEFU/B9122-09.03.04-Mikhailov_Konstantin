# ============================================================================
# auth-service Dockerfile (uv workspace)
# Build context: корень монорепо
# Команда: docker build -f auth-service/Dockerfile -t ref-auth:dev .
# ============================================================================

# ---------- Stage 1: Builder ----------
FROM python:3.12-slim AS builder

WORKDIR /build

# Системные зависимости для сборки psycopg, cryptography
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Копируем workspace-конфигурацию для кэширования слоя зависимостей.
# ВАЖНО: uv workspace требует pyproject.toml от ВСЕХ участников + корневой + uv.lock
COPY pyproject.toml uv.lock ./
COPY main-backend/pyproject.toml main-backend/pyproject.toml
COPY forecasting-service/pyproject.toml forecasting-service/pyproject.toml
COPY auth-service/pyproject.toml auth-service/pyproject.toml

# Синхронизируем зависимости ТОЛЬКО для auth-service (без dev-зависимостей)
# --frozen = использовать uv.lock без изменения
# --no-dev = без dev-группы
# --no-install-workspace = не устанавливать сами workspace-пакеты, только их deps
RUN uv sync \
    --package auth-service \
    --frozen \
    --no-dev \
    --no-install-workspace

# ---------- Stage 2: Runtime ----------
FROM python:3.12-slim AS runtime

WORKDIR /app

# Runtime-зависимости (без build-инструментов)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && addgroup --system appgroup \
    && adduser --system --ingroup appgroup appuser

# Копируем виртуальное окружение из builder
COPY --from=builder --chown=appuser:appgroup /build/.venv /app/.venv

# Копируем исходники auth-service
COPY --chown=appuser:appgroup auth-service/ .

# Создаём директории для логов
RUN mkdir -p /app/logs

# Добавляем .venv/bin в PATH
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

USER appuser

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

EXPOSE 8001

# Запуск через uvicorn напрямую (venv уже в PATH)
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8001"]