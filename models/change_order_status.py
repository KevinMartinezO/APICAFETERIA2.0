from pydantic import BaseModel, Field

class ChangeOrderStatus(BaseModel):
    """Modelo simplificado para cambiar estado de orden (solo id_status)"""
    id_status: str = Field(
        description="ID del estado a asignar",
        examples=["507f1f77bcf86cd799439012"]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id_status": "507f1f77bcf86cd799439012"
            }
        }
