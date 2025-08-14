from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class OrderDetail(BaseModel):
    id: Optional[str] = Field(
        default=None,
        description="MongoDB ID - Se genera automáticamente desde el _id de MongoDB"
    )

    id_order: str = Field(
        description="ID de la orden",
        examples=["507f1f77bcf86cd799439011"]
    )

    id_producto: str = Field(
        description="ID del producto",
        examples=["507f1f77bcf86cd799439012"]
    )

    date_created: datetime = Field(
        default_factory=datetime.utcnow,
        description="Fecha de creación del detalle"
    )

    date_updated: datetime = Field(
        default_factory=datetime.utcnow,
        description="Fecha de última actualización"
    )

    quantity: int = Field(
        description="Cantidad del producto",
        gt=0,
        examples=[1, 2, 5]
    )

    active: bool = Field(
        default=True,
        description="Si el detalle está activo"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id_order": "507f1f77bcf86cd799439011",
                "id_producto": "507f1f77bcf86cd799439012",
                "quantity": 2,
                "active": True
            }
        }

class CreateOrderDetail(BaseModel):
    """Modelo para crear un detalle de orden"""
    id_producto: str = Field(
        description="ID del producto",
        examples=["507f1f77bcf86cd799439012"]
    )
    
    quantity: int = Field(
        description="Cantidad del producto",
        gt=0,
        examples=[1, 2, 5]
    )

class UpdateOrderDetail(BaseModel):
    """Modelo para actualizar cantidad de un detalle"""
    quantity: int = Field(
        description="Nueva cantidad del producto",
        gt=0,
        examples=[1, 2, 5]
    )
