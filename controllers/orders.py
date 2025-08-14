from models.orders import Order, CreateOrder
from models.order_status_records import OrderStatusRecord, CreateOrderStatusRecord
from pipelines.order_pipelines import (
    get_all_orders_pipeline,
    get_orders_by_user_pipeline,
    get_order_by_id_pipeline,
    get_order_owner_pipeline,
    get_existing_inprogress_order_pipeline
)
from utils.mongodb import get_collection
from bson import ObjectId
from datetime import datetime

# Conexión a las colecciones
orders_collection = get_collection("orders")
users_collection = get_collection("users")
order_status_records_collection = get_collection("order_status_record")  # Historial de cambios de estado
order_statuses_collection = get_collection("order_statuses")  # Catálogo de estados disponibles

# ============================================================================
# ORDERS - FUNCIONES DE CREACIÓN
# ============================================================================

async def create_order(order_data: CreateOrder, user_id: str) -> dict:
    """Crear una nueva orden o retornar la existente en 'inprogress'"""
    try:
        # Validar que el usuario existe (consulta directa más simple)
        user_exists = users_collection.find_one({"_id": ObjectId(user_id)})
        if not user_exists:
            return {"success": False, "message": "Usuario no encontrado", "data": None}

        # Verificar si ya existe una orden en "inprogress" (aquí sí necesitamos pipeline por el lookup)
        existing_order = list(orders_collection.aggregate(get_existing_inprogress_order_pipeline(user_id)))

        if existing_order:
            return {
                "success": True,
                "message": "Ya tienes una orden en progreso",
                "data": existing_order[0]
            }

        # Crear nueva orden vacía (sin subtotal, taxes, etc.)
        order_dict = {
            "id_user": user_id,  # Mantener como string para consistencia
            "date": datetime.utcnow(),
            "subtotal": 0.0,
            "taxes": 0.0,
            "discount": 0.0,
            "total": 0.0
        }

        result = orders_collection.insert_one(order_dict)

        if result.inserted_id:
            # Crear estado inicial "InProgress" automáticamente
            initial_status = list(order_statuses_collection.aggregate([
                {"$match": {"description": "inprogress"}},
                {"$project": {"_id": 1}},
                {"$limit": 1}
            ]))

            if initial_status:
                status_data = {
                    "id_order": str(result.inserted_id),  # Convertir a string para consistencia
                    "id_status": str(initial_status[0]["_id"]),  # Convertir a string para consistencia
                    "date": datetime.utcnow()
                }
                order_status_records_collection.insert_one(status_data)

            # Retornar la orden creada con formato similar al existente
            created_order = {
                "_id": str(result.inserted_id),
                "id_user": user_id,
                "date": order_dict["date"],
                "subtotal": 0.0,
                "taxes": 0.0,
                "discount": 0.0,
                "total": 0.0,
                "status": "inprogress"
            }

            return {
                "success": True,
                "message": "Orden creada exitosamente",
                "data": created_order
            }

        return {"success": False, "message": "Error al crear la orden", "data": None}

    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}", "data": None}

# ============================================================================
# ORDERS - FUNCIONES DE CONSULTA
# ============================================================================

async def get_orders(skip: int = 0, limit: int = 50, user_id: str = None) -> dict:
    """Obtener órdenes (todas o de un usuario específico)"""
    try:
        if user_id:
            # Validar que el usuario existe (consulta directa)
            user_exists = users_collection.find_one({"_id": ObjectId(user_id)})
            if not user_exists:
                return {"success": False, "message": "Usuario no encontrado", "data": None}
            
            pipeline = get_orders_by_user_pipeline(user_id, skip, limit)
        else:
            pipeline = get_all_orders_pipeline(skip, limit)
        
        orders = list(orders_collection.aggregate(pipeline))
        
        # Contar total de documentos
        if user_id:
            total = orders_collection.count_documents({"id_user": user_id})  # Buscar por string
        else:
            total = orders_collection.count_documents({})
        
        return {
            "success": True,
            "message": "Órdenes obtenidas exitosamente",
            "data": {
                "orders": orders,
                "total": total,
                "skip": skip,
                "limit": limit,
                "has_more": skip + len(orders) < total
            }
        }
    
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}", "data": None}


# ============================================================================
# ORDERS - FUNCIONES DE CONSULTA ESPECÍFICA
# ============================================================================

