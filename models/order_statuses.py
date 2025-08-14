from pydantic import BaseModel, Field
from typing import Optional

class OrderStatus(BaseModel):
    id: Optional[str] = Field(
        default=None,
        description="MongoDB ID - Se genera automáticamente desde el _id de MongoDB, no es necesario enviarlo en POST"
    )

    description: str = Field(
        description="Descripción del estado del pedido",
        min_length=2,
        max_length=50,
        pattern=r"^[a-zA-Z0-9\s\-_]+$",  # Solo letras, números, espacios, guiones y guiones bajos
        examples=["ordered", "pending", "processing", "shipped", "delivered", "cancelled"]
    )