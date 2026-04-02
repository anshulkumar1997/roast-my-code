from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, field_validator

from app.database import get_db
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
async def register(request: RegisterRequest, db=Depends(get_db)):
    # Check email not already taken
    existing = await db["users"].find_one({"email": request.email})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    if len(request.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters",
        )

    # Hash password — NEVER store plain text
    user_doc = {
        "email": request.email,
        "hashed_password": hash_password(request.password),
        "is_active": True,
    }
    await db["users"].insert_one(user_doc)

    # Log the user in immediately after registering
    token = create_access_token({"sub": request.email})
    return TokenResponse(access_token=token)


# ── Login ─────────────────────────────────────────────────────────
@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db=Depends(get_db)):
    user = await db["users"].find_one({"email": request.email})

    # Same vague error for wrong email OR wrong password
    # Never tell the caller which one was wrong — leaks user existence
    auth_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password",
    )

    if not user or not verify_password(request.password, user["hashed_password"]):
        raise auth_error

    token = create_access_token({"sub": request.email})
    return TokenResponse(access_token=token)


# ── Me — protected route ──────────────────────────────────────────
@router.get("/me")
async def me(current_user: dict = Depends(get_current_user)):
    """Only reachable with a valid JWT token in the Authorization header."""
    return {
        "email": current_user["email"],
        "is_active": current_user["is_active"],
    }
