from models.order_details import OrderDetail, CreateOrderDetail, UpdateOrderDetail
from pipelines.order_detail_pipelines import (
    get_order_details_pipeline,
    get_order_detail_by_id_pipeline,
    validate_order_exists_pipeline,
    validate_product_exists_pipeline,
    check_order_detail_exists_pipeline,
    get_order_details_owner_pipeline
)
from utils.mongodb import get_collection
from bson import ObjectId
from datetime import datetime

# Conexión a las colecciones
order_details_collection = get_collection("order_details")
orders_collection = get_collection("orders")
catalogs_collection = get_collection("catalogs")
settings_collection = get_collection("app_settings")

# ============================================================================
# ORDER DETAILS - FUNCIONES HELPER
# ============================================================================

async def recalculate_order_totals(order_id: str) -> dict:
    """Recalcular y actualizar los totales de una orden basado en sus detalles activos"""
    try:
        print(f"DEBUG: Recalculando totales para orden: {order_id}")

        # Obtener todos los detalles activos de la orden con información del producto
        pipeline = [
            {"$match": {"id_order": order_id, "active": True}},
            {
                "$lookup": {
                    "from": "catalogs",
                    "let": {"product_id": {"$toObjectId": "$id_producto"}},
                    "pipeline": [
                        {"$match": {"$expr": {"$eq": ["$_id", "$$product_id"]}}}
                    ],
                    "as": "product_info"
                }
            },
            {
                "$addFields": {
                    "product": {"$arrayElemAt": ["$product_info", 0]},
                    "product_price": {"$arrayElemAt": ["$product_info.cost", 0]},
                    "line_subtotal": {
                        "$cond": {
                            "if": {"$gt": [{"$size": "$product_info"}, 0]},
                            "then": {
                                "$multiply": [
                                    "$quantity",
                                    {"$arrayElemAt": ["$product_info.cost", 0]}
                                ]
                            },
                            "else": 0
                        }
                    }
                }
            }
        ]

        # Debug: ver los detalles antes del group
        debug_result = list(order_details_collection.aggregate(pipeline))
        print(f"DEBUG: Detalles encontrados: {len(debug_result)}")
        for detail in debug_result:
            print(f"DEBUG: Detalle - quantity: {detail.get('quantity')}, product_info: {detail.get('product_info')}, line_subtotal: {detail.get('line_subtotal')}")

        # Ahora hacer el group
        pipeline.append({
            "$group": {
                "_id": None,
                "subtotal": {"$sum": "$line_subtotal"},
                "total_items": {"$sum": "$quantity"}
            }
        })

        result = list(order_details_collection.aggregate(pipeline))
        print(f"DEBUG: Resultado del pipeline: {result}")

        if result and result[0]["subtotal"] > 0:
            subtotal = result[0]["subtotal"]

            # Calcular impuestos (15% por ejemplo - esto puede ser configurable)
            tax_result = settings_collection.find_one({"key": "general_tax"})
            if tax_result and "value" in tax_result:
                tax_rate = tax_result["value"]
            else:
                print("DEBUG: No se encontró tasa de impuesto, usando valor por defecto de 0.15")
                tax_rate = 0.01

            taxes = subtotal * tax_rate

            # Por ahora no hay descuentos automáticos
            discount = 0.0
            total = subtotal + taxes - discount

            print(f"DEBUG: Calculando - subtotal: {subtotal}, taxes: {taxes}, total: {total}")

            # Actualizar la orden con los nuevos totales
            update_result = orders_collection.update_one(
                {"_id": ObjectId(order_id)},
                {
                    "$set": {
                        "subtotal": round(subtotal, 2),
                        "taxes": round(taxes, 2),
                        "discount": discount,
                        "total": round(total, 2),
                        "date_updated": datetime.utcnow()
                    }
                }
            )

            print(f"DEBUG: Update result - modified_count: {update_result.modified_count}")

            if update_result.modified_count > 0:
                return {
                    "success": True,
                    "subtotal": round(subtotal, 2),
                    "taxes": round(taxes, 2),
                    "discount": discount,
                    "total": round(total, 2)
                }
        else:
            print("DEBUG: No hay productos o subtotal es 0, reseteando a cero")
            # La orden no tiene productos, resetear a cero
            orders_collection.update_one(
                {"_id": ObjectId(order_id)},
                {
                    "$set": {
                        "subtotal": 0.0,
                        "taxes": 0.0,
                        "discount": 0.0,
                        "total": 0.0,
                        "date_updated": datetime.utcnow()
                    }
                }
            )
            return {
                "success": True,
                "subtotal": 0.0,
                "taxes": 0.0,
                "discount": 0.0,
                "total": 0.0
            }

        return {"success": False, "message": "Error al actualizar totales"}

    except Exception as e:
        print(f"DEBUG: Error en recalculate_order_totals: {str(e)}")
        return {"success": False, "message": f"Error al recalcular totales: {str(e)}"}

# ============================================================================
# ORDER DETAILS - FUNCIONES DE CREACIÓN
# ============================================================================

