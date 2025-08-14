from models.order_statuses import OrderStatus
from utils.mongodb import get_collection
from fastapi import HTTPException
from bson import ObjectId
from pipelines.order_status_pipelines import (
    get_order_status_with_orders_pipeline,
    get_all_order_status_pipeline,
    validate_order_status_pipeline,
    search_order_status_pipeline
)

coll = get_collection("order_statuses")

async def create_order_status(order_status: OrderStatus) -> dict:
    """Crear un nuevo order status"""
    try:
        # Normalizar descripción
        order_status.description = order_status.description.strip().lower()

        # Verificar si ya existe un order status con la misma descripción
        existing = coll.find_one({"description": order_status.description})

        if existing:
            raise HTTPException(status_code=400, detail="Order status with this description already exists")

        # Crear el order status
        order_status_dict = order_status.model_dump(exclude={"id"})
        inserted = coll.insert_one(order_status_dict)

        # Retornar el order status creado con su ID
        order_status_dict["id"] = str(inserted.inserted_id)
        return order_status_dict

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating order status: {str(e)}")

async def get_order_statuses(skip: int = 0, limit: int = 10) -> dict:
    """Obtener todos los order statuses con paginación usando pipeline"""
    try:
        pipeline = get_all_order_status_pipeline(skip, limit)
        order_statuses_cursor = coll.aggregate(pipeline)
        order_statuses = [status for status in order_statuses_cursor]
        return {
            "order_statuses": order_statuses,
            "total": len(order_statuses)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching order statuses: {str(e)}")

async def get_order_status_by_id(order_status_id: str) -> dict:
    """Obtener un order status por ID y sus órdenes usando pipeline"""
    try:
        # Validar ObjectId
        if not ObjectId.is_valid(order_status_id):
            raise HTTPException(status_code=400, detail="Invalid order status ID")
        
        pipeline = get_order_status_with_orders_pipeline(order_status_id)
        result = list(coll.aggregate(pipeline))

        if not result:
            raise HTTPException(status_code=404, detail="Order status not found")
        
        return result[0]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching order status: {str(e)}")

async def update_order_status(order_status_id: str, order_status: OrderStatus) -> dict:
    """Actualizar un order status"""
    try:
        # Validar ObjectId
        if not ObjectId.is_valid(order_status_id):
            raise HTTPException(status_code=400, detail="Invalid order status ID")

        # Verificar que el order status existe
        existing = coll.find_one({"_id": ObjectId(order_status_id)})

        if not existing:
            raise HTTPException(status_code=404, detail="Order status not found")

        # Normalizar descripción
        order_status.description = order_status.description.strip().lower()

        # Verificar si ya existe otro order status con la misma descripción
        duplicate = coll.find_one({
            "description": order_status.description,
            "_id": {"$ne": ObjectId(order_status_id)}
        })

        if duplicate:
            raise HTTPException(status_code=400, detail="Order status with this description already exists")

        # Actualizar el order status
        order_status_dict = order_status.model_dump(exclude={"id"})
        result = coll.update_one(
            {"_id": ObjectId(order_status_id)},
            {"$set": order_status_dict}
        )

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Order status not found")

        # Retornar el order status actualizado
        order_status_dict["id"] = order_status_id
        return order_status_dict

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating order status: {str(e)}")

async def delete_order_status(order_status_id: str) -> dict:
    """Eliminar un order status"""
    try:
        # Validar ObjectId
        if not ObjectId.is_valid(order_status_id):
            raise HTTPException(status_code=400, detail="Invalid order status ID")

        # Obtener el order status antes de eliminarlo
        order_status = coll.find_one({"_id": ObjectId(order_status_id)})

        if not order_status:
            raise HTTPException(status_code=404, detail="Order status not found")

        # Eliminar el order status
        result = coll.delete_one({"_id": ObjectId(order_status_id)})

        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Order status not found")

        # Convertir ObjectId a string para la respuesta
        order_status["id"] = str(order_status["_id"])
        del order_status["_id"]

        return {
            "message": "Order status deleted successfully",
            "deleted_order_status": order_status
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting order status: {str(e)}")

async def validate_order_status(order_status_id: str) -> dict:
    """Validar que un order_status existe y está activo usando pipeline"""
    try:
        # Validar ObjectId
        if not ObjectId.is_valid(order_status_id):
            raise HTTPException(status_code=400, detail="Invalid order status ID")
        
        pipeline = validate_order_status_pipeline(order_status_id)
        result = list(coll.aggregate(pipeline))

        if not result:
            raise HTTPException(status_code=404, detail="Order status not found or inactive")
        
        return result[0]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error validating order status: {str(e)}")

async def search_order_statuses(search_term: str, skip: int = 0, limit: int = 10) -> dict:
    """Buscar estados de orden por nombre o descripción usando pipeline"""
    try:
        pipeline = search_order_status_pipeline(search_term, skip, limit)
        results = list(coll.aggregate(pipeline))
        return {
            "results": results,
            "total": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching order statuses: {str(e)}")
