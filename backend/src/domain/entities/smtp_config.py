"""SMTP configuration entity for email delivery."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class SmtpConfig:
    host: str
    port: int = 587
    username: str | None = None
    password_encrypted: str | None = None
    from_email: str = ""
    use_tls: bool = True
    is_enabled: bool = True
    id: UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
