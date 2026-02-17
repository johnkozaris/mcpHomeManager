# ---- Stage 1: Build frontend ----
FROM node:24-alpine AS frontend-build

WORKDIR /app

RUN corepack enable

COPY frontend/package.json frontend/pnpm-lock.yaml* ./
RUN pnpm install --frozen-lockfile

COPY frontend/ .
RUN pnpm build


# ---- Stage 2: Python app + built frontend ----
FROM python:3.14-slim

WORKDIR /app

# Install curl for healthcheck (slim image has no curl/wget)
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv (pinned for reproducible builds)
COPY --from=ghcr.io/astral-sh/uv:0.10 /uv /uvx /bin/

# Store uv-managed Python inside /app (not /root) so non-root user can access it
ENV UV_PYTHON_INSTALL_DIR=/app/.python

# Copy dependency files
COPY backend/pyproject.toml backend/uv.lock ./

# Install dependencies (without the project itself)
RUN uv sync --no-dev --no-install-project

# Copy source and install the project
COPY backend/src/ src/

RUN uv sync --no-dev

# Copy built frontend into static/ (Litestar serves this via create_static_files_router)
COPY --from=frontend-build /app/dist /app/static

# Entrypoint: run migrations then start server
COPY entrypoint.sh /app/entrypoint.sh

# Non-root user with access to /app (including /app/data for persisted encryption key)
RUN mkdir -p /app/data \
    && adduser --disabled-password --no-create-home appuser \
    && chown -R appuser:appuser /app
USER appuser

ENV UV_NO_CACHE=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -sf http://localhost:8000/api/health/ || exit 1

CMD ["/app/entrypoint.sh"]
