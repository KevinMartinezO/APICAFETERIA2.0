"""
Pipelines de MongoDB para operaciones con order_status
"""
from bson import ObjectId

def get_order_status_with_orders_pipeline(order_status_id: str) -> list:
    """
    Pipeline para obtener un estado de orden con información de las órdenes asociadas
    """
    return [
        {"$match": {"_id": ObjectId(order_status_id)}},
        {"$lookup": {
            "from": "orders",
            "localField": "_id",
            "foreignField": "id_order_status",
            "as": "orders"
        }},
        {"$project": {
            "id": {"$toString": "$_id"},
            "name": "$name",
            "description": "$description",
            "active": "$active",
            "orders": {
                "$map": {
                    "input": "$orders",
                    "as": "order",
                    "in": {
                        "id": {"$toString": "$$order._id"},
                        "total": "$$order.total",
                        "created_at": "$$order.created_at"
                    }
                }
            }
        }}
    ]

def get_all_order_status_pipeline(skip: int = 0, limit: int = 10) -> list:
    """
    Pipeline para obtener todos los estados de orden con paginación
    """
    return [
        {"$match": {"active": True}},
        {"$project": {
            "id": {"$toString": "$_id"},
            "name": "$name",
            "description": "$description",
            "active": "$active"
        }},
        {"$skip": skip},
        {"$limit": limit}
    ]

def validate_order_status_pipeline(order_status_id: str) -> list:
    """
    Pipeline para validar que un order_status existe y está activo
    """
    return [
        {"$match": {
            "_id": ObjectId(order_status_id),
            "active": True
        }},
        {"$project": {
            "id": {"$toString": "$_id"},
            "name": "$name",
            "description": "$description",
            "active": "$active"
        }}
    ]

def search_order_status_pipeline(search_term: str, skip: int = 0, limit: int = 10) -> list:
    """
    Pipeline para buscar estados de orden por nombre o descripción
    """
    return [
        {"$match": {
            "$or": [
                {"name": {"$regex": search_term, "$options": "i"}},
                {"description": {"$regex": search_term, "$options": "i"}}
            ],
            "active": True
        }},
        {"$project": {
            "id": {"$toString": "$_id"},
            "name": "$name",
            "description": "$description",
            "active": "$active"
        }},
        {"$skip": skip},
        {"$limit": limit}
    ]