from cryptography.fernet import Fernet, InvalidToken

from domain.exceptions import EncryptionError
from domain.ports.encryption import IEncryptionPort


class FernetEncryption(IEncryptionPort):
    def __init__(self, key: str) -> None:
        if not key:
            raise EncryptionError(
                "ENCRYPTION_KEY is required. Generate one with: "
                'python -c "from cryptography.fernet import Fernet; '
                'print(Fernet.generate_key().decode())"'
            )
        try:
            self._fernet = Fernet(key.encode() if isinstance(key, str) else key)
        except (ValueError, Exception) as e:
            raise EncryptionError(f"Invalid Fernet key: {e}") from e

    def encrypt(self, plaintext: str) -> str:
        return self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        try:
            return self._fernet.decrypt(ciphertext.encode()).decode()
        except InvalidToken as e:
            raise EncryptionError("Failed to decrypt: invalid token or wrong key") from e