async def get_order_by_id(order_id: str, requesting_user_id: str = None, is_admin: bool = False) -> dict:
    """Obtener una orden específica por ID"""
    try:
        # Validar ObjectId
        if not ObjectId.is_valid(order_id):
            return {"success": False, "message": "ID de orden inválido", "data": None}

        # Si no es admin, verificar que la orden pertenece al usuario
        if not is_admin and requesting_user_id:
            owner_result = list(orders_collection.aggregate(get_order_owner_pipeline(order_id)))
            if not owner_result:
                return {"success": False, "message": "Orden no encontrada", "data": None}

            if owner_result[0]["id_user"] != requesting_user_id:
                return {"success": False, "message": "No tienes permiso para ver esta orden", "data": None}

        # Obtener orden con detalles completos
        pipeline = get_order_by_id_pipeline(order_id)
        orders = list(orders_collection.aggregate(pipeline))

        if not orders:
            return {"success": False, "message": "Orden no encontrada", "data": None}

        return {
            "success": True,
            "message": "Orden obtenida exitosamente",
            "data": orders[0]
        }

    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}", "data": None}

# ============================================================================
# ORDERS - FUNCIONES DE ACTUALIZACIÓN DE ESTADO
# ============================================================================

async def update_order_status(order_id: str, order_status_id: str = None, requesting_user_id: str = None, is_admin: bool = False) -> dict:
    """Actualizar el estado de una orden (solo para users si es su orden, o admins)"""
    try:
        # Validar ObjectId
        if not ObjectId.is_valid(order_id):
            return {"success": False, "message": "ID de orden inválido", "data": None}

        # Verificar que la orden existe
        order_exists = orders_collection.find_one({"_id": ObjectId(order_id)})
        if not order_exists:
            return {"success": False, "message": "Orden no encontrada", "data": None}

        # Si no es admin, verificar permisos y restricciones
        if not is_admin:
            if not requesting_user_id:
                return {"success": False, "message": "Usuario no especificado", "data": None}

            # Verificar que la orden pertenece al usuario
            if order_exists["id_user"] != requesting_user_id:
                return {"success": False, "message": "No tienes permiso para modificar esta orden", "data": None}

            # Verificar que el estado actual es "InProgress"
            current_status = order_status_records_collection.find_one(
                {"id_order": order_id},  # Buscar por string directamente
                sort=[("date", -1)]
            )

            if current_status:
                current_status_info = order_statuses_collection.find_one({"_id": ObjectId(current_status["id_status"])})
                if current_status_info and current_status_info["description"] != "inprogress":
                    return {"success": False, "message": "Solo puedes finalizar órdenes en progreso", "data": None}

            # Para usuarios, automáticamente buscar el estado "ordered"
            if order_status_id is None:
                ordered_status = order_statuses_collection.find_one({"description": "ordered"})
                if not ordered_status:
                    return {"success": False, "message": "Estado 'ordered' no encontrado en el sistema", "data": None}
                order_status_id = str(ordered_status["_id"])

            # VALIDACIÓN CRÍTICA: Verificar que la orden tenga productos antes de finalizar
            order_details_collection = get_collection("order_details")
            active_products = order_details_collection.count_documents({
                "id_order": order_id,
                "active": True
            })

            if active_products == 0:
                return {"success": False, "message": "No puedes finalizar una orden vacía. Agrega al menos un producto antes de finalizar.", "data": None}

        # Para admins, validar que el estado existe si se proporciona
        if order_status_id:
            if not ObjectId.is_valid(order_status_id):
                return {"success": False, "message": "ID de estado inválido", "data": None}

            status_exists = order_statuses_collection.find_one({"_id": ObjectId(order_status_id)})
            if not status_exists:
                return {"success": False, "message": "Estado de orden no encontrado", "data": None}

            # VALIDACIÓN PARA ADMINS: También verificar productos para ciertos estados
            status_description = status_exists.get("description", "").lower()
            states_requiring_products = ["ordered", "shipped", "delivered", "processing"]

            if status_description in states_requiring_products:
                order_details_collection = get_collection("order_details")
                active_products = order_details_collection.count_documents({
                    "id_order": order_id,
                    "active": True
                })

                if active_products == 0:
                    return {"success": False, "message": f"No se puede cambiar a '{status_description}' una orden vacía. La orden debe tener al menos un producto.", "data": None}

        # Crear nuevo registro de estado
        status_data = {
            "id_order": order_id,  # Ya viene como string del parámetro
            "id_status": order_status_id,  # Ya viene como string del parámetro
            "date": datetime.utcnow()
        }

        result = order_status_records_collection.insert_one(status_data)

        if result.inserted_id:
            return {
                "success": True,
                "message": "Estado de orden actualizado exitosamente",
                "data": {"id": str(result.inserted_id)}
            }

        return {"success": False, "message": "Error al actualizar el estado", "data": None}

    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}", "data": None}
