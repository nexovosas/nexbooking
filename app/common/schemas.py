from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

class ErrorResponse(BaseModel):
    """Formato estándar para errores HTTP no 2xx."""
    model_config = ConfigDict(extra="allow")  # Permite campos adicionales si se necesitan
    type: str = Field(examples=["about:blank"])       # categoría o URI del error
    title: str = Field(examples=["Not Found"])        # título corto y claro
    status: int = Field(examples=[404])               # código HTTP
    detail: Optional[str] = Field(
        default=None,
        examples=["Accommodation not found"]
    ) 
    instance: Optional[str] = Field(
        default=None,
        examples=["/api/v1/accommodations/123"]
    )
