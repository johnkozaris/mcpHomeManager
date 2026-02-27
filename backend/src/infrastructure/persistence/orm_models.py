from datetime import datetime
from uuid import UUID

from advanced_alchemy.base import UUIDAuditBase
from sqlalchemy import JSON, Boolean, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship


class ServiceConnectionModel(UUIDAuditBase):
    __tablename__ = "service_connections"

    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(200))
    service_type: Mapped[str] = mapped_column(String(50), index=True)
    base_url: Mapped[str] = mapped_column(String(500))
    api_token_encrypted: Mapped[str] = mapped_column(Text)
    is_enabled: Mapped[bool] = mapped_column(default=True)
    health_status: Mapped[str] = mapped_column(String(20), default="unknown")
    last_health_check: Mapped[datetime | None] = mapped_column(nullable=True)
    config_json: Mapped[dict] = mapped_column(JSON, default=dict)

    tool_permissions: Mapped[list[ToolPermissionModel]] = relationship(
        back_populates="service",
        cascade="all, delete-orphan",
        lazy="noload",
    )


class ToolPermissionModel(UUIDAuditBase):
    __tablename__ = "tool_permissions"
    __table_args__ = (
        UniqueConstraint("service_id", "tool_name", name="uq_tool_permission_service_tool"),
        Index("ix_tool_permission_service_tool", "service_id", "tool_name"),
    )

    service_id: Mapped[UUID] = mapped_column(
        ForeignKey("service_connections.id", ondelete="CASCADE"),
    )
    tool_name: Mapped[str] = mapped_column(String(200))
    is_enabled: Mapped[bool] = mapped_column(default=True)
    description_override: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    parameters_schema_override: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        default=None,
    )
    http_method_override: Mapped[str | None] = mapped_column(String(10), nullable=True, default=None)
    path_template_override: Mapped[str | None] = mapped_column(
        String(500), nullable=True, default=None
    )

    service: Mapped[ServiceConnectionModel] = relationship(
        back_populates="tool_permissions",
        lazy="noload",
    )


class UserModel(UUIDAuditBase):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(254), unique=True, nullable=True, index=True)
    api_key_hash: Mapped[str | None] = mapped_column(
        String(64),
        unique=True,
        nullable=True,
        index=True,
    )
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    self_mcp_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    allowed_service_ids: Mapped[list] = mapped_column(JSON, default=list)
    password_hash: Mapped[str | None] = mapped_column(String(256), nullable=True, default=None)
    encrypted_api_key: Mapped[str | None] = mapped_column(String(512), nullable=True, default=None)


class GenericToolDefinitionModel(UUIDAuditBase):
    __tablename__ = "generic_tool_definitions"
    __table_args__ = (
        UniqueConstraint("service_id", "tool_name", name="uq_generic_tool_service_tool"),
    )

    service_id: Mapped[UUID] = mapped_column(
        ForeignKey("service_connections.id", ondelete="CASCADE"),
    )
    tool_name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    http_method: Mapped[str] = mapped_column(String(10))
    path_template: Mapped[str] = mapped_column(String(500))
    params_schema: Mapped[dict] = mapped_column(JSON, default=dict)


class AuditLogModel(UUIDAuditBase):
    __tablename__ = "audit_logs"
    __table_args__ = (Index("ix_audit_log_created_at", "created_at"),)

    service_name: Mapped[str] = mapped_column(String(100), index=True)
    tool_name: Mapped[str] = mapped_column(String(200), index=True)
    input_summary: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20))
    duration_ms: Mapped[int]
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    client_name: Mapped[str | None] = mapped_column(String(200), nullable=True)


class SmtpConfigModel(UUIDAuditBase):
    """SMTP configuration — single-row table for email delivery settings."""

    __tablename__ = "smtp_config"

    host: Mapped[str] = mapped_column(String(253))
    port: Mapped[int] = mapped_column(default=587)
    username: Mapped[str | None] = mapped_column(String(254), nullable=True)
    password_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    from_email: Mapped[str] = mapped_column(String(254))
    use_tls: Mapped[bool] = mapped_column(Boolean, default=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class PasswordResetTokenModel(UUIDAuditBase):
    """Password reset tokens — single-use, time-limited."""

    __tablename__ = "password_reset_tokens"

    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    expires_at: Mapped[datetime] = mapped_column()


class SessionTokenModel(UUIDAuditBase):
    """Web session tokens — created on login, validated per-request."""

    __tablename__ = "session_tokens"
    __table_args__ = (
        Index("ix_session_token_hash", "token_hash"),
        Index("ix_session_user_id", "user_id"),
    )

    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
    )
    expires_at: Mapped[datetime] = mapped_column()
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    username: Mapped[str] = mapped_column(String(100))
