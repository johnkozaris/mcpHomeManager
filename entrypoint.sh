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

echo "Starting ${APP_NAME:-MCP Manager}..."
exec $PYTHON -m serve
