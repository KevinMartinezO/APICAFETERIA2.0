from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class OrderStatusRecord(BaseModel):
    """Modelo para un registro de cambio de estado de orden (colección order_status)"""
    id: Optional[str] = Field(
        default=None,
        description="MongoDB ID - Se genera automáticamente desde el _id de MongoDB"
    )
    
    id_order: str = Field(
        description="ID de la orden",
        examples=["507f1f77bcf86cd799439011"]
    )
    
    id_status: str = Field(
        description="ID del estado (referencia a order_statuses)",
        examples=["507f1f77bcf86cd799439012"]
    )
    
    date: datetime = Field(
        default_factory=datetime.utcnow,
        description="Fecha del cambio de estado"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id_order": "507f1f77bcf86cd799439011",
                "id_status": "507f1f77bcf86cd799439012"
            }
        }

class CreateOrderStatusRecord(BaseModel):
    """Modelo para crear un registro de cambio de estado de orden"""
    id_order: str = Field(
        description="ID de la orden",
        examples=["507f1f77bcf86cd799439011"]
    )
    
    id_status: str = Field(
        description="ID del estado",
        examples=["507f1f77bcf86cd799439012"]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id_order": "507f1f77bcf86cd799439011",
                "id_status": "507f1f77bcf86cd799439012"
            }
        }
