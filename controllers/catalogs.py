from models.catalogs import Catalog
from models.catalogtypes import CatalogType
from utils.mongodb import get_collection
from fastapi import HTTPException
from bson import ObjectId
from pipelines.catalog_pipelines import (
    validate_catalog_type_pipeline,
    get_catalog_with_type_pipeline,
    get_catalogs_by_type_pipeline,
    get_all_catalogs_with_types_pipeline
)

coll = get_collection("catalogs")
catalog_types_coll = get_collection("catalogtypes")

async def create_catalog(catalog: Catalog) -> Catalog:
    try:

        # Validar que el catalog_type existe y está activo usando pipeline
        catalog_type_pipeline = validate_catalog_type_pipeline(catalog.id_catalog_type)
        catalog_type_result = list(catalog_types_coll.aggregate(catalog_type_pipeline))

        if not catalog_type_result:
            raise HTTPException(status_code=400, detail="Catalog type not found or inactive")

        catalog.name = catalog.name.strip()
        catalog.description = catalog.description.strip()

        # Verificar si ya existe un catálogo con el mismo nombre
        existing_catalog = coll.find_one({"name": {"$regex": f"^{catalog.name}$", "$options": "i"}})
        if existing_catalog:
            raise HTTPException(status_code=400, detail="Catalog with this name already exists")

        catalog_dict = catalog.model_dump(exclude={"id"})
        inserted = coll.insert_one(catalog_dict)
        catalog.id = str(inserted.inserted_id)
        return catalog
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating catalog: {str(e)}")

async def get_catalogs() -> list[Catalog]:
    try:
        catalogs = []
        for doc in coll.find():
            # Mapear _id a id para el modelo Pydantic
            doc['id'] = str(doc['_id'])
            del doc['_id']
            catalog = Catalog(**doc)
            catalogs.append(catalog)
        return catalogs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching catalogs: {str(e)}")

async def get_catalogs(skip: int = 0, limit: int = 10) -> dict:
    try:
        # Usar pipeline optimizada para obtener catálogos con información del tipo
        pipeline = get_all_catalogs_with_types_pipeline(skip, limit)
        catalogs = list(coll.aggregate(pipeline))

        # Contar total de documentos para paginación
        total_count = coll.count_documents({"active": True})

        return {
            "catalogs": catalogs,
            "total": total_count,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching catalogs: {str(e)}")

async def get_catalog_by_id(catalog_id: str) -> dict:
    try:
        # Usar pipeline para obtener catálogo con información del tipo
        pipeline = get_catalog_with_type_pipeline(catalog_id)
        catalog_result = list(coll.aggregate(pipeline))
        
        if not catalog_result:
            raise HTTPException(status_code=404, detail="Catalog not found")
            
        return catalog_result[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching catalog: {str(e)}")

async def get_catalogs_by_type(catalog_type_description: str, skip: int = 0, limit: int = 10) -> dict:
    try:
        # Usar pipeline optimizada para obtener catálogos por tipo
        pipeline = get_catalogs_by_type_pipeline(catalog_type_description, skip, limit)
        catalogs = list(coll.aggregate(pipeline))
        
        # Contar total para paginación
        count_pipeline = [
            {"$addFields": {"id_catalog_type_obj": {"$toObjectId": "$id_catalog_type"}}},
            {"$lookup": {
                "from": "catalogtypes",
                "localField": "id_catalog_type_obj", 
                "foreignField": "_id",
                "as": "catalog_type"
            }},
            {"$unwind": "$catalog_type"},
            {"$match": {
                "catalog_type.description": {"$regex": f"^{catalog_type_description}$", "$options": "i"},
                "active": True
            }},
            {"$count": "total"}
        ]
        
        count_result = list(coll.aggregate(count_pipeline))
        total_count = count_result[0]["total"] if count_result else 0
        
        return {
            "catalogs": catalogs,
            "total": total_count,
            "skip": skip,
            "limit": limit,
            "catalog_type": catalog_type_description
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching catalogs by type: {str(e)}")

async def get_catalogs_by_type(catalog_type_id: str) -> list[Catalog]:
    try:
        # Validar que el catalog_type existe
        catalog_type = catalog_types_coll.find_one({"_id": ObjectId(catalog_type_id)})
        if not catalog_type:
            raise HTTPException(status_code=404, detail="Catalog type not found")

        catalogs = []
        for doc in coll.find({"id_catalog_type": catalog_type_id}):
            # Mapear _id a id para el modelo Pydantic
            doc['id'] = str(doc['_id'])
            del doc['_id']
            catalog = Catalog(**doc)
            catalogs.append(catalog)
        return catalogs
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching catalogs by type: {str(e)}")

async def update_catalog(catalog_id: str, catalog: Catalog) -> Catalog:
    try:
        # Validar que el catalog_type existe
        catalog_type = catalog_types_coll.find_one({"_id": ObjectId(catalog.id_catalog_type)})
        if not catalog_type:
            raise HTTPException(status_code=400, detail="Catalog type not found")

        catalog.name = catalog.name.strip()
        catalog.description = catalog.description.strip()

        # Verificar si ya existe otro catálogo con el mismo nombre
        existing_catalog = coll.find_one({
            "name": {"$regex": f"^{catalog.name}$", "$options": "i"},
            "_id": {"$ne": ObjectId(catalog_id)}
        })
        if existing_catalog:
            raise HTTPException(status_code=400, detail="Catalog with this name already exists")

        result = coll.update_one(
            {"_id": ObjectId(catalog_id)},
            {"$set": catalog.model_dump(exclude={"id"})}
        )
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Catalog not found")

        return await get_catalog_by_id(catalog_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating catalog: {str(e)}")

async def deactivate_catalog(catalog_id: str) -> Catalog:
    try:
        result = coll.update_one(
            {"_id": ObjectId(catalog_id)},
            {"$set": {"active": False}}
        )
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Catalog not found")

        return await get_catalog_by_id(catalog_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deactivating catalog: {str(e)}")

