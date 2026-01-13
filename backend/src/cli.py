"""CLI commands for administrative tasks.

Usage (Docker):
    docker compose exec app uv run mcp-home-reset-password [username]

Usage (local):
    uv run mcp-home-reset-password [username]
"""

import asyncio
import getpass
import sys

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from config import settings
from infrastructure.persistence.user_repository import UserRepository
from services.user_service import UserService


async def _reset_admin_password() -> None:
    username = sys.argv[1] if len(sys.argv) > 1 else None

    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with session_factory() as session:
            repo = UserRepository(session)

            if username:
                user = await repo.get_by_username(username)
            else:
                users = await repo.get_all()
                user = next((u for u in users if u.is_admin), None)

            if user is None:
                if username:
                    print(f"User '{username}' not found.")
                else:
                    print("No admin user found. Run the setup wizard first.")
                sys.exit(1)

            print(f"Resetting password for user: {user.username}")
            new_password = getpass.getpass("New password (min 8 chars): ")
            if len(new_password) < 8:
                print("Password must be at least 8 characters.")
                sys.exit(1)
            confirm = getpass.getpass("Confirm password: ")
            if new_password != confirm:
                print("Passwords do not match.")
                sys.exit(1)

            svc = UserService(repo)
            assert user.id is not None
            await svc.set_password(user.id, new_password)
            await session.commit()
            print(f"Password reset successfully for '{user.username}'.")
    finally:
        await engine.dispose()


def reset_admin_password() -> None:
    """Entry point for mcp-home-reset-password CLI command."""
    asyncio.run(_reset_admin_password())
