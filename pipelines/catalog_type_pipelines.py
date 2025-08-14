from bson import ObjectId

def get_catalog_type_pipeline() -> list:
    return [
        {
            "$addFields": {
                "id": {"$toString": "$_id"}
            }
        },{
            "$lookup": {
                "from": "catalogs",
                "localField": "id",
                "foreignField": "id_catalog_type",
                "as": "result"
            }
        },{
            "$group": {
                "_id": {
                    "id": "$id",
                    "description": "$description",
                    "active": "$active"
                },
                "number_of_products": {
                    "$sum": {"$size": "$result"}
                }
            }
        },{
            "$project": {
                "_id": 0,
                "id": "$_id.id",
                "description": "$_id.description",
                "active": "$_id.active",
                "number_of_products": 1
            }
        }
    ]


def validate_type_is_assigned_pipeline(id: str) -> list:
    return [
        {
            "$match": {
                "_id": ObjectId(id),
            }
        },{
            "$addFields": {
                "id": {"$toString": "$_id"}
            }
        },{
            "$lookup": {
                "from": "catalogs",
                "localField": "id",
                "foreignField": "id_catalog_type",
                "as": "result"
            }
        },{
            "$group": {
                "_id": {
                    "id": "$id",
                    "description": "$description",
                    "active": "$active"
                },
                "number_of_products": {
                    "$sum": {"$size": "$result"}
                }
            }
        },{
            "$project": {
                "_id": 0,
                "id": "$_id.id",
                "description": "$_id.description",
                "active": "$_id.active",
                "number_of_products": 1
            }
        }
    ]