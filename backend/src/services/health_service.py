"""Background health check service with per-service commits and jitter."""

import asyncio
import random
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from uuid import UUID

import structlog
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from domain.entities.service_connection import ServiceConnection
from domain.exceptions import ServiceConnectionError
from domain.ports.encryption import IEncryptionPort
from domain.ports.service_repository import IServiceRepository
from infrastructure import metrics as prom_metrics
from services.client_factory import ServiceClientFactory

logger = structlog.get_logger()

_JITTER_FRACTION = 0.2


class HealthCheckRunner:
    """Runs periodic health checks against all enabled services.

    Each service is checked and committed individually so a single failure
    doesn't roll back updates for other services.  A random jitter is added
    to the sleep interval to avoid thundering-herd effects when many
    instances start simultaneously.
    """

    # Maximum backoff multiplier (caps exponential growth).
    _MAX_BACKOFF = 10

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        encryption: IEncryptionPort,
        client_factory: ServiceClientFactory,
        *,
        interval_seconds: int = 60,
        service_repo_factory: Callable[[AsyncSession], IServiceRepository] | None = None,
        audit_retention_days: int = 90,
    ) -> None:
        self._session_factory = session_factory
        self._encryption = encryption
        self._client_factory = client_factory
        self._interval = interval_seconds
        self._running = False
        self._service_repo_factory = service_repo_factory
        self._audit_retention_days = audit_retention_days
        self._checks_since_cleanup = 0
        self._lock = asyncio.Lock()
        self._failure_counts: dict[UUID, int] = {}
        self._cycle: int = 0

    def update_encryption(self, encryption: IEncryptionPort) -> None:
        """Update encryption instance after key rotation."""
        self._encryption = encryption

    async def run_forever(self) -> None:
        """Run health checks in a loop until cancelled."""
        while True:
            jitter = random.uniform(0, self._interval * _JITTER_FRACTION)  # noqa: S311 -- jitter timing, not security
            await asyncio.sleep(self._interval + jitter)
            # Atomic non-blocking acquire: avoids the race between
            # checking locked() and entering `async with self._lock`.
            try:
                await asyncio.wait_for(self._lock.acquire(), timeout=0)
            except TimeoutError:
                logger.debug("Skipping health check — previous cycle still running")
                continue
            try:
                await self._check_all()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Background health check cycle failed")
            finally:
                self._lock.release()

    def _make_repo(self, session: AsyncSession) -> IServiceRepository:
        if self._service_repo_factory:
            return self._service_repo_factory(session)
        from infrastructure.persistence.service_repository import ServiceRepository

        return ServiceRepository(session)

    async def _check_all(self) -> None:
        """Load enabled services, then check each one in its own session/commit."""
        self._cycle += 1

        async with self._session_factory() as session:
            repo = self._make_repo(session)
            services = await repo.get_enabled()

        healthy = 0
        skipped = 0
        for svc in services:
            if svc.id is None:
                continue
            failures = self._failure_counts.get(svc.id, 0)
            backoff = min(2**failures, self._MAX_BACKOFF) if failures > 0 else 1
            if self._cycle % backoff != 0:
                skipped += 1
                continue

            ok = await self._check_one(svc)
            if ok:
                healthy += 1

        logger.info(
            "Health check cycle %d: %d/%d healthy, %d skipped (backoff)",
            self._cycle,
            healthy,
            len(services),
            skipped,
        )

        active_ids = {svc.id for svc in services if svc.id is not None}
        self._failure_counts = {k: v for k, v in self._failure_counts.items() if k in active_ids}

        prom_metrics.services_total.set(len(services))
        prom_metrics.services_healthy.set(healthy)

        self._checks_since_cleanup += 1
        if self._checks_since_cleanup >= 100:
            self._checks_since_cleanup = 0
            await self._cleanup_audit_logs()
            await self._cleanup_expired_sessions()
            await self._cleanup_expired_reset_tokens()

    async def _cleanup_audit_logs(self) -> None:
        """Delete audit log entries older than the retention period."""
        if self._audit_retention_days <= 0:
            return
        cutoff = datetime.now(UTC) - timedelta(days=self._audit_retention_days)
        try:
            async with self._session_factory() as session:
                from infrastructure.persistence.audit_repository import AuditRepository

                repo = AuditRepository(session)
                deleted = await repo.delete_older_than(cutoff)
                await session.commit()
                if deleted:
                    logger.info(
                        "Audit log cleanup: deleted %d entries older than %d days",
                        deleted,
                        self._audit_retention_days,
                    )
        except Exception:
            logger.exception("Audit log cleanup failed")

    async def _cleanup_expired_sessions(self) -> None:
        """Delete expired session tokens."""
        try:
            async with self._session_factory() as session:
                from sqlalchemy import delete as sa_delete

                from infrastructure.persistence.orm_models import SessionTokenModel

                result = await session.execute(
                    sa_delete(SessionTokenModel).where(
                        SessionTokenModel.expires_at < datetime.now(UTC)
                    )
                )
                await session.commit()
                cursor_result = result if isinstance(result, CursorResult) else None
                deleted = cursor_result.rowcount if cursor_result is not None else 0
                if deleted:
                    logger.info("Session cleanup: deleted %d expired tokens", deleted)
        except Exception:
            logger.exception("Session token cleanup failed")

    async def _cleanup_expired_reset_tokens(self) -> None:
        """Delete expired password reset tokens."""
        try:
            async with self._session_factory() as session:
                from sqlalchemy import delete as sa_delete

                from infrastructure.persistence.orm_models import PasswordResetTokenModel

                result = await session.execute(
                    sa_delete(PasswordResetTokenModel).where(
                        PasswordResetTokenModel.expires_at < datetime.now(UTC)
                    )
                )
                await session.commit()
                cursor_result = result if isinstance(result, CursorResult) else None
                deleted = cursor_result.rowcount if cursor_result is not None else 0
                if deleted:
                    logger.info("Reset token cleanup: deleted %d expired tokens", deleted)
        except Exception:
            logger.exception("Reset token cleanup failed")

    async def _check_one(self, svc: ServiceConnection) -> bool:
        """Check a single service and persist the result in its own transaction."""
        if svc.id is None:
            logger.warning("Service %s has no ID, skipping health check", svc.name)
            return False
        client = None
        try:
            token = self._encryption.decrypt(svc.api_token_encrypted)
            client = self._client_factory.create(svc.service_type, svc.base_url, token)
            result = await client.health_check()

            if result:
                svc.mark_healthy()
            else:
                svc.mark_unhealthy()
        except ServiceConnectionError:
            svc.mark_unhealthy()
            result = False
        except Exception:
            logger.exception("Unexpected error checking %s", svc.name)
            svc.mark_unhealthy()
            result = False
        finally:
            if client is not None:
                await client.close()

        prev_failures = self._failure_counts.get(svc.id, 0)
        if result:
            if prev_failures > 0:
                logger.info(
                    "Service %s recovered after %d consecutive failures, exiting backoff",
                    svc.name,
                    prev_failures,
                )
            self._failure_counts[svc.id] = 0
        else:
            self._failure_counts[svc.id] = prev_failures + 1
            new_backoff = min(2 ** self._failure_counts[svc.id], self._MAX_BACKOFF)
            if prev_failures == 0:
                logger.info(
                    "Service %s entering backoff (next check in ~%d cycles)",
                    svc.name,
                    new_backoff,
                )

        try:
            async with self._session_factory() as session:
                repo = self._make_repo(session)
                await repo.update(svc)
                await session.commit()
        except Exception:
            logger.exception("Failed to persist health status for %s", svc.name)

        return result
