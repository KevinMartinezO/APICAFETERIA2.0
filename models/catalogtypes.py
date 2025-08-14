from  pydantic import BaseModel, Field, field_validator
from typing import Optional

class CatalogType(BaseModel):
    id: Optional[str] = Field(
        default=None,
        description="MongoDB ID - Se genera automáticamente desde el _id de MongoDB, no es necesario enviarlo en POST"
    )

    description: str = Field(
        description="Descripción del tipo de catálogo",
        pattern=r"^[0-9A-Za-zÁÉÍÓÚÜÑáéíóúüñ' -]+$",
        examples=["Product","Bundle"]
    )

    active: bool = Field(
        default=True,
        description="Estado activo del tipo de catálogo"
    )