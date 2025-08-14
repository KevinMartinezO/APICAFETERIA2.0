from bson import ObjectId

def get_all_orders_pipeline(skip: int = 0, limit: int = 50) -> list:
    """Pipeline para obtener todas las órdenes con información del usuario"""
    return [
        {
            "$lookup": {
                "from": "users",
                "let": {"user_id": {"$toObjectId": "$id_user"}},  # Convertir string a ObjectId para lookup
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$_id", "$$user_id"]}}}
                ],
                "as": "user_info"
            }
        },
        {
            "$project": {
                "id": {"$toString": "$_id"},
                "id_user": "$id_user",  # Ya es string
                "user_name": {"$arrayElemAt": ["$user_info.name", 0]},
                "date": 1,
                "subtotal": 1,
                "taxes": 1,
                "discount": 1,
                "total": 1,
                "_id": 0
            }
        },
        {"$sort": {"date": -1}},
        {"$skip": skip},
        {"$limit": limit}
    ]


def get_orders_by_user_pipeline(user_id: str, skip: int = 0, limit: int = 50) -> list:
    """Pipeline para obtener órdenes de un usuario específico"""
    return [
        {"$match": {"id_user": user_id}},  # Ahora id_user es string
        {
            "$lookup": {
                "from": "users",
                "let": {"user_id": {"$toObjectId": "$id_user"}},  # Convertir string a ObjectId para lookup
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$_id", "$$user_id"]}}}
                ],
                "as": "user_info"
            }
        },
        {
            "$project": {
                "id": {"$toString": "$_id"},
                "id_user": "$id_user",  # Ya es string
                "user_name": {"$arrayElemAt": ["$user_info.name", 0]},
                "date": 1,
                "subtotal": 1,
                "taxes": 1,
                "discount": 1,
                "total": 1,
                "_id": 0
            }
        },
        {"$sort": {"date": -1}},
        {"$skip": skip},
        {"$limit": limit}
    ]


def get_order_by_id_pipeline(order_id: str) -> list:
    """Pipeline para obtener una orden específica con detalles completos"""
    return [
        {"$match": {"_id": ObjectId(order_id)}},
        {
            "$lookup": {
                "from": "users",
                "let": {"user_id": {"$toObjectId": "$id_user"}},  # Convertir string a ObjectId para lookup
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$_id", "$$user_id"]}}}
                ],
                "as": "user_info"
            }
        },
        {
            "$lookup": {
                "from": "order_details",
                "let": {"order_id": {"$toString": "$_id"}},  # Convertir ObjectId a string para lookup
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$id_order", "$$order_id"]}}}
                ],
                "as": "details"
            }
        },
        {
            "$lookup": {
                "from": "order_status_record",
                "let": {"order_id": {"$toString": "$_id"}},  # Convertir ObjectId a string para lookup
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$id_order", "$$order_id"]}}}
                ],
                "as": "status_history"
            }
        },
        {
            "$project": {
                "id": {"$toString": "$_id"},
                "id_user": "$id_user",  # Ya es string
                "user_info": {"$arrayElemAt": ["$user_info", 0]},
                "date": 1,
                "subtotal": 1,
                "taxes": 1,
                "discount": 1,
                "total": 1,
                "details": {
                    "$map": {
                        "input": "$details",
                        "as": "detail",
                        "in": {
                            "id": {"$toString": "$$detail._id"},
                            "id_producto": "$$detail.id_producto",  # Ya es string
                            "quantity": "$$detail.quantity",
                            "active": "$$detail.active",
                            "date_created": "$$detail.date_created",
                            "date_updated": "$$detail.date_updated"
                        }
                    }
                },
                "status_history": {
                    "$map": {
                        "input": "$status_history",
                        "as": "status",
                        "in": {
                            "id": {"$toString": "$$status._id"},
                            "id_status": "$$status.id_status",  # Ya es string
                            "date": "$$status.date"
                        }
                    }
                },
                "_id": 0
            }
        }
    ]


def validate_user_exists_pipeline(user_id: str) -> list:
    """Pipeline para validar que un usuario existe"""
    return [
        {"$match": {"_id": ObjectId(user_id)}},
        {"$project": {"_id": 1}},
        {"$limit": 1}
    ]


def get_order_owner_pipeline(order_id: str):
    """Pipeline para obtener el propietario de una orden"""
    return [
        {"$match": {"_id": ObjectId(order_id)}},
        {"$project": {"id_user": "$id_user"}},  # Ya es string, no necesita conversión
        {"$limit": 1}
    ]


