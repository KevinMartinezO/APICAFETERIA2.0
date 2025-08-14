"""
Pipelines de MongoDB para operaciones con catálogos
"""
from bson import ObjectId

def get_catalog_with_type_pipeline(catalog_id: str) -> list:
    """
    Pipeline para obtener un catálogo con información del tipo
    """
    return [
        {"$match": {"_id": ObjectId(catalog_id)}},
        {"$addFields": {
            "id_catalog_type_obj": {"$toObjectId": "$id_catalog_type"}
        }},
        {"$lookup": {
            "from": "catalogtypes",
            "localField": "id_catalog_type_obj",
            "foreignField": "_id",
            "as": "catalog_type"
        }},
        {"$unwind": "$catalog_type"},
        {"$project": {
            "id": {"$toString": "$_id"},
            "id_catalog_type": {"$toString": "$id_catalog_type"},
            "name": "$name",
            "description": "$description",
            "cost": "$cost",
            "discount": "$discount",
            "active": "$active",
            "catalog_type_description": "$catalog_type.description"
        }}
    ]

def get_catalogs_by_type_pipeline(catalog_type_description: str, skip: int = 0, limit: int = 10) -> list:
    """
    Pipeline para obtener catálogos filtrados por tipo con paginación
    """
    return [
        {"$addFields": {
            "id_catalog_type_obj": {"$toObjectId": "$id_catalog_type"}
        }},
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
        {"$project": {
            "id": {"$toString": "$_id"},
            "id_catalog_type": {"$toString": "$id_catalog_type"},
            "name": "$name",
            "description": "$description",
            "cost": "$cost",
            "discount": "$discount",
            "active": "$active"
        }},
        {"$skip": skip},
        {"$limit": limit}
    ]

def get_all_catalogs_with_types_pipeline(skip: int = 0, limit: int = 10) -> list:
    """
    Pipeline para obtener todos los catálogos con información del tipo
    """
    return [
        {"$addFields": {
            "id_catalog_type_obj": {"$toObjectId": "$id_catalog_type"}
        }},
        {"$lookup": {
            "from": "catalogtypes",
            "localField": "id_catalog_type_obj",
            "foreignField": "_id",
            "as": "catalog_type"
        }},
        {"$unwind": "$catalog_type"},
        {"$match": {
            "catalog_type.active": True
        }},
        {"$project": {
            "_id": 0,  # Excluir el _id original
            "id": {"$toString": "$_id"},
            "id_catalog_type": {"$toString": "$id_catalog_type"},
            "name": "$name",
            "description": "$description",
            "cost": "$cost",
            "discount": "$discount",
            "active": "$active",
            "catalog_type_description": "$catalog_type.description"
        }},
        {"$skip": skip},
        {"$limit": limit}
    ]

def validate_catalog_type_pipeline(catalog_type_id: str) -> list:
    """
    Pipeline para validar que un catalog type existe y está activo
    """
    return [
        {"$match": {
            "_id": ObjectId(catalog_type_id),
            "active": True
        }},
        {"$project": {
            "id": {"$toString": "$_id"},
            "description": "$description",
            "active": "$active"
        }}
    ]

def search_catalogs_pipeline(search_term: str, skip: int = 0, limit: int = 10) -> list:
    """
    Pipeline para buscar catálogos por nombre o descripción
    """
    return [
        {"$match": {
            "$or": [
                {"name": {"$regex": search_term, "$options": "i"}},
                {"description": {"$regex": search_term, "$options": "i"}}
            ],
            "active": True
        }},
        {"$addFields": {
            "id_catalog_type_obj": {"$toObjectId": "$id_catalog_type"}
        }},
        {"$lookup": {
            "from": "catalogtypes",
            "localField": "id_catalog_type_obj",
            "foreignField": "_id",
            "as": "catalog_type"
        }},
        {"$unwind": "$catalog_type"},
        {"$project": {
            "id": {"$toString": "$_id"},
            "id_catalog_type": {"$toString": "$id_catalog_type"},
            "name": "$name",
            "description": "$description",
            "cost": "$cost",
            "discount": "$discount",
            "active": "$active",
            "catalog_type_description": "$catalog_type.description"
        }},
        {"$skip": skip},
        {"$limit": limit}
    ]
