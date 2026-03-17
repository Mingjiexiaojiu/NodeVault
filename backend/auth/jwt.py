from datetime import datetime, timedelta

import bcrypt
from jose import JWTError, jwt

from backend.core.config import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.jwt_access_token_expire_minutes)
    )
    payload = {"sub": subject, "exp": expire, "iat": datetime.utcnow()}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
    except JWTError as e:
        raise ValueError(f"Invalid token: {e}") from e