def get_existing_inprogress_order_pipeline(user_id: str):
    """Pipeline para buscar una orden existente en estado 'inprogress' del usuario"""
    return [
        # Buscar órdenes del usuario (ahora id_user es string)
        {"$match": {"id_user": user_id}},

        # Lookup con order_status_record para obtener el estado más reciente
        # Convertimos _id a string para hacer match con id_order (que ahora es string)
        {"$lookup": {
            "from": "order_status_record",
            "let": {"order_id": {"$toString": "$_id"}},
            "pipeline": [
                {"$match": {"$expr": {"$eq": ["$id_order", "$$order_id"]}}},
                {"$sort": {"date": -1}},
                {"$limit": 1}
            ],
            "as": "latest_status_array"
        }},

        # Extraer el estado más reciente
        {"$addFields": {
            "latest_status": {"$arrayElemAt": ["$latest_status_array", 0]}
        }},

        # Solo procesar órdenes que tienen estado
        {"$match": {"latest_status": {"$exists": True}}},

        # Lookup con order_statuses para obtener la descripción del estado
        # Convertimos id_status (string) a ObjectId para hacer match con _id
        {"$lookup": {
            "from": "order_statuses",
            "let": {"status_id": {"$toObjectId": "$latest_status.id_status"}},
            "pipeline": [
                {"$match": {"$expr": {"$eq": ["$_id", "$$status_id"]}}}
            ],
            "as": "status_info"
        }},

        # Filtrar solo órdenes en "inprogress"
        {"$match": {"status_info.description": "inprogress"}},

        # Proyectar solo los campos necesarios
        {"$project": {
            "_id": {"$toString": "$_id"},
            "id_user": "$id_user",  # Ya es string
            "date": 1,
            "subtotal": {"$ifNull": ["$subtotal", 0.0]},
            "taxes": {"$ifNull": ["$taxes", 0.0]},
            "discount": {"$ifNull": ["$discount", 0.0]},
            "total": {"$ifNull": ["$total", 0.0]},
            "status": {"$arrayElemAt": ["$status_info.description", 0]}
        }},

        {"$limit": 1}
    ]

def get_total_sales_by_order_status_pipeline() -> list:
    """Pipeline para obtener la suma total de ventas agrupadas por estado de orden."""
    return [
        {
            "$group": {
                "_id": "$id_order_status",          # Agrupa por estado de orden
                "total_sales": {"$sum": "$total"},  # Suma el campo 'total' de cada orden
                "count": {"$sum": 1}                # Cuenta el número de órdenes por estado
            }
        },
        {
            "$lookup": {
                "from": "order_statuses",           # Une con la colección de estados
                "localField": "_id",
                "foreignField": "_id",
                "as": "order_status"
            }
        },
        {"$unwind": "$order_status"},               # Desenrolla el array de estado
        {
            "$project": {
                "order_status": "$order_status.description",  # Muestra la descripción del estado
                "total_sales": 1,
                "count": 1
            }
        }
    ]


def get_avg_sales_by_user_pipeline() -> list:
    """Pipeline para obtener el promedio de ventas agrupadas por usuario."""
    return [
        {
            "$group": {
                "_id": "$id_user",                   # Agrupa por usuario
                "avg_sales": {"$avg": "$total"},     # Calcula el promedio del campo 'total'
                "count": {"$sum": 1}                 # Cuenta el número de órdenes por usuario
            }
        },
        {
            "$lookup": {
                "from": "users",                     # Une con la colección de usuarios
                "localField": "_id",
                "foreignField": "_id",
                "as": "user"
            }
        },
        {"$unwind": "$user"},                        # Desenrolla el array de usuario
        {
            "$project": {
                "user": "$user.email",               # Muestra el email del usuario
                "avg_sales": 1,
                "count": 1
            }
        }
    ]


def get_order_count_by_status_pipeline() -> list:
    """Pipeline para contar el número de órdenes por estado."""
    return [
        {
            "$group": {
                "_id": "$id_order_status",           # Agrupa por estado de orden
                "order_count": {"$sum": 1}           # Cuenta el número de órdenes por estado
            }
        },
        {
            "$lookup": {
                "from": "order_statuses",            # Une con la colección de estados
                "localField": "_id",
                "foreignField": "_id",
                "as": "order_status"
            }
        },
        {"$unwind": "$order_status"},                # Desenrolla el array de estado
        {
            "$project": {
                "order_status": "$order_status.description",  # Muestra la descripción del estado
                "order_count": 1
            }
        }
    ]