async def create_order_detail(order_id: str, detail_data: CreateOrderDetail, requesting_user_id: str = None, is_admin: bool = False) -> dict:
    """Crear un nuevo detalle de orden"""
    try:
        # Validar ObjectId de la orden
        if not ObjectId.is_valid(order_id):
            return {"success": False, "message": "ID de orden inválido", "data": None}

        # Verificar que la orden existe y pertenece al usuario (si no es admin)
        order_info = orders_collection.find_one({"_id": ObjectId(order_id)})
        if not order_info:
            return {"success": False, "message": "Orden no encontrada", "data": None}

        if not is_admin and requesting_user_id:
            if order_info["id_user"] != requesting_user_id:
                return {"success": False, "message": "No tienes permiso para modificar esta orden", "data": None}

        # Verificar que el producto existe (consulta directa)
        product_exists = catalogs_collection.find_one({"_id": ObjectId(detail_data.id_producto)})
        if not product_exists:
            return {"success": False, "message": "Producto no encontrado", "data": None}

        # Verificar si ya existe un detalle activo para este producto en esta orden (consulta directa)
        existing_detail = order_details_collection.find_one({
            "id_order": order_id,  # Usar string directamente
            "id_producto": detail_data.id_producto,  # Usar string directamente
            "active": True
        })

        if existing_detail:
            return {"success": False, "message": "Este producto ya está en la orden", "data": None}

        # Crear detalle
        detail_dict = detail_data.model_dump()
        detail_dict["id_order"] = order_id  # Mantener como string para consistencia
        detail_dict["id_producto"] = detail_data.id_producto  # Mantener como string para consistencia
        detail_dict["date_created"] = datetime.utcnow()
        detail_dict["date_updated"] = datetime.utcnow()
        detail_dict["active"] = True

        result = order_details_collection.insert_one(detail_dict)
        
        if result.inserted_id:
            # Recalcular totales de la orden después de agregar el producto
            totals_result = await recalculate_order_totals(order_id)
            
            response_data = {"id": str(result.inserted_id)}
            if totals_result["success"]:
                response_data["order_totals"] = {
                    "subtotal": totals_result["subtotal"],
                    "taxes": totals_result["taxes"],
                    "discount": totals_result["discount"],
                    "total": totals_result["total"]
                }
            
            return {
                "success": True,
                "message": "Producto agregado a la orden exitosamente",
                "data": response_data
            }
        
        return {"success": False, "message": "Error al agregar el producto a la orden", "data": None}

    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}", "data": None}

# ============================================================================
# ORDER DETAILS - FUNCIONES DE CONSULTA
# ============================================================================

async def get_order_details(order_id: str, requesting_user_id: str = None, is_admin: bool = False) -> dict:
    """Obtener detalles de una orden específica usando pipeline"""
    try:
        if not ObjectId.is_valid(order_id):
            return {"success": False, "message": "ID de orden inválido", "data": None}

        # Validar que la orden existe usando pipeline
        exists_pipeline = validate_order_exists_pipeline(order_id)
        exists_result = list(orders_collection.aggregate(exists_pipeline))
        if not exists_result:
            return {"success": False, "message": "Orden no encontrada", "data": None}

        # Verificar permisos
        order_info = orders_collection.find_one({"_id": ObjectId(order_id)})
        if not is_admin and requesting_user_id:
            if order_info["id_user"] != requesting_user_id:
                return {"success": False, "message": "No tienes permiso para ver esta orden", "data": None}

        # Obtener detalles usando pipeline
        pipeline = get_order_details_pipeline(order_id)
        details = list(order_details_collection.aggregate(pipeline))

        return {
            "success": True,
            "message": "Detalles de orden obtenidos exitosamente",
            "data": {
                "order_id": order_id,
                "details": details,
                "total_items": len(details)
            }
        }
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}", "data": None}

async def get_order_detail_by_id(detail_id: str) -> dict:
    """Obtener un detalle específico de orden usando pipeline"""
    try:
        if not ObjectId.is_valid(detail_id):
            return {"success": False, "message": "ID de detalle inválido", "data": None}
        pipeline = get_order_detail_by_id_pipeline(detail_id)
        result = list(order_details_collection.aggregate(pipeline))
        if not result:
            return {"success": False, "message": "Detalle no encontrado", "data": None}
        return {
            "success": True,
            "message": "Detalle obtenido exitosamente",
            "data": result[0]
        }
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}", "data": None}

async def validate_product_exists(product_id: str) -> bool:
    """Validar que un producto existe usando pipeline"""
    pipeline = validate_product_exists_pipeline(product_id)
    result = list(catalogs_collection.aggregate(pipeline))
    return bool(result)

async def check_order_detail_exists(order_id: str, product_id: str) -> bool:
    """Verificar si ya existe un detalle de orden para un producto específico usando pipeline"""
    pipeline = check_order_detail_exists_pipeline(order_id, product_id)
    result = list(order_details_collection.aggregate(pipeline))
    return bool(result)

async def get_order_details_owner(detail_id: str) -> str:
    """Obtener el propietario de un detalle de orden usando pipeline"""
    pipeline = get_order_details_owner_pipeline(detail_id)
    result = list(order_details_collection.aggregate(pipeline))
    if result and "id_user" in result[0]:
        return result[0]["id_user"]
    return None

