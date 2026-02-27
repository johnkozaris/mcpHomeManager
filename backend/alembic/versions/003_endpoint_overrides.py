"""add endpoint override columns to tool_permissions

Revision ID: 003
Revises: 002
Create Date: 2026-02-27
"""

from alembic import op
import sqlalchemy as sa

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tool_permissions",
        sa.Column("http_method_override", sa.String(10), nullable=True),
    )
    op.add_column(
        "tool_permissions",
        sa.Column("path_template_override", sa.String(500), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("tool_permissions", "path_template_override")
    op.drop_column("tool_permissions", "http_method_override")
