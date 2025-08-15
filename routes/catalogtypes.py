from fastapi import APIRouter, Request
from models.catalogtypes import CatalogType
from controllers.catalogtypes import (
    create_catalog_type,
    get_catalog_types,
    get_catalog_type_by_id,
    update_catalog_type,
    deactivate_catalog_type
)
from utils.security import validateadmin

router = APIRouter()

@router.post("/catalogtypes", response_model=CatalogType, tags=["📂 Catalog Types"])
@validateadmin
async def create_catalog_type_endpoint(request: Request, catalog_type: CatalogType) -> CatalogType:
    return await create_catalog_type(catalog_type)

@router.get("/catalogtypes", response_model=list[CatalogType], tags=["📂 Catalog Types"])
@validateadmin
async def get_catalog_types_endpoint(request: Request, ) -> list[CatalogType]:
    return await get_catalog_types()

@router.get("/catalogtypes/{catalog_type_id}", response_model=CatalogType, tags=["📂 Catalog Types"])
@validateadmin
async def get_catalog_type_by_id_endpoint(request: Request, catalog_type_id: str) -> CatalogType:
    return await get_catalog_type_by_id(catalog_type_id)

@router.put("/catalogtypes/{catalog_type_id}", response_model=CatalogType, tags=["📂 Catalog Types"])
@validateadmin
async def update_catalog_type_endpoint(request: Request, catalog_type_id: str, catalog_type: CatalogType) -> CatalogType:
    return await update_catalog_type(catalog_type_id, catalog_type)

@router.delete("/catalogtypes/{catalog_type_id}", response_model=CatalogType, tags=["📂 Catalog Types"])
@validateadmin
async def deactivate_catalog_type_endpoint(request: Request, catalog_type_id: str) -> CatalogType:
    return await deactivate_catalog_type(catalog_type_id)


