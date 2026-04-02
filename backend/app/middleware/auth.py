from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.database import get_db
from app.services.auth import decode_access_token

# Extracts "Bearer <token>" from the Authorization header automatically
bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db=Depends(get_db),
) -> dict:
    """
    FastAPI dependency — add this to any route to protect it.

    Checks:
    1. Authorization header exists and has a Bearer token
    2. Token is valid and not expired
    3. User still exists in the database

    Usage:
        @router.get("/me")
        async def me(user = Depends(get_current_user)):
            return user
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Decode the token → get the email
    email = decode_access_token(credentials.credentials)
    if not email:
        raise credentials_exception

    # Check the user still exists in the DB
    user = await db["users"].find_one({"email": email})
    if not user:
        raise credentials_exception

    return user
