"""SQLAlchemy implementation of the SMTP config repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.smtp_config import SmtpConfig
from domain.ports.smtp_repository import ISmtpConfigRepository
from infrastructure.persistence.orm_models import SmtpConfigModel


class SmtpConfigRepository(ISmtpConfigRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self) -> SmtpConfig | None:
        result = await self._session.execute(select(SmtpConfigModel).limit(1))
        row = result.scalar_one_or_none()
        return self._to_entity(row) if row else None

    async def upsert(self, config: SmtpConfig) -> SmtpConfig:
        result = await self._session.execute(select(SmtpConfigModel).limit(1))
        model = result.scalar_one_or_none()

        if model is None:
            model = SmtpConfigModel(
                host=config.host,
                port=config.port,
                username=config.username,
                password_encrypted=config.password_encrypted,
                from_email=config.from_email,
                use_tls=config.use_tls,
                is_enabled=config.is_enabled,
            )
            self._session.add(model)
        else:
            model.host = config.host
            model.port = config.port
            model.username = config.username
            if config.password_encrypted is not None:
                model.password_encrypted = config.password_encrypted
            model.from_email = config.from_email
            model.use_tls = config.use_tls
            model.is_enabled = config.is_enabled

        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    @staticmethod
    def _to_entity(model: SmtpConfigModel) -> SmtpConfig:
        return SmtpConfig(
            id=model.id,
            host=model.host,
            port=model.port,
            username=model.username,
            password_encrypted=model.password_encrypted,
            from_email=model.from_email,
            use_tls=model.use_tls,
            is_enabled=model.is_enabled,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
