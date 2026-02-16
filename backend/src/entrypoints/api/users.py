"""User management API (admin-only)."""

from uuid import UUID

from litestar import Controller, delete, get, patch, post
from litestar.exceptions import ClientException, NotFoundException
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.user import User
from entrypoints.api.guards import require_admin
from entrypoints.api.schemas import CreateUserRequest, UpdateUserRequest, UserResponse
from infrastructure.persistence.user_repository import UserRepository
from services.user_service import UserService


def _to_response(user: User) -> UserResponse:
    if user.id is None:
        raise ValueError("User ID is required for API responses")
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        is_admin=user.is_admin,
        self_mcp_enabled=user.self_mcp_enabled,
        allowed_service_ids=[str(sid) for sid in user.allowed_service_ids],
        created_at=user.created_at,
    )


class UserController(Controller):
    path = "/api/users"
    guards = [require_admin]

    @get("/")
    async def list_users(self, db_session: AsyncSession) -> list[UserResponse]:
        svc = UserService(UserRepository(db_session))
        users = await svc.list_all()
        return [_to_response(u) for u in users]

    @post("/")
    async def create_user(
        self,
        db_session: AsyncSession,
        data: CreateUserRequest,
    ) -> UserResponse:
        svc = UserService(UserRepository(db_session))
        service_ids = [UUID(sid) for sid in data.allowed_service_ids]
        try:
            user = await svc.create_user(
                username=data.username,
                is_admin=data.is_admin,
                allowed_service_ids=service_ids,
                password=data.password,
                email=data.email,
                self_mcp_enabled=data.self_mcp_enabled,
            )
        except ValueError as e:
            raise ClientException(str(e)) from e
        await db_session.commit()
        return _to_response(user)

    @get("/{user_id:uuid}")
    async def get_user(
        self,
        db_session: AsyncSession,
        user_id: UUID,
    ) -> UserResponse:
        svc = UserService(UserRepository(db_session))
        user = await svc.get_by_id(user_id)
        if user is None:
            raise NotFoundException("User not found")
        return _to_response(user)

    @patch("/{user_id:uuid}")
    async def update_user(
        self,
        db_session: AsyncSession,
        user_id: UUID,
        data: UpdateUserRequest,
    ) -> UserResponse:
        svc = UserService(UserRepository(db_session))
        try:
            kwargs: dict = {}
            if data.is_admin is not None:
                kwargs["is_admin"] = data.is_admin
            if data.allowed_service_ids is not None:
                kwargs["allowed_service_ids"] = [UUID(s) for s in data.allowed_service_ids]
            if data.self_mcp_enabled is not None:
                kwargs["self_mcp_enabled"] = data.self_mcp_enabled
            user = await svc.update_user(user_id, **kwargs)
        except ValueError as e:
            raise NotFoundException(str(e)) from e
        await db_session.commit()
        return _to_response(user)

    @delete("/{user_id:uuid}")
    async def delete_user(
        self,
        db_session: AsyncSession,
        user_id: UUID,
    ) -> None:
        svc = UserService(UserRepository(db_session))
        await svc.delete_user(user_id)
        await db_session.commit()
