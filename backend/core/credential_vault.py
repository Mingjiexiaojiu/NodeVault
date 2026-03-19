"""AES-256-GCM credential vault — encrypt / decrypt sensitive values."""

from __future__ import annotations

import base64
import binascii
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

_key: bytes | None = None


class CredentialVaultError(Exception):
    """Raised when the credential vault cannot operate."""


def _load_key() -> bytes:
    global _key
    if _key is not None:
        return _key

    raw = os.environ.get("CREDENTIAL_ENCRYPT_KEY", "")
    if not raw:
        raise CredentialVaultError(
            "CREDENTIAL_ENCRYPT_KEY is not set. "
            "Cannot encrypt/decrypt credentials."
        )

    # Try hex (64 chars → 32 bytes)
    try:
        decoded = binascii.unhexlify(raw)
        if len(decoded) == 32:
            _key = decoded
            return _key
    except (ValueError, binascii.Error):
        pass

    # Try base64 (44 chars → 32 bytes)
    try:
        decoded = base64.b64decode(raw, validate=True)
        if len(decoded) == 32:
            _key = decoded
            return _key
    except Exception:
        pass

    raise CredentialVaultError(
        f"CREDENTIAL_ENCRYPT_KEY is invalid (got {len(raw)} chars). "
        "Provide exactly 32 bytes as 64-char hex or 44-char base64."
    )


def encrypt_value(plaintext: str) -> tuple[bytes, bytes]:
    """Encrypt *plaintext* with AES-256-GCM.

    Returns ``(ciphertext, nonce)`` — both raw ``bytes``.
    """
    key = _load_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)  # 96-bit nonce for GCM
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    return ciphertext, nonce


def decrypt_value(ciphertext: bytes, nonce: bytes) -> str:
    """Decrypt AES-256-GCM *ciphertext* back to a string."""
    key = _load_key()
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return plaintext.decode("utf-8")


def reset_key() -> None:
    """Clear the cached key (for testing)."""
    global _key
    _key = None
