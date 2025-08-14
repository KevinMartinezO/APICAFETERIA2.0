from fastapi import APIRouter, HTTPException, Request
from models.bundle_details import BundleWithProducts, AddProductToBundle
from controllers.bundle_details import (
    get_bundle_with_products,
    add_product_to_bundle,
    remove_product_from_bundle
)
from utils.security import validateadmin

router = APIRouter()

@router.get("/bundle/{bundle_id}", response_model=BundleWithProducts, tags=["🎁 Bundle Details"])
async def get_bundle_with_products_endpoint(bundle_id: str) -> BundleWithProducts:
    """Obtener información completa del bundle con todos sus productos"""
    return await get_bundle_with_products(bundle_id)

@router.post("/bundles/{bundle_id}/product", tags=["🎁 Bundle Details"])
@validateadmin
async def add_product_to_bundle_endpoint(
    bundle_id: str, 
    product_data: AddProductToBundle,
    request: Request
) -> dict:
    """Agregar un producto al bundle (requiere permisos de admin)"""
    return await add_product_to_bundle(bundle_id, product_data)

@router.delete("/bundles/{bundle_id}/product/{bundle_detail_id}", tags=["🎁 Bundle Details"])
@validateadmin
async def remove_product_from_bundle_endpoint(
    bundle_id: str, 
    bundle_detail_id: str,
    request: Request
) -> dict:
    """Remover un producto del bundle (requiere permisos de admin)"""
    return await remove_product_from_bundle(bundle_id, bundle_detail_id)
