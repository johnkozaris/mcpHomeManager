"""First-run setup wizard — creates the initial admin account.

The POST /api/setup endpoint is one of the few unauthenticated endpoints.
It only succeeds when zero users exist in the database, enforced inside
the DB transaction to prevent race conditions.
"""

from typing import Annotated

import msgspec
import structlog
from litestar import Controller, Response, get, post
from litestar.exceptions import ClientException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from entrypoints.api.auth import apply_session_cookie, create_session
from infrastructure.persistence.user_repository import UserRepository
from services.user_service import UserService

logger = structlog.get_logger()


class SetupRequest(msgspec.Struct):
    username: Annotated[str, msgspec.Meta(min_length=2, max_length=100)]
    password: Annotated[str, msgspec.Meta(min_length=8, max_length=200)]
    email: str | None = None


class SetupResponse(msgspec.Struct):
    token: str
    username: str
    is_admin: bool
    api_key: str


class SetupStatusResponse(msgspec.Struct):
    setup_required: bool


class SetupController(Controller):
    path = "/api/setup"

    @get("/status", exclude_from_auth=True)
    async def status(self, db_session: AsyncSession) -> SetupStatusResponse:
        """Check whether the initial setup wizard needs to run."""
        repo = UserRepository(db_session)
        count = await repo.get_count()
        return SetupStatusResponse(setup_required=count == 0)

    @post("/", exclude_from_auth=True)
    async def setup(
        self,
        db_session: AsyncSession,
        data: SetupRequest,
        user_service: UserService,
    ) -> Response[SetupResponse]:
        """Create the initial admin account. Only works when no users exist."""
        repo = UserRepository(db_session)

        # Race-safe: check inside the transaction
        count = await repo.get_count()
        if count > 0:
            raise ClientException(
                "Setup already completed. An admin account already exists.",
                status_code=409,
            )

        if data.email:
            parts = data.email.split("@")
            if len(parts) != 2 or not parts[0] or not parts[1] or "." not in parts[1]:
                raise ClientException("Invalid email address.")

        try:
            user = await user_service.create_user(
                username=data.username,
                is_admin=True,
                self_mcp_enabled=True,
                password=data.password,
                email=data.email,
            )
        except (ValueError, IntegrityError) as e:
            raise ClientException(
                "Setup already completed. An admin account already exists.",
                status_code=409,
            ) from e

        if user.id is None:
            raise RuntimeError("User was created without an ID — this should never happen")
        _, api_key = await user_service.generate_api_key(user.id)

        token = await create_session(
            db_session,
            username=user.username,
            is_admin=True,
            user_id=str(user.id),
        )

        await db_session.commit()

        logger.info("setup_complete", username=user.username)

        body = SetupResponse(
            token=token,
            username=user.username,
            is_admin=True,
            api_key=api_key,
        )
        response = Response(content=body)
        apply_session_cookie(response, token)
        return response
