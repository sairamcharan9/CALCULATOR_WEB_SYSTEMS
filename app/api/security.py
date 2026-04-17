"""
Password Security & JWT
=======================

Provides password hashing/verification using bcrypt via passlib,
JWT creation/decoding using python-jose, and a FastAPI dependency
for extracting the currently authenticated user from the Bearer token.
"""

import os
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

# ── bcrypt config ──────────────────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(raw_password: str) -> str:
    """Hash a plain-text password using bcrypt."""
    return pwd_context.hash(raw_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


# ── JWT config ────────────────────────────────────────────────────────────
SECRET_KEY: str = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "30"))


def create_access_token(data: dict) -> str:
    """
    Create a signed JWT access token.

    Args:
        data: Payload dict to encode (e.g. {"sub": str(user_id)}).

    Returns:
        Signed JWT string.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    """
    Decode and verify a JWT access token.

    Args:
        token: The JWT string to decode.

    Returns:
        Decoded payload dict.

    Raises:
        JWTError: If the token is invalid or expired.
    """
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


# ── OAuth2 Scheme ─────────────────────────────────────────────────────────
# tokenUrl points to the login endpoint that issues JWT tokens.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login", auto_error=False)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(lambda: None),   # placeholder — real import below
):
    """Placeholder overridden at module level below."""
    ...  # pragma: no cover


def _build_get_current_user():
    """
    Returns the real get_current_user dependency as a closure.
    Defined as a factory to avoid circular imports at import time
    (security.py must not import models.py or database.py at the top level).
    """
    from app.api.database import get_db
    from app.api.models import User

    def _get_current_user(
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db),
    ):
        """
        FastAPI dependency — decodes the Bearer JWT and returns the User ORM object.

        Raises 401 if:
        - No token is present.
        - Token signature is invalid or expired.
        - The user referenced by 'sub' no longer exists in the database.
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Please log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )

        if token is None:
            raise credentials_exception

        try:
            payload = decode_access_token(token)
            user_id_str: str = payload.get("sub")
            if user_id_str is None:
                raise credentials_exception
            user_id = int(user_id_str)
        except (JWTError, ValueError):
            raise credentials_exception

        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise credentials_exception

        return user

    return _get_current_user


# Replace the placeholder with the real implementation.
# Routes import this symbol; the factory pattern avoids circular imports
# while still letting FastAPI propagate DB session overrides through Depends.
get_current_user = _build_get_current_user()
