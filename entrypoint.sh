#!/bin/sh
set -e

# Use the venv Python directly (avoids uv sync in read-only containers)
PYTHON="/app/.venv/bin/python"

if [ -z "$ENCRYPTION_KEY" ]; then
    KEY_FILE="/app/data/encryption_key"
    if [ -f "$KEY_FILE" ]; then
        ENCRYPTION_KEY=$(cat "$KEY_FILE")
        if [ -z "$ENCRYPTION_KEY" ]; then
            echo "ERROR: $KEY_FILE exists but is empty. Delete the file or set ENCRYPTION_KEY manually." >&2
            exit 1
        fi
        export ENCRYPTION_KEY
    else
        mkdir -p /app/data
        if ! ENCRYPTION_KEY=$($PYTHON -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())' 2>/dev/null); then
            echo "ERROR: Failed to generate encryption key. Is the cryptography package installed?" >&2
            exit 1
        fi
        if [ -z "$ENCRYPTION_KEY" ] || [ ${#ENCRYPTION_KEY} -ne 44 ]; then
            echo "ERROR: Generated encryption key is invalid (expected 44-char Fernet key, got ${#ENCRYPTION_KEY} chars)." >&2
            exit 1
        fi
        printf '%s' "$ENCRYPTION_KEY" > "$KEY_FILE"
        chmod 600 "$KEY_FILE"
        export ENCRYPTION_KEY
        echo "Generated new encryption key (persisted in app_data volume)"
    fi
fi

if [ -z "$DATABASE_URL" ] && [ -n "$POSTGRES_PASSWORD" ]; then
    POSTGRES_HOST="${POSTGRES_HOST:-db}"
    POSTGRES_PORT="${POSTGRES_PORT:-5432}"
    POSTGRES_DB="${POSTGRES_DB:-mcp_home}"
    POSTGRES_USER="${POSTGRES_USER:-mcp}"

    DATABASE_URL=$(
        POSTGRES_HOST="$POSTGRES_HOST" \
        POSTGRES_PORT="$POSTGRES_PORT" \
        POSTGRES_DB="$POSTGRES_DB" \
        POSTGRES_USER="$POSTGRES_USER" \
        POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
        "$PYTHON" - <<'PY'
import os
from urllib.parse import quote

print(
    "postgresql+asyncpg://"
    f"{quote(os.environ['POSTGRES_USER'], safe='')}:"
    f"{quote(os.environ['POSTGRES_PASSWORD'], safe='')}@"
    f"{os.environ['POSTGRES_HOST']}:{os.environ['POSTGRES_PORT']}/"
    f"{quote(os.environ['POSTGRES_DB'], safe='')}"
)
PY
    )
    export DATABASE_URL
fi

echo "Starting ${APP_NAME:-MCP Manager}..."
exec $PYTHON -m serve
