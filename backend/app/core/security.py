import secrets
from datetime import UTC, datetime, timedelta
from hashlib import sha256

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

password_hasher = PasswordHasher()


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return password_hasher.verify(password_hash, password)
    except (InvalidHashError, VerificationError, VerifyMismatchError):
        return False


def new_opaque_token() -> str:
    return secrets.token_urlsafe(32)


def digest_token(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()


def session_expiry(hours: int, now: datetime) -> datetime:
    return now + timedelta(hours=hours)
