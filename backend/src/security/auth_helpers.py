"""Shared authentication helpers for API and MCP auth paths."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from domain.entities.user import User
from infrastructure.persistence.user_repository import UserRepository
from security.auth_context import AuthContext
from services.user_service import UserService


def extract_api_token(*, auth_header: str, api_key_header: str) -> str:
    bearer_token = auth_header[7:].strip() if auth_header.lower().startswith("bearer ") else ""
    return api_key_header or bearer_token


def build_auth_context(user: User) -> AuthContext:
    return AuthContext(
        is_admin=user.is_admin,
        allowed_service_ids={str(sid) for sid in user.allowed_service_ids},
        username=user.username,
        user_id=str(user.id) if user.id is not None else None,
        self_mcp_enabled=user.self_mcp_enabled,
    )


async def authenticate_api_key(
    session_factory: async_sessionmaker[AsyncSession],
    token: str,
) -> User | None:
    async with session_factory() as session:
        user_svc = UserService(UserRepository(session))
        return await user_svc.authenticate_by_key(token)
