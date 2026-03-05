from abc import ABC, abstractmethod

from domain.entities.smtp_config import SmtpConfig


class ISmtpConfigRepository(ABC):
    @abstractmethod
    async def get(self) -> SmtpConfig | None: ...

    @abstractmethod
    async def upsert(self, config: SmtpConfig) -> SmtpConfig: ...
