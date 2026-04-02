import os
from datetime import datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext

# ── Password hashing ──────────────────────────────────────────────
# bcrypt is the industry standard — slow by design (harder to brute force)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    """Turn 'mysecret' into '$2b$12$...' — never reversible."""
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Check if a plain password matches the stored hash."""
    return pwd_context.verify(plain, hashed)


# ── JWT tokens ────────────────────────────────────────────────────
JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "30"))


def create_access_token(data: dict) -> str:
    """
    Create a signed JWT token.

    data = {"sub": "user@example.com"}  ← "sub" = subject (standard JWT field)
    The token encodes who the user is + when it expires.
    Anyone with the JWT_SECRET can verify it — keep that secret safe.
    """
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES)
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> str | None:
    """
    Verify and decode a JWT token.
    Returns the user's email if valid, None if expired or tampered.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload.get("sub")  # the email we stored
    except JWTError:
        return None
