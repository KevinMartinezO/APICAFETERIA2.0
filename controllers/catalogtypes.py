from models.catalogtypes import CatalogType
from utils.mongodb import get_collection
from fastapi import HTTPException
from bson import ObjectId

coll = get_collection("catalogtypes")

async def create_catalog_type(catalog_type: CatalogType) -> CatalogType:
    try:
        catalog_type.description = catalog_type.description.strip().lower()

        existing_type = coll.find_one({"description": catalog_type.description})
        if existing_type:
            raise HTTPException(status_code=400, detail="Catalog type already exists")

        catalog_type_dict = catalog_type.model_dump(exclude={"id"})
        inserted = coll.insert_one(catalog_type_dict)
        catalog_type.id = str(inserted.inserted_id)
        return catalog_type
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating catalog type: {str(e)}")

async def get_catalog_types() -> list[CatalogType]:
    try:
        catalog_types = []
        for doc in coll.find():
            # Mapear _id a id para el modelo Pydantic
            doc['id'] = str(doc['_id'])
            del doc['_id']
            catalog_type = CatalogType(**doc)
            catalog_types.append(catalog_type)
        return catalog_types
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching catalog types: {str(e)}")

async def get_catalog_type_by_id(catalog_type_id: str) -> CatalogType:
    try:
        doc = coll.find_one({"_id": ObjectId(catalog_type_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Catalog type not found")

        # Mapear _id a id para el modelo Pydantic
        doc['id'] = str(doc['_id'])
        del doc['_id']
        return CatalogType(**doc)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching catalog type: {str(e)}")

async def update_catalog_type(catalog_type_id: str, catalog_type: CatalogType) -> CatalogType:
    try:
        catalog_type.description = catalog_type.description.strip().lower()

        existing_type = coll.find_one({"description": catalog_type.description, "_id": {"$ne": ObjectId(catalog_type_id)}})
        if existing_type:
            raise HTTPException(status_code=400, detail="Catalog type already exists")

        result = coll.update_one(
            {"_id": ObjectId(catalog_type_id)},
            {"$set": catalog_type.model_dump(exclude={"id"})}
        )
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Catalog type not found")

        return await get_catalog_type_by_id(catalog_type_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating catalog type: {str(e)}")

#insted of delete_catalog_type we can deactivate it
async def deactivate_catalog_type(catalog_type_id: str) -> CatalogType:
    try:
        result = coll.update_one(
            {"_id": ObjectId(catalog_type_id)},
            {"$set": {"active": False}}
        )
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Catalog type not found")

        return await get_catalog_type_by_id(catalog_type_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deactivating catalog type: {str(e)}")