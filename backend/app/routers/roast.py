from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, field_validator

from app.limiter import check_rate_limit, get_user_email_from_request
from app.middleware.auth import get_current_user
from app.services.roaster import roast_code

router = APIRouter(tags=["roast"])


# ─── Request / Response schemas ───────────────────────────────────────────────
class RoastRequest(BaseModel):
    code: str
    language: str = "auto"

    @field_validator("code")
    @classmethod
    def code_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Code cannot be empty")
        if len(v) > 5000:
            raise ValueError("Code must be under 5000 characters")
        return v


class RoastResponse(BaseModel):
    roast: str  # the funny part
    feedback: str  # the actually useful part
    rating: int  # code quality rating 1–10


# ─── Route ───────────────────────────────────────────────────────────────────
@router.post("/roast", response_model=RoastResponse)
async def roast(
    request: Request,
    body: RoastRequest,
    current_user: dict = Depends(get_current_user),
):
    # Rate limit: 2 roasts per hour per user
    email = get_user_email_from_request(request)
    await check_rate_limit(
        key=f"roast:{email}",
        limit=2,
        window_seconds=3600,  # 1 hour
    )

    try:
        result = await roast_code(body.code, body.language)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
