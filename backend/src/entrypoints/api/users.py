"""User management API (admin-only)."""

from uuid import UUID

from litestar import Controller, delete, get, patch, post
from litestar.exceptions import ClientException, NotFoundException
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.user import User
from entrypoints.api.guards import require_admin
from entrypoints.api.message_codes import ApiMessageCode, exception_extra
from entrypoints.api.schemas import CreateUserRequest, UpdateUserRequest, UserResponse
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
    async def list_users(self, user_service: UserService) -> list[UserResponse]:
        users = await user_service.list_all()
        return [_to_response(u) for u in users]

    @post("/")
    async def create_user(
        self,
        db_session: AsyncSession,
        data: CreateUserRequest,
        user_service: UserService,
    ) -> UserResponse:
        service_ids = [UUID(sid) for sid in data.allowed_service_ids]
        try:
            user = await user_service.create_user(
                username=data.username,
                is_admin=data.is_admin,
                allowed_service_ids=service_ids,
                password=data.password,
                email=data.email,
                self_mcp_enabled=data.self_mcp_enabled,
            )
        except ValueError as e:
            raise ClientException(
                str(e),
                extra=exception_extra(ApiMessageCode.HTTP_BAD_REQUEST),
            ) from e
        await db_session.commit()
        return _to_response(user)

    @get("/{user_id:uuid}")
    async def get_user(
        self,
        user_id: UUID,
        user_service: UserService,
    ) -> UserResponse:
        user = await user_service.get_by_id(user_id)
        if user is None:
            raise NotFoundException(
                "User not found",
                extra=exception_extra(ApiMessageCode.HTTP_NOT_FOUND),
            )
        return _to_response(user)

    @patch("/{user_id:uuid}")
    async def update_user(
        self,
        db_session: AsyncSession,
        user_id: UUID,
        data: UpdateUserRequest,
        user_service: UserService,
    ) -> UserResponse:
        try:
            kwargs: dict = {}
            if data.is_admin is not None:
                kwargs["is_admin"] = data.is_admin
            if data.allowed_service_ids is not None:
                kwargs["allowed_service_ids"] = [UUID(s) for s in data.allowed_service_ids]
            if data.self_mcp_enabled is not None:
                kwargs["self_mcp_enabled"] = data.self_mcp_enabled
            user = await user_service.update_user(user_id, **kwargs)
        except ValueError as e:
            raise NotFoundException(
                str(e),
                extra=exception_extra(ApiMessageCode.HTTP_NOT_FOUND),
            ) from e
        await db_session.commit()
        return _to_response(user)

    @delete("/{user_id:uuid}")
    async def delete_user(
        self,
        db_session: AsyncSession,
        user_id: UUID,
        user_service: UserService,
    ) -> None:
        await user_service.delete_user(user_id)
        await db_session.commit()
