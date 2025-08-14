from models.bundle_details import BundleDetail, BundleWithProducts, AddProductToBundle
from models.catalogs import Catalog
from utils.mongodb import get_collection
from fastapi import HTTPException
from bson import ObjectId
from pipelines import (
    get_bundle_with_catalog_type_pipeline,
    get_bundle_products_pipeline,
    get_bundle_validation_pipeline,
    get_product_validation_pipeline,
    get_bundle_detail_with_product_pipeline,
    check_existing_product_in_bundle_pipeline
)

bundle_details_coll = get_collection("bundle_details")
catalogs_coll = get_collection("catalogs")
catalog_types_coll = get_collection("catalogtypes")

async def get_bundle_with_products(bundle_id: str) -> BundleWithProducts:
    """Obtener información completa del bundle con todos sus productos"""
    try:
        # Verificar que el bundle existe y es de tipo "bundle" usando pipeline
        pipeline = get_bundle_with_catalog_type_pipeline(bundle_id)
        bundle_result = list(catalogs_coll.aggregate(pipeline))

        if not bundle_result:
            raise HTTPException(status_code=404, detail="Bundle no encontrado o no es de tipo bundle")

        bundle = bundle_result[0]

        # Obtener los productos del bundle usando pipeline optimizada
        products_pipeline = get_bundle_products_pipeline(bundle_id)
        products = list(bundle_details_coll.aggregate(products_pipeline))

        # Crear respuesta completa
        bundle_response = BundleWithProducts(
            id=str(bundle["_id"]),
            id_catalog_type=str(bundle["id_catalog_type"]),
            name=bundle["name"],
            description=bundle["description"],
            cost=bundle["cost"],
            discount=bundle.get("discount", 0),
            active=bundle.get("active", True),
            products=products
        )

        return bundle_response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching bundle with products: {str(e)}")

async def add_product_to_bundle(bundle_id: str, product_data: AddProductToBundle) -> dict:
    """Agregar un producto al bundle"""
    try:
        # Verificar que no se esté agregando el mismo bundle como producto (evitar recursión)
        if product_data.id_producto == bundle_id:
            raise HTTPException(status_code=400, detail="Cannot add bundle to itself")

        # Validar bundle (existe, activo y es de tipo bundle) en una sola pipeline
        bundle_pipeline = get_bundle_validation_pipeline(bundle_id)
        bundle_result = list(catalogs_coll.aggregate(bundle_pipeline))

        if not bundle_result:
            raise HTTPException(status_code=404, detail="Bundle no encontrado, inactivo o no es de tipo bundle")

        bundle = bundle_result[0]

        # Validar producto (existe, activo y es de tipo producto) en una sola pipeline
        product_pipeline = get_product_validation_pipeline(product_data.id_producto)
        product_result = list(catalogs_coll.aggregate(product_pipeline))

        if not product_result:
            raise HTTPException(status_code=404, detail="Producto no encontrado, inactivo o no es de tipo producto")

        product = product_result[0]

        # Verificar si el producto ya existe en el bundle usando pipeline
        existing_pipeline = check_existing_product_in_bundle_pipeline(bundle_id, product_data.id_producto)
        existing_result = list(bundle_details_coll.aggregate(existing_pipeline))

        if existing_result:
            # Actualizar cantidad si ya existe
            existing_detail = existing_result[0]
            new_quantity = existing_detail["quantity"] + product_data.quantity
            bundle_details_coll.update_one(
                {"_id": ObjectId(existing_detail["bundle_detail_id"])},
                {"$set": {"quantity": new_quantity}}
            )
            detail_id = existing_detail["bundle_detail_id"]
            final_quantity = new_quantity
        else:
            # Crear nuevo detalle del bundle
            bundle_detail = BundleDetail(
                id_bundle=bundle_id,
                id_producto=product_data.id_producto,
                quantity=product_data.quantity
            )
            
            bundle_detail_dict = bundle_detail.model_dump(exclude={"id"})
            inserted = bundle_details_coll.insert_one(bundle_detail_dict)
            detail_id = str(inserted.inserted_id)
            final_quantity = product_data.quantity

        # Retornar información del producto agregado
        return {
            "message": "Product added to bundle successfully",
            "bundle_detail_id": detail_id,
            "bundle_id": bundle_id,
            "product_id": product_data.id_producto,
            "product_name": product["name"],
            "quantity": final_quantity,
            "product_cost": product["cost"]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding product to bundle: {str(e)}")

async def remove_product_from_bundle(bundle_id: str, bundle_detail_id: str) -> dict:
    """Remover un producto del bundle"""
    try:
        # Validar bundle y obtener detalle del bundle con información del producto en una sola pipeline
        bundle_detail_pipeline = get_bundle_detail_with_product_pipeline(bundle_id, bundle_detail_id)
        bundle_detail_result = list(bundle_details_coll.aggregate(bundle_detail_pipeline))
        
        if not bundle_detail_result:
            raise HTTPException(status_code=404, detail="Product not found in bundle")

        bundle_detail = bundle_detail_result[0]

        # Eliminar el detalle del bundle
        result = bundle_details_coll.delete_one({"_id": ObjectId(bundle_detail_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Product not found in bundle")

        return {
            "message": "Product removed from bundle successfully",
            "bundle_id": bundle_detail["id_bundle"],
            "product_id": bundle_detail["id_producto"],
            "product_name": bundle_detail["product_name"],
            "removed_quantity": bundle_detail["quantity"]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error removing product from bundle: {str(e)}")
