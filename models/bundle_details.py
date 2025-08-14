from pydantic import BaseModel, Field, field_validator
from typing import Optional

class BundleDetail(BaseModel):
    id: Optional[str] = Field(
        default=None,
        description="MongoDB ID - Se genera automáticamente desde el _id de MongoDB, no es necesario enviarlo en POST"
    )

    id_bundle: str = Field(
        description="ID del bundle (equivalente a id_product cuando el tipo es bundle)",
        examples=["507f1f77bcf86cd799439011"]
    )

    id_producto: str = Field(
        description="ID del producto que forma parte del bundle",
        examples=["507f1f77bcf86cd799439012"]
    )

    quantity: int = Field(
        description="Cantidad del producto en el bundle",
        gt=0,
        examples=[1, 2, 5]
    )

    @field_validator('quantity')
    @classmethod
    def validate_quantity(cls, value: int):
        if value <= 0:
            raise ValueError("La cantidad debe ser mayor a 0")
        return value

# Modelo para la respuesta del bundle completo con productos
class BundleWithProducts(BaseModel):
    id: str = Field(description="ID del bundle")
    id_catalog_type: str = Field(description="ID del tipo de catálogo")
    name: str = Field(description="Nombre del bundle")
    description: str = Field(description="Descripción del bundle")
    cost: float = Field(description="Costo del bundle")
    discount: int = Field(description="Descuento del bundle")
    active: bool = Field(description="Estado activo del bundle")
    products: list[dict] = Field(description="Lista de productos en el bundle")

# Modelo para agregar producto a bundle
class AddProductToBundle(BaseModel):
    id_producto: str = Field(
        description="ID del producto a agregar al bundle",
        examples=["507f1f77bcf86cd799439012"]
    )

    quantity: int = Field(
        description="Cantidad del producto a agregar",
        gt=0,
        examples=[1, 2, 5]
    )

    @field_validator('quantity')
    @classmethod
    def validate_quantity(cls, value: int):
        if value <= 0:
            raise ValueError("La cantidad debe ser mayor a 0")
        return value
