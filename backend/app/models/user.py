from datetime import datetime

from bson import ObjectId
from pydantic import BaseModel, EmailStr, Field


# ── Helper so Pydantic understands MongoDB's ObjectId ─────────────
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, schema):
        schema.update(type="string")
        return schema


# ── What gets stored in MongoDB ────────────────────────────────────
class UserInDB(BaseModel):
    """Represents a user document as stored in the database."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    email: str
    hashed_password: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"arbitrary_types_allowed": True, "populate_by_name": True}


# ── What we return to the client (never expose hashed_password) ────
class UserResponse(BaseModel):
    """Safe user shape returned in API responses."""
    id: str
    email: str
    is_active: bool
    created_at: datetime
