"""
Pipelines de MongoDB para operaciones con bundles
"""
from bson import ObjectId

def get_bundle_validation_pipeline(bundle_id: str) -> list:
    """
    Pipeline para validar que un bundle existe, está activo y es de tipo 'bundle'
    """
    return [
        {"$match": {"_id": ObjectId(bundle_id)}},
        {"$addFields": {
            "id_catalog_type_obj": {"$toObjectId": "$id_catalog_type"}
        }},
        {"$lookup": {
            "from": "catalogtypes",
            "localField": "id_catalog_type_obj",
            "foreignField": "_id",
            "as": "catalog_type"
        }},
        {"$match": {
            "catalog_type.description": {"$regex": "^bundle$", "$options": "i"},
            "active": True
        }}
    ]

def get_bundle_with_catalog_type_pipeline(bundle_id: str) -> list:
    """
    Pipeline para obtener un bundle con información del catalog type
    (sin filtro de activo para casos de solo lectura)
    """
    return [
        {"$match": {"_id": ObjectId(bundle_id)}},
        {"$addFields": {
            "id_catalog_type_obj": {"$toObjectId": "$id_catalog_type"}
        }},
        {"$lookup": {
            "from": "catalogtypes",
            "localField": "id_catalog_type_obj",
            "foreignField": "_id",
            "as": "catalog_type"
        }},
        {"$match": {
            "catalog_type.description": {"$regex": "^bundle$", "$options": "i"}
        }}
    ]

def get_bundle_products_pipeline(bundle_id: str) -> list:
    """
    Pipeline para obtener todos los productos de un bundle con información completa
    """
    return [
        {"$match": {"id_bundle": bundle_id}},
        {"$addFields": {
            "id_producto_obj": {"$toObjectId": "$id_producto"}
        }},
        {"$lookup": {
            "from": "catalogs",
            "localField": "id_producto_obj",
            "foreignField": "_id",
            "as": "product_info"
        }},
        {"$unwind": "$product_info"},
        {"$project": {
            "_id": 0,  # Excluir el _id original
            "bundle_detail_id": {"$toString": "$_id"},
            "id_producto": {"$toString": "$id_producto"},
            "quantity": "$quantity",
            "product_name": "$product_info.name",
            "product_description": "$product_info.description",
            "product_cost": "$product_info.cost",
            "product_active": "$product_info.active"
        }}
    ]

def get_product_validation_pipeline(product_id: str) -> list:
    """
    Pipeline para validar que un producto existe y está activo
    """
    return [
        {"$match": {
            "_id": ObjectId(product_id),
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
        {"$match": {
            "catalog_type.description": {"$regex": "^products$", "$options": "i"}
        }}
    ]

def get_bundle_detail_with_product_pipeline(bundle_id: str, bundle_detail_id: str) -> list:
    """
    Pipeline para obtener un bundle detail específico con información del producto
    """
    return [
        {"$match": {
            "_id": ObjectId(bundle_detail_id),
            "id_bundle": bundle_id
        }},
        {"$addFields": {
            "id_producto_obj": {"$toObjectId": "$id_producto"}
        }},
        {"$lookup": {
            "from": "catalogs",
            "localField": "id_producto_obj",
            "foreignField": "_id",
            "as": "product_info"
        }},
        {"$unwind": "$product_info"},
        {"$project": {
            "bundle_detail_id": {"$toString": "$_id"},
            "id_bundle": "$id_bundle",
            "id_producto": {"$toString": "$id_producto"},
            "quantity": "$quantity",
            "product_name": "$product_info.name",
            "product_cost": "$product_info.cost"
        }}
    ]

def check_existing_product_in_bundle_pipeline(bundle_id: str, product_id: str) -> list:
    """
    Pipeline para verificar si un producto ya existe en un bundle
    """
    return [
        {"$match": {
            "id_bundle": bundle_id,
            "id_producto": product_id
        }},
        {"$project": {
            "bundle_detail_id": {"$toString": "$_id"},
            "quantity": "$quantity"
        }}
    ]