# ============================================================================
# ORDER DETAILS - FUNCIONES DE ACTUALIZACIÓN
# ============================================================================

async def update_order_detail(order_id: str, detail_id: str, update_data: UpdateOrderDetail, requesting_user_id: str = None, is_admin: bool = False) -> dict:
    """Actualizar un detalle de orden específico con validación de pertenencia"""
    try:
        print(f"DEBUG: Iniciando update_order_detail - order_id: {order_id}, detail_id: {detail_id}")
        
        # Validar ObjectIds
        if not ObjectId.is_valid(detail_id):
            return {"success": False, "message": "ID de detalle inválido", "data": None}

        if not ObjectId.is_valid(order_id):
            return {"success": False, "message": "ID de orden inválido", "data": None}

        # Verificar que el detalle existe Y pertenece a la orden especificada
        detail_info = order_details_collection.find_one({
            "_id": ObjectId(detail_id), 
            "id_order": order_id,  # VALIDACIÓN CRÍTICA: el detalle debe pertenecer a esta orden
            "active": True
        })

        if not detail_info:
            return {"success": False, "message": "Detalle no encontrado o no pertenece a esta orden", "data": None}

        # Si no es admin, verificar que la orden pertenece al usuario
        if not is_admin and requesting_user_id:
            # Obtener la orden asociada al detalle para verificar permisos
            order_info = orders_collection.find_one({"_id": ObjectId(order_id)})
            if not order_info or order_info["id_user"] != requesting_user_id:
                return {"success": False, "message": "No tienes permiso para modificar este detalle", "data": None}

        # Actualizar detalle
        update_dict = update_data.model_dump()
        update_dict["date_updated"] = datetime.utcnow()

        result = order_details_collection.update_one(
            {"_id": ObjectId(detail_id)},
            {"$set": update_dict}
        )

        if result.modified_count > 0:
            print(f"DEBUG: Detalle actualizado exitosamente, iniciando recálculo de totales")
            # Recalcular totales de la orden después de actualizar el producto
            totals_result = await recalculate_order_totals(order_id)
            print(f"DEBUG: Resultado del recálculo: {totals_result}")
            
            response_data = {"modified_count": result.modified_count}
            if totals_result["success"]:
                response_data["order_totals"] = {
                    "subtotal": totals_result["subtotal"],
                    "taxes": totals_result["taxes"],
                    "discount": totals_result["discount"],
                    "total": totals_result["total"]
                }
            
            return {
                "success": True,
                "message": "Detalle de orden actualizado exitosamente",
                "data": response_data
            }

        return {"success": False, "message": "No se pudo actualizar el detalle", "data": None}

    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}", "data": None}

# ============================================================================
# ORDER DETAILS - FUNCIONES DE ELIMINACIÓN
# ============================================================================

async def delete_order_detail(order_id: str, detail_id: str, requesting_user_id: str = None, is_admin: bool = False) -> dict:
    """Eliminar (desactivar) un detalle de orden específico con validación de pertenencia"""
    try:
        # Validar ObjectIds
        if not ObjectId.is_valid(detail_id):
            return {"success": False, "message": "ID de detalle inválido", "data": None}

        if not ObjectId.is_valid(order_id):
            return {"success": False, "message": "ID de orden inválido", "data": None}

        # Verificar que el detalle existe Y pertenece a la orden especificada
        detail_info = order_details_collection.find_one({
            "_id": ObjectId(detail_id), 
            "id_order": order_id,  # VALIDACIÓN CRÍTICA: el detalle debe pertenecer a esta orden
            "active": True
        })

        if not detail_info:
            return {"success": False, "message": "Detalle no encontrado o no pertenece a esta orden", "data": None}

        # Si no es admin, verificar que la orden pertenece al usuario
        if not is_admin and requesting_user_id:
            # Obtener la orden asociada al detalle para verificar permisos
            order_info = orders_collection.find_one({"_id": ObjectId(order_id)})
            if not order_info or order_info["id_user"] != requesting_user_id:
                return {"success": False, "message": "No tienes permiso para modificar este detalle", "data": None}

        # Desactivar detalle (soft delete)
        result = order_details_collection.update_one(
            {"_id": ObjectId(detail_id)},
            {"$set": {"active": False, "date_updated": datetime.utcnow()}}
        )

        if result.modified_count > 0:
            # Recalcular totales de la orden después de eliminar el producto
            totals_result = await recalculate_order_totals(order_id)

            response_data = {"modified_count": result.modified_count}
            if totals_result["success"]:
                response_data["order_totals"] = {
                    "subtotal": totals_result["subtotal"],
                    "taxes": totals_result["taxes"],
                    "discount": totals_result["discount"],
                    "total": totals_result["total"]
                }

            return {
                "success": True,
                "message": "Producto eliminado de la orden exitosamente",
                "data": response_data
            }

        return {"success": False, "message": "No se pudo eliminar el producto", "data": None}

    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}", "data": None}
