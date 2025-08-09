# app/booking/schemas/user_schema.py
from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing_extensions import Annotated


# ---------- Create ----------
class UserCreate(BaseModel):
    email: Annotated[EmailStr, Field(description="Valid email address of the user")]
    username: Annotated[str, Field(min_length=3, max_length=50, description="Unique username")]
    password: Annotated[str, Field(min_length=8, max_length=128, description="Plain text password (will be hashed)")]


# ---------- Output ----------
class UserOut(BaseModel):
    id: int
    email: Annotated[EmailStr, Field(description="Email address of the user")]
    username: Annotated[str, Field(description="Unique username")]
    is_active: bool

    model_config = ConfigDict(from_attributes=True)  # Pydantic v2 replacement for orm_mode
