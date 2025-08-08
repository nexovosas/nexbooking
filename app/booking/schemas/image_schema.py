from pydantic import BaseModel
from typing import Optional

class ImageCreate(BaseModel):
    url: str
    alt_text: Optional[str] = None
    
class ImageOut(BaseModel):
    id: int
    url: str
    room_id: Optional[int] = None
    accommodation_id: Optional[int] = None

    class Config:
        orm_mode = True
