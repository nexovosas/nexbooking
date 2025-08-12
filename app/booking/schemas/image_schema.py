from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from typing_extensions import Annotated

class ImageCreate(BaseModel):
    # Este schema ya no se usará para subir archivo.
    # Lo mantenemos opcional por compatibilidad (alt_text únicamente).
    alt_text: Annotated[Optional[str], Field(default=None, max_length=255)]

class ImageOut(BaseModel):
    id: int
    # Guardaremos la KEY de S3 aquí (o una URL definitiva si cambias la estrategia)
    url: Annotated[str, Field(description="S3 object key or final URL")]
    room_id: Optional[int] = None
    accommodation_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)
