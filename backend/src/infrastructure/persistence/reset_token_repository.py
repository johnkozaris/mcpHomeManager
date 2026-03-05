from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.ports.reset_token_repository import IResetTokenRepository
from infrastructure.persistence.orm_models import PasswordResetTokenModel


class ResetTokenRepository(IResetTokenRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, token_hash: str, user_id: UUID, expires_at: datetime) -> None:
        model = PasswordResetTokenModel(
            token_hash=token_hash,
            user_id=user_id,
            expires_at=expires_at,
        )
        self._session.add(model)
        await self._session.flush()

    async def get_user_id_by_hash(self, token_hash: str) -> tuple[UUID, datetime] | None:
        result = await self._session.execute(
            select(PasswordResetTokenModel).where(PasswordResetTokenModel.token_hash == token_hash)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return (row.user_id, row.expires_at)

    async def delete_by_hash(self, token_hash: str) -> None:
        await self._session.execute(
            delete(PasswordResetTokenModel).where(PasswordResetTokenModel.token_hash == token_hash)
        )
        await self._session.flush()

    async def delete_for_user(self, user_id: UUID) -> None:
        await self._session.execute(
            delete(PasswordResetTokenModel).where(PasswordResetTokenModel.user_id == user_id)
        )
        await self._session.flush()

    async def delete_expired(self) -> int:
        result = await self._session.execute(
            delete(PasswordResetTokenModel).where(
                PasswordResetTokenModel.expires_at < datetime.now(UTC)
            )
        )
        await self._session.flush()
        rowcount = getattr(result, "rowcount", None)
        return rowcount if isinstance(rowcount, int) else 0
