"""User entity for multi-user access control."""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID


@dataclass
class User:
    username: str
    email: str | None = None
    api_key_hash: str | None = None
    is_admin: bool = False
    self_mcp_enabled: bool = False
    allowed_service_ids: list[UUID] = field(default_factory=list)
    password_hash: str | None = None
    encrypted_api_key: str | None = None
    id: UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
