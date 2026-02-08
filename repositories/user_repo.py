from database.mongodb import mongodb
from bson import ObjectId

class UserRepository:
    def __init__(self):
        self.collection = mongodb.get_collection("user_profile")

    async def update_additional_info(self, user_id: str, info_data: dict) -> dict:
        update_result = await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": info_data}
        )
        return update_result.modified_count
