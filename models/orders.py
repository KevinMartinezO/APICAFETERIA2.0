from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class Order(BaseModel):
    id: Optional[str] = Field(
        default=None,
        description="MongoDB ID - Se genera automáticamente desde el _id de MongoDB"
    )

    id_user: str = Field(
        description="ID del usuario que realizó la orden",
        examples=["507f1f77bcf86cd799439011"]
    )

    date: datetime = Field(
        default_factory=datetime.utcnow,
        description="Fecha de creación de la orden"
    )

    subtotal: float = Field(
        description="Subtotal de la orden",
        gt=0,
        examples=[150.50, 99.99]
    )

    taxes: float = Field(
        description="Impuestos de la orden",
        ge=0,
        examples=[15.05, 9.99]
    )

    discount: float = Field(
        default=0.0,
        description="Descuento aplicado a la orden",
        ge=0,
        examples=[0.0, 10.50]
    )

    total: float = Field(
        description="Total de la orden (subtotal + taxes - discount)",
        gt=0,
        examples=[165.55, 109.98]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "subtotal": 150.50,
                "taxes": 15.05,
                "discount": 10.00,
                "total": 155.55
            }
        }

class CreateOrder(BaseModel):
    """Modelo para crear una orden - las órdenes se crean vacías"""
    pass  # No necesita campos, todo se calcula automáticamente

    class Config:
        json_schema_extra = {
            "example": {}
        }
