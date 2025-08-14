from fastapi import APIRouter, HTTPException, Request
from models.catalogs import Catalog
from controllers.catalogs import (
    create_catalog,
    get_catalogs,
    get_catalog_by_id,
    update_catalog,
    deactivate_catalog
)
from utils.security import validateadmin

router = APIRouter()

@router.post("/catalogs", response_model=Catalog, tags=["📋 Catalogs"])
@validateadmin
async def create_catalog_endpoint(request: Request, catalog: Catalog) -> Catalog:
    """Crear un nuevo catálogo"""
    return await create_catalog(catalog)

@router.get("/catalogs", response_model=dict, tags=["📋 Catalogs"])
async def get_catalogs_endpoint() -> dict:
    """Obtener todos los catálogos"""
    return await get_catalogs()

@router.get("/catalogs/{catalog_id}", response_model=Catalog, tags=["📋 Catalogs"])
async def get_catalog_by_id_endpoint(catalog_id: str) -> Catalog:
    """Obtener un catálogo por ID"""
    return await get_catalog_by_id(catalog_id)

@router.put("/catalogs/{catalog_id}", response_model=Catalog, tags=["📋 Catalogs"])
@validateadmin
async def update_catalog_endpoint(request: Request, catalog_id: str, catalog: Catalog) -> Catalog:
    """Actualizar un catálogo"""
    return await update_catalog(catalog_id, catalog)

@router.delete("/catalogs/{catalog_id}", response_model=Catalog, tags=["📋 Catalogs"])
@validateadmin
async def deactivate_catalog_endpoint(request: Request,catalog_id: str) -> Catalog:
    """Desactivar un catálogo"""
    return await deactivate_catalog(catalog_id)
