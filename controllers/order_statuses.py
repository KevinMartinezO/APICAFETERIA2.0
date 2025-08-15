from models.order_statuses import OrderStatus
from utils.mongodb import get_collection
from fastapi import HTTPException
from bson import ObjectId

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

async def get_order_statuses() -> dict:
    """Obtener todos los order statuses"""
    try:
        # Obtener todos los order statuses directamente
        order_statuses_cursor = coll.find({})
        order_statuses = []
        
        for status in order_statuses_cursor:
            status["id"] = str(status["_id"])
            del status["_id"]
            order_statuses.append(status)
        
        return {
            "order_statuses": order_statuses,
            "total": len(order_statuses)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching order statuses: {str(e)}")

async def get_order_status_by_id(order_status_id: str) -> dict:
    """Obtener un order status por ID"""
    try:
        # Validar ObjectId
        if not ObjectId.is_valid(order_status_id):
            raise HTTPException(status_code=400, detail="Invalid order status ID")
        
        # Buscar el order status directamente
        order_status = coll.find_one({"_id": ObjectId(order_status_id)})
        
        if not order_status:
            raise HTTPException(status_code=404, detail="Order status not found")
        
        # Convertir ObjectId a string para la respuesta
        order_status["id"] = str(order_status["_id"])
        del order_status["_id"]
        
        return order_status
        
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
