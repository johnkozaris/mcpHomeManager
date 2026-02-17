"""Tests for Fernet encryption implementation."""

import pytest
from cryptography.fernet import Fernet

from domain.exceptions import EncryptionError
from infrastructure.encryption.fernet_encryption import FernetEncryption


class TestFernetEncryption:
    @pytest.fixture
    def valid_key(self) -> str:
        return Fernet.generate_key().decode()

    @pytest.fixture
    def encryption(self, valid_key: str) -> FernetEncryption:
        return FernetEncryption(valid_key)

    def test_encrypt_decrypt_roundtrip(self, encryption: FernetEncryption) -> None:
        plaintext = "my-secret-api-token"
        ciphertext = encryption.encrypt(plaintext)
        assert ciphertext != plaintext
        assert encryption.decrypt(ciphertext) == plaintext

    def test_encrypt_produces_different_ciphertexts(self, encryption: FernetEncryption) -> None:
        """Fernet includes a timestamp, so same plaintext produces different ciphertexts."""
        c1 = encryption.encrypt("same")
        c2 = encryption.encrypt("same")
        assert c1 != c2  # different due to timestamp/IV

    def test_decrypt_with_wrong_key_raises(self, valid_key: str) -> None:
        enc1 = FernetEncryption(valid_key)
        ciphertext = enc1.encrypt("secret")

        other_key = Fernet.generate_key().decode()
        enc2 = FernetEncryption(other_key)
        with pytest.raises(EncryptionError, match="Failed to decrypt"):
            enc2.decrypt(ciphertext)

    def test_decrypt_garbage_raises(self, encryption: FernetEncryption) -> None:
        with pytest.raises(EncryptionError, match="Failed to decrypt"):
            encryption.decrypt("not-valid-fernet-token")

    def test_empty_key_raises(self) -> None:
        with pytest.raises(EncryptionError, match="ENCRYPTION_KEY is required"):
            FernetEncryption("")

    def test_invalid_key_raises(self) -> None:
        with pytest.raises(EncryptionError, match="Invalid Fernet key"):
            FernetEncryption("not-a-valid-base64-key")

    def test_empty_plaintext(self, encryption: FernetEncryption) -> None:
        ciphertext = encryption.encrypt("")
        assert encryption.decrypt(ciphertext) == ""

    def test_unicode_plaintext(self, encryption: FernetEncryption) -> None:
        plaintext = "p\u00e4ssw\u00f6rd-with-\u00fcnic\u00f6de"
        assert encryption.decrypt(encryption.encrypt(plaintext)) == plaintext
