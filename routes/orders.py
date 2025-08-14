from fastapi import APIRouter, Query, HTTPException, Request
from models.orders import CreateOrder
from models.change_order_status import ChangeOrderStatus
from controllers.orders import (
    create_order,
    get_orders,
    get_order_by_id,
    update_order_status
)
from utils.security import validateuser, validateadmin

router = APIRouter(prefix="/orders")


@router.post("/", tags=["📦 Orders"])
@validateuser
async def create_new_order(
    request: Request,
    order_data: CreateOrder
):
    """Crear nueva orden - Solo usuarios autenticados"""
    # El user_id se toma automáticamente del request.state.id (inyectado por @validateuser)
    result = await create_order(order_data, request.state.id)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result


@router.get("/", tags=["📦 Orders"])
@validateuser
async def get_all_orders(
    request: Request,
    skip: int = Query(default=0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(default=50, ge=1, le=100, description="Número de registros a obtener")
):
    """
    Obtener órdenes:
    - Admin: todas las órdenes del sistema
    - Usuario: solo sus propias órdenes
    """
    # Verificar si es admin desde request.state
    is_admin = getattr(request.state, 'admin', False)
    user_id = None if is_admin else request.state.id
    
    result = await get_orders(skip=skip, limit=limit, user_id=user_id)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result


@router.get("/{order_id}", tags=["📦 Orders"])
@validateuser
async def get_order_details(
    request: Request,
    order_id: str
):
    """
    Obtener orden específica:
    - Admin: cualquier orden
    - Usuario: solo si la orden le pertenece
    """
    is_admin = getattr(request.state, 'admin', False)
    requesting_user_id = request.state.id if not is_admin else None
    
    result = await get_order_by_id(order_id, requesting_user_id, is_admin)
    
    if not result["success"]:
        if result["message"] == "Orden no encontrada":
            raise HTTPException(status_code=404, detail=result["message"])
        elif "permiso" in result["message"]:
            raise HTTPException(status_code=403, detail=result["message"])
        else:
            raise HTTPException(status_code=400, detail=result["message"])
    
    return result


@router.put("/{order_id}/status", summary="Finalizar orden (cambiar a Ordered)", tags=["📦 Orders"])
@validateuser
async def finalize_order(
    request: Request,
    order_id: str
):
    """
    Finalizar orden (usuarios):
    - Automáticamente cambia de InProgress a Ordered
    - Solo sus propias órdenes
    - No requiere payload
    """
    result = await update_order_status(
        order_id, 
        None,  # No enviamos id_status, se determina automáticamente
        requesting_user_id=request.state.id,
        is_admin=False
    )
    
    if not result["success"]:
        if result["message"] == "Orden no encontrada":
            raise HTTPException(status_code=404, detail=result["message"])
        elif "permiso" in result["message"]:
            raise HTTPException(status_code=403, detail=result["message"])
        else:
            raise HTTPException(status_code=400, detail=result["message"])
    
    return result


@router.post("/{order_id}/status", tags=["📦 Orders"])
@validateadmin
async def change_order_status_admin(
    request: Request,
    order_id: str,
    status_data: ChangeOrderStatus
):
    """
    Cambiar estado de orden (admin):
    - Pueden cambiar cualquier orden a cualquier estado
    - Solo requiere id_status en el payload
    """
    result = await update_order_status(
        order_id, 
        status_data.id_status,  # Solo el id_status, no el id_order
        is_admin=True
    )
    
    if not result["success"]:
        if result["message"] == "Orden no encontrada":
            raise HTTPException(status_code=404, detail=result["message"])
        else:
            raise HTTPException(status_code=400, detail=result["message"])
    
    return result
