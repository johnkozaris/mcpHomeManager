"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-02-18

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from advanced_alchemy.types import GUID, DateTimeUTC

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "service_connections",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("display_name", sa.String(200), nullable=False),
        sa.Column("service_type", sa.String(50), nullable=False),
        sa.Column("base_url", sa.String(500), nullable=False),
        sa.Column("api_token_encrypted", sa.Text(), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("health_status", sa.String(20), nullable=False, server_default=sa.text("'unknown'")),
        sa.Column("last_health_check", DateTimeUTC(timezone=True), nullable=True),
        sa.Column("config_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("sa_orm_sentinel", sa.Integer(), nullable=True),
        sa.Column("created_at", DateTimeUTC(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", DateTimeUTC(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_service_connections_name", "service_connections", ["name"], unique=True)
    op.create_index("ix_service_connections_service_type", "service_connections", ["service_type"])

    op.create_table(
        "tool_permissions",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("service_id", GUID(), sa.ForeignKey("service_connections.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tool_name", sa.String(200), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("description_override", sa.Text(), nullable=True),
        sa.Column("parameters_schema_override", sa.JSON(), nullable=True),
        sa.Column("sa_orm_sentinel", sa.Integer(), nullable=True),
        sa.Column("created_at", DateTimeUTC(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", DateTimeUTC(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("service_id", "tool_name", name="uq_tool_permission_service_tool"),
    )
    op.create_index("ix_tool_permission_service_tool", "tool_permissions", ["service_id", "tool_name"])

    op.create_table(
        "users",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("username", sa.String(100), nullable=False),
        sa.Column("email", sa.String(254), nullable=True),
        sa.Column("api_key_hash", sa.String(64), nullable=True),
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("self_mcp_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("allowed_service_ids", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("password_hash", sa.String(256), nullable=True),
        sa.Column("encrypted_api_key", sa.String(512), nullable=True),
        sa.Column("sa_orm_sentinel", sa.Integer(), nullable=True),
        sa.Column("created_at", DateTimeUTC(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", DateTimeUTC(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_api_key_hash", "users", ["api_key_hash"], unique=True)

    op.create_table(
        "generic_tool_definitions",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("service_id", GUID(), sa.ForeignKey("service_connections.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tool_name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=sa.text("''")),
        sa.Column("http_method", sa.String(10), nullable=False),
        sa.Column("path_template", sa.String(500), nullable=False),
        sa.Column("params_schema", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("sa_orm_sentinel", sa.Integer(), nullable=True),
        sa.Column("created_at", DateTimeUTC(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", DateTimeUTC(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("service_id", "tool_name", name="uq_generic_tool_service_tool"),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("service_name", sa.String(100), nullable=False),
        sa.Column("tool_name", sa.String(200), nullable=False),
        sa.Column("input_summary", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("client_name", sa.String(200), nullable=True),
        sa.Column("sa_orm_sentinel", sa.Integer(), nullable=True),
        sa.Column("created_at", DateTimeUTC(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", DateTimeUTC(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_log_created_at", "audit_logs", ["created_at"])
    op.create_index("ix_audit_logs_service_name", "audit_logs", ["service_name"])
    op.create_index("ix_audit_logs_tool_name", "audit_logs", ["tool_name"])

    op.create_table(
        "session_tokens",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("user_id", GUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
        sa.Column("expires_at", DateTimeUTC(timezone=True), nullable=False),
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("username", sa.String(100), nullable=False),
        sa.Column("sa_orm_sentinel", sa.Integer(), nullable=True),
        sa.Column("created_at", DateTimeUTC(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", DateTimeUTC(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_session_token_hash", "session_tokens", ["token_hash"], unique=True)
    op.create_index("ix_session_user_id", "session_tokens", ["user_id"])


def downgrade() -> None:
    op.drop_table("session_tokens")
    op.drop_table("audit_logs")
    op.drop_table("generic_tool_definitions")
    op.drop_table("tool_permissions")
    op.drop_table("users")
    op.drop_table("service_connections")
