from fastapi import APIRouter, Query, HTTPException, Request
from models.order_details import CreateOrderDetail, UpdateOrderDetail
from controllers.order_details import (
    create_order_detail,
    get_order_details,
    update_order_detail,
    delete_order_detail
)
from utils.security import validateuser

router = APIRouter(prefix="/orders")


@router.post("/{order_id}/detail", tags=["� Order Details"])
@validateuser
async def add_product_to_order(
    request: Request,
    order_id: str,
    detail_data: CreateOrderDetail
):
    """Agregar producto a una orden - Solo el dueño de la orden"""
    is_admin = getattr(request.state, 'admin', False)
    requesting_user_id = request.state.id if not is_admin else None
    
    result = await create_order_detail(order_id, detail_data, requesting_user_id, is_admin)
    
    if not result["success"]:
        if result["message"] == "Orden no encontrada":
            raise HTTPException(status_code=404, detail=result["message"])
        elif "permiso" in result["message"]:
            raise HTTPException(status_code=403, detail=result["message"])
        elif "ya está en la orden" in result["message"]:
            raise HTTPException(status_code=409, detail=result["message"])
        else:
            raise HTTPException(status_code=400, detail=result["message"])
    
    return result


@router.get("/{order_id}/details", tags=["� Order Details"])
@validateuser
async def get_order_products(
    request: Request,
    order_id: str
):
    """Obtener productos de una orden - Solo el dueño de la orden o admin"""
    is_admin = getattr(request.state, 'admin', False)
    requesting_user_id = request.state.id if not is_admin else None
    
    result = await get_order_details(order_id, requesting_user_id, is_admin)
    
    if not result["success"]:
        if result["message"] == "Orden no encontrada":
            raise HTTPException(status_code=404, detail=result["message"])
        elif "permiso" in result["message"]:
            raise HTTPException(status_code=403, detail=result["message"])
        else:
            raise HTTPException(status_code=400, detail=result["message"])
    
    return result


@router.put("/{order_id}/detail/{detail_id}", tags=["🛒 Order Details"])
@validateuser
async def update_product_quantity(
    request: Request,
    order_id: str,
    detail_id: str,
    update_data: UpdateOrderDetail
):
    """Actualizar cantidad de producto en orden - Solo el dueño de la orden"""
    is_admin = getattr(request.state, 'admin', False)
    requesting_user_id = request.state.id if not is_admin else None
    
    result = await update_order_detail(order_id, detail_id, update_data, requesting_user_id, is_admin)
    
    if not result["success"]:
        if result["message"] == "Detalle de orden no encontrado":
            raise HTTPException(status_code=404, detail=result["message"])
        elif "permiso" in result["message"]:
            raise HTTPException(status_code=403, detail=result["message"])
        else:
            raise HTTPException(status_code=400, detail=result["message"])
    
    return result


@router.delete("/{order_id}/details/{detail_id}", tags=["� Order Details"])
@validateuser
async def remove_product_from_order(
    request: Request,
    order_id: str,
    detail_id: str
):
    """Eliminar producto de orden - Solo el dueño de la orden"""
    is_admin = getattr(request.state, 'admin', False)
    requesting_user_id = request.state.id if not is_admin else None
    
    result = await delete_order_detail(order_id, detail_id, requesting_user_id, is_admin)
    
    if not result["success"]:
        if result["message"] == "Detalle de orden no encontrado":
            raise HTTPException(status_code=404, detail=result["message"])
        elif "permiso" in result["message"]:
            raise HTTPException(status_code=403, detail=result["message"])
        else:
            raise HTTPException(status_code=400, detail=result["message"])
    
    return result
