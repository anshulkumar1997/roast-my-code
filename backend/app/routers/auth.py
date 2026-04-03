from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, field_validator

from app.database import get_db
from app.limiter import check_rate_limit
from app.middleware.auth import get_current_user
from app.services.auth import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])

# bcrypt hard limit — passwords longer than this are silently truncated
# We reject them explicitly so users aren't confused
BCRYPT_MAX_BYTES = 72


# ── Schemas ───────────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if len(v.encode("utf-8")) > BCRYPT_MAX_BYTES:
            raise ValueError("Password must be under 72 bytes")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── Register ──────────────────────────────────────────────────────


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(request: Request, body: RegisterRequest, db=Depends(get_db)):
    # Rate limit by IP for register/login (user not authenticated yet)
    ip = request.client.host if request.client else "unknown"
    await check_rate_limit(key=f"register:{ip}", limit=3, window_seconds=60)

    existing = await db["users"].find_one({"email": body.email})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    if len(body.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters",
        )

    user_doc = {
        "email": body.email,
        "hashed_password": hash_password(body.password),
        "is_active": True,
    }
    await db["users"].insert_one(user_doc)

    token = create_access_token({"sub": body.email})
    return TokenResponse(access_token=token)


# ── Login ─────────────────────────────────────────────────────────
@router.post("/login", response_model=TokenResponse)
async def login(request: Request, body: LoginRequest, db=Depends(get_db)):
    # Rate limit login attempts by IP
    ip = request.client.host if request.client else "unknown"
    await check_rate_limit(key=f"login:{ip}", limit=5, window_seconds=60)

    user = await db["users"].find_one({"email": body.email})

    auth_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password",
    )

    if not user or not verify_password(body.password, user["hashed_password"]):
        raise auth_error

    token = create_access_token({"sub": body.email})
    return TokenResponse(access_token=token)


# ── Me — protected route ──────────────────────────────────────────
@router.get("/me")
async def me(current_user: dict = Depends(get_current_user)):
    """Only reachable with a valid JWT token in the Authorization header."""
    return {
        "email": current_user["email"],
        "is_active": current_user["is_active"],
    }
