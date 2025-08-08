from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str  # asumimos que la contraseña se envía al crear

class UserOut(BaseModel):
    id: int
    email: EmailStr
    username: str
    is_active: bool

    class Config:
        orm_mode = True  # permite usar objetos SQLAlchemy
