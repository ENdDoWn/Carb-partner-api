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

    async def update_profile(self, user_id: str, data_profile: dict) -> dict:
        update_payload = data_profile or {}
        update_result = await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_payload}
        )
        return update_result.modified_count
