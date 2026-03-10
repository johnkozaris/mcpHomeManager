"""Tests for Settings encryption key and database URL resolution."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest
from cryptography.fernet import Fernet

import config as config_mod


def _make_settings(
    tmp_path: Path,
    env: dict[str, str] | None = None,
    *,
    db_path: Path | None = None,
) -> config_mod.Settings:
    """Build a Settings instance with _KEY_PATH pointed at tmp_path."""
    key_path = tmp_path / "encryption_key"
    # Point _DEFAULT_DB_PATH to a non-existent dir so tests get the dev SQLite URL
    effective_db_path = db_path or (tmp_path / "nonexistent" / "mcp_home.db")
    combined_env = {"ENCRYPTION_KEY": "", "DATABASE_URL": "", **(env or {})}

    with (
        patch.dict(os.environ, combined_env, clear=False),
        patch.object(config_mod, "_KEY_PATH", key_path),
        patch.object(config_mod, "_DEFAULT_DB_PATH", effective_db_path),
    ):
        return config_mod.Settings(
            _env_file=None,  # type: ignore[call-arg]
        )


class TestEncryptionKeyAutoGen:
    def test_generates_key_when_empty(self, tmp_path: Path) -> None:
        s = _make_settings(tmp_path)
        assert s.encryption_key
        Fernet(s.encryption_key.encode())

    def test_persists_key_to_file(self, tmp_path: Path) -> None:
        s = _make_settings(tmp_path)
        key_file = tmp_path / "encryption_key"
        assert key_file.exists()
        assert key_file.read_text(encoding="utf-8") == s.encryption_key

    def test_reads_existing_key_file(self, tmp_path: Path) -> None:
        key = Fernet.generate_key().decode()
        key_file = tmp_path / "encryption_key"
        key_file.write_text(key, encoding="utf-8")

        s = _make_settings(tmp_path)
        assert s.encryption_key == key

    def test_empty_key_file_raises(self, tmp_path: Path) -> None:
        key_file = tmp_path / "encryption_key"
        key_file.write_text("", encoding="utf-8")

        with pytest.raises(ValueError, match="exists but is empty"):
            _make_settings(tmp_path)

    def test_env_var_takes_precedence(self, tmp_path: Path) -> None:
        key = Fernet.generate_key().decode()
        s = _make_settings(tmp_path, env={"ENCRYPTION_KEY": key})
        assert s.encryption_key == key
        assert not (tmp_path / "encryption_key").exists()


class TestFileSecrets:
    def test_encryption_key_file_pattern(self, tmp_path: Path) -> None:
        key = Fernet.generate_key().decode()
        secret_file = tmp_path / "secret_key"
        secret_file.write_text(key, encoding="utf-8")

        s = _make_settings(tmp_path, env={"ENCRYPTION_KEY_FILE": str(secret_file)})
        assert s.encryption_key == key

    def test_database_url_file_pattern(self, tmp_path: Path) -> None:
        db_url = "postgresql+asyncpg://user:pass@host:5432/db"
        secret_file = tmp_path / "db_url"
        secret_file.write_text(db_url, encoding="utf-8")

        key = Fernet.generate_key().decode()
        s = _make_settings(
            tmp_path,
            env={"DATABASE_URL_FILE": str(secret_file), "ENCRYPTION_KEY": key},
        )
        assert s.database_url == db_url

    def test_file_missing_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="does not exist"):
            _make_settings(
                tmp_path,
                env={"ENCRYPTION_KEY_FILE": str(tmp_path / "nonexistent")},
            )

    def test_file_empty_raises(self, tmp_path: Path) -> None:
        secret_file = tmp_path / "empty_secret"
        secret_file.write_text("  \n  ", encoding="utf-8")

        with pytest.raises(ValueError, match="exists but is empty"):
            _make_settings(tmp_path, env={"ENCRYPTION_KEY_FILE": str(secret_file)})

    def test_postgres_password_file_pattern(self, tmp_path: Path) -> None:
        secret_file = tmp_path / "db_pass"
        secret_file.write_text("file-secret\n", encoding="utf-8")

        key = Fernet.generate_key().decode()
        s = _make_settings(
            tmp_path,
            env={"POSTGRES_PASSWORD_FILE": str(secret_file), "ENCRYPTION_KEY": key},
        )
        assert s.postgres_password == "file-secret"
        assert "file-secret" in s.database_url


class TestDatabaseUrlFromParts:
    def test_builds_url_from_postgres_parts(self, tmp_path: Path) -> None:
        key = Fernet.generate_key().decode()
        s = _make_settings(
            tmp_path,
            env={
                "ENCRYPTION_KEY": key,
                "POSTGRES_PASSWORD": "s3cret",
                "POSTGRES_USER": "myuser",
                "POSTGRES_HOST": "myhost",
                "POSTGRES_PORT": "5433",
                "POSTGRES_DB": "mydb",
            },
        )
        assert s.database_url == "postgresql+asyncpg://myuser:s3cret@myhost:5433/mydb"

    def test_url_encodes_special_chars(self, tmp_path: Path) -> None:
        key = Fernet.generate_key().decode()
        s = _make_settings(
            tmp_path,
            env={
                "ENCRYPTION_KEY": key,
                "POSTGRES_PASSWORD": "p@ss:word/here",
                "POSTGRES_USER": "user@name",
            },
        )
        assert "p%40ss%3Aword%2Fhere" in s.database_url
        assert "user%40name" in s.database_url

    def test_explicit_database_url_takes_precedence(self, tmp_path: Path) -> None:
        key = Fernet.generate_key().decode()
        url = "postgresql+asyncpg://custom:url@somewhere:5432/other"
        s = _make_settings(
            tmp_path,
            env={
                "ENCRYPTION_KEY": key,
                "DATABASE_URL": url,
                "POSTGRES_PASSWORD": "ignored",
            },
        )
        assert s.database_url == url

    def test_dev_default_when_no_password(self, tmp_path: Path) -> None:
        key = Fernet.generate_key().decode()
        s = _make_settings(tmp_path, env={"ENCRYPTION_KEY": key})
        assert s.database_url == config_mod._DEV_DB_URL

    def test_defaults_with_only_password(self, tmp_path: Path) -> None:
        """Minimal Docker config: user only sets POSTGRES_PASSWORD."""
        key = Fernet.generate_key().decode()
        s = _make_settings(tmp_path, env={"ENCRYPTION_KEY": key, "POSTGRES_PASSWORD": "s3cret"})
        # Should use all defaults: db:5432, mcp user, mcp_home database
        assert s.database_url == "postgresql+asyncpg://mcp:s3cret@db:5432/mcp_home"

    def test_partial_overrides(self, tmp_path: Path) -> None:
        """User overrides DB name but keeps default user and host."""
        key = Fernet.generate_key().decode()
        s = _make_settings(
            tmp_path,
            env={
                "ENCRYPTION_KEY": key,
                "POSTGRES_PASSWORD": "s3cret",
                "POSTGRES_DB": "custom_db",
            },
        )
        assert s.database_url == "postgresql+asyncpg://mcp:s3cret@db:5432/custom_db"

    def test_is_sqlite_true_by_default(self, tmp_path: Path) -> None:
        key = Fernet.generate_key().decode()
        s = _make_settings(tmp_path, env={"ENCRYPTION_KEY": key})
        assert s.is_sqlite is True

    def test_is_sqlite_false_for_postgres(self, tmp_path: Path) -> None:
        key = Fernet.generate_key().decode()
        s = _make_settings(
            tmp_path,
            env={"ENCRYPTION_KEY": key, "POSTGRES_PASSWORD": "s3cret"},
        )
        assert s.is_sqlite is False

    def test_sqlite_uses_data_dir_in_docker(self, tmp_path: Path) -> None:
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        db_path = data_dir / "mcp_home.db"
        key = Fernet.generate_key().decode()
        s = _make_settings(tmp_path, env={"ENCRYPTION_KEY": key}, db_path=db_path)
        assert s.database_url == f"sqlite+aiosqlite:///{db_path}"

    def test_secrets_hidden_from_repr(self, tmp_path: Path) -> None:
        key = Fernet.generate_key().decode()
        s = _make_settings(
            tmp_path,
            env={"ENCRYPTION_KEY": key, "POSTGRES_PASSWORD": "secret"},
        )
        r = repr(s)
        assert key not in r
        assert "secret" not in r
        assert "database_url" not in r
        assert "encryption_key" not in r
        assert "postgres_password" not in r
