# app/booking/schemas/user_schema.py
from __future__ import annotations
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing_extensions import Annotated

# ---------- Create ----------
class UserCreate(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "examples": [
            {
                "email": "user@example.com",
                "username": "john_doe",
                "password": "StrongP@ssw0rd"
            }
        ]
    })
    email: Annotated[
        EmailStr,
        Field(
            description="Valid email address of the user",
            examples=["user@example.com"]
        )
    ]
    username: Annotated[
        str,
        Field(
            min_length=3,
            max_length=50,
            description="Unique username",
            examples=["john_doe"]
        )
    ]
    password: Annotated[
        str,
        Field(
            min_length=8,
            max_length=128,
            description="Plain text password (will be hashed)",
            examples=["StrongP@ssw0rd"]
        )
    ]


# ---------- Output ----------
class UserOut(BaseModel):
    id: int
    email: Annotated[
        EmailStr,
        Field(
            description="Email address of the user",
            examples=["user@example.com"]
        )
    ]
    username: Annotated[
        str,
        Field(
            description="Unique username",
            examples=["john_doe"]
        )
    ]
    is_active: Annotated[
        bool,
        Field(
            description="Indicates whether the user is active",
            examples=[True]
        )
    ]

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 1,
                    "email": "user@example.com",
                    "username": "john_doe",
                    "is_active": True
                }
            ]
        }
    )
