from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore removed settings (MCP_API_KEY, AUTH_MODE, etc.) in old .env files
    )

    # Application — all configurable for open-source use
    app_name: str = "MCP Manager"
    debug: bool = False

    # Database — override via DATABASE_URL env var
    database_url: str = "postgresql+asyncpg://mcp:changeme@localhost:5432/mcp_home"

    # Security
    encryption_key: str = ""  # Fernet key — must be set in production

    # Public URL of this application (used in password reset emails)
    public_url: str = "http://localhost:8000"

    # MCP — these are user-configurable
    mcp_server_name: str = "My Homelab"
    # Expose management tools (list/add services, toggle tools) via MCP
    self_mcp_enabled: bool = True

    # Timeouts & intervals — override via env vars
    health_check_interval_seconds: int = 60
    http_timeout_seconds: float = 30.0
    http_connect_timeout_seconds: float = 10.0


settings = Settings()
