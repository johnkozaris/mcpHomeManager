import os
from pathlib import Path
from urllib.parse import quote

from cryptography.fernet import Fernet
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_KEY_PATH = Path("/app/data/encryption_key")

_DEFAULT_DB_PATH = Path("/app/data/mcp_home.db")
_DEV_DB_URL = "sqlite+aiosqlite:///mcp_home.db"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore removed settings (MCP_API_KEY, AUTH_MODE, etc.) in old .env files
    )

    app_name: str = "MCP Manager"
    debug: bool = False

    # Database — defaults to SQLite; POSTGRES_* parts or DATABASE_URL override
    database_url: str = Field(default="", repr=False)
    postgres_host: str = "db"
    postgres_port: int = 5432
    postgres_db: str = "mcp_home"
    postgres_user: str = "mcp"
    postgres_password: str = Field(default="", repr=False)

    encryption_key: str = Field(default="", repr=False)  # Fernet key — auto-generated on first run

    # Public URL of this application (used in password reset emails)
    public_url: str = "http://localhost:8000"

    mcp_server_name: str = "My Homelab"
    # Expose self-management tools (services, tools, audit, HTML UIs) via MCP
    self_mcp_enabled: bool = True

    health_check_interval_seconds: int = 60
    http_timeout_seconds: float = 30.0
    http_connect_timeout_seconds: float = 10.0

    @model_validator(mode="before")
    @classmethod
    def _resolve_file_secrets(cls, values: dict[str, object]) -> dict[str, object]:
        """Docker-style _FILE indirection (e.g. ENCRYPTION_KEY_FILE=/run/secrets/key)."""
        for field in ("encryption_key", "database_url", "postgres_password"):
            file_env = f"{field.upper()}_FILE"
            file_path = os.environ.get(file_env) or values.get(file_env)
            if file_path:
                path = Path(str(file_path))
                if not path.is_file():
                    raise ValueError(f"{file_env}={file_path} does not exist or is not a file")
                content = path.read_text(encoding="utf-8").strip()
                if not content:
                    raise ValueError(f"{file_env}={file_path} exists but is empty")
                values[field] = content
        return values

    @model_validator(mode="after")
    def _resolve_database_url(self) -> Settings:
        """Build DATABASE_URL from POSTGRES_* parts, or default to SQLite."""
        if self.database_url:
            return self

        if self.postgres_password:
            user = quote(self.postgres_user, safe="")
            password = quote(self.postgres_password, safe="")
            self.database_url = (
                f"postgresql+asyncpg://{user}:{password}"
                f"@{self.postgres_host}:{self.postgres_port}"
                f"/{quote(self.postgres_db, safe='')}"
            )
        elif _DEFAULT_DB_PATH.parent.exists():
            # Docker: /app/data volume exists — store DB there
            self.database_url = f"sqlite+aiosqlite:///{_DEFAULT_DB_PATH}"
        else:
            # Local dev: relative path in working directory
            self.database_url = _DEV_DB_URL
        return self

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    @model_validator(mode="after")
    def _resolve_encryption_key(self) -> Settings:
        """Auto-generate and persist a Fernet key when none is provided."""
        if self.encryption_key:
            return self

        # Try reading from persistent file (Docker volume)
        if _KEY_PATH.is_file():
            stored = _KEY_PATH.read_text(encoding="utf-8").strip()
            if not stored:
                raise ValueError(
                    f"{_KEY_PATH} exists but is empty. "
                    "Delete the file or set ENCRYPTION_KEY manually."
                )
            self.encryption_key = stored
            return self

        # Generate a new key and attempt to persist it
        key = Fernet.generate_key().decode()
        try:
            _KEY_PATH.parent.mkdir(parents=True, exist_ok=True)
            _KEY_PATH.write_text(key, encoding="utf-8")
            _KEY_PATH.chmod(0o600)
            print(f"Generated new encryption key (persisted to {_KEY_PATH})")
        except OSError:
            # Non-Docker / read-only FS — key lives only in memory this run
            print(
                "Generated new encryption key (could not persist — "
                "set ENCRYPTION_KEY env var for stable encryption across restarts)"
            )
        self.encryption_key = key
        return self


settings = Settings()
