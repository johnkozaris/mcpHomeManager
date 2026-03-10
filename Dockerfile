# ---- Stage 1: Build frontend ----
FROM node:24-alpine AS frontend-build

WORKDIR /app

RUN corepack enable

ARG APP_VERSION

COPY frontend/package.json frontend/pnpm-lock.yaml* frontend/pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile

COPY frontend/ .
RUN APP_VERSION="${APP_VERSION}" pnpm build


# ---- Stage 2: Python app + built frontend ----
FROM python:3.14-slim

WORKDIR /app

ARG APP_VERSION=dev
ARG VCS_REF=unknown
ARG BUILD_DATE=unknown
ARG REPO_URL=https://github.com/johnkozaris/mcpHomeManager

LABEL org.opencontainers.image.title="MCP Home Manager" \
    org.opencontainers.image.description="Self-hosted gateway that connects homelab services to AI clients via MCP." \
    org.opencontainers.image.url="${REPO_URL}" \
    org.opencontainers.image.source="${REPO_URL}" \
    org.opencontainers.image.documentation="${REPO_URL}#readme" \
    org.opencontainers.image.licenses="MIT" \
    org.opencontainers.image.vendor="MCP Home Manager Contributors" \
    org.opencontainers.image.version="${APP_VERSION}" \
    org.opencontainers.image.revision="${VCS_REF}" \
    org.opencontainers.image.created="${BUILD_DATE}" \
    org.opencontainers.image.base.name="docker.io/library/python:3.14-slim"

# Install curl for healthcheck (slim image has no curl/wget)
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv (pinned for reproducible builds)
COPY --from=ghcr.io/astral-sh/uv:0.10 /uv /uvx /bin/

# Store uv-managed Python inside /app (not /root) so non-root user can access it
ENV UV_PYTHON_INSTALL_DIR=/app/.python

# Copy dependency files
COPY backend/pyproject.toml backend/uv.lock backend/README.md ./

# Install dependencies (without the project itself)
RUN uv sync --no-dev --no-install-project

# Copy source and install the project
COPY backend/src/ src/

RUN uv sync --no-dev

# Copy built frontend into static/ (Litestar serves this via create_static_files_router)
COPY --from=frontend-build /app/dist /app/static

# Non-root user with access to /app (including /app/data for encryption key + SQLite DB)
RUN mkdir -p /app/data \
    && adduser --disabled-password --no-create-home appuser \
    && chown -R appuser:appuser /app
USER appuser

ENV UV_NO_CACHE=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -sf http://localhost:8000/api/health/ || exit 1

CMD ["/app/.venv/bin/python", "-m", "serve"]
