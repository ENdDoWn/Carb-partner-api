from database.mongodb import mongodb
from bson import ObjectId
from datetime import datetime

class AdminRepository:
    def __init__(self):
        self.user_profile = mongodb.get_collection("user_profile")
        self.carb = mongodb.get_collection("carb-logs")
        self.blood = mongodb.get_collection("blood-sugar-logs")

    async def find_latest_user_profile(self) -> dict | None:
        user = await self.user_profile.find_one(sort=[("created_at", -1), ("_id", -1)])
        if user:
            user["_id"] = str(user["_id"])
        return user

    async def find_user_profile(self, user_id: str) -> dict | None:
        try:
            user = await self.user_profile.find_one({"_id": ObjectId(user_id)})
        except Exception:
            return None

        if user:
            user["_id"] = str(user["_id"])
        return user

    async def find_carb_logs_by_range(self, user_id: str, start_at: datetime, end_at: datetime) -> list:
        cursor = self.carb.find(
            {
                "user_id": user_id,
                "created_at": {"$gte": start_at, "$lt": end_at},
            }
        ).sort("created_at", 1)
        logs = []
        async for document in cursor:
            document["_id"] = str(document["_id"])
            logs.append(document)
        return logs

    async def find_blood_sugar_logs_by_range(self, user_id: str, start_at: datetime, end_at: datetime) -> list:
        cursor = self.blood.find(
            {
                "user_id": user_id,
                "created_at": {"$gte": start_at, "$lt": end_at},
            }
        ).sort("created_at", 1)
        logs = []
        async for document in cursor:
            document["_id"] = str(document["_id"])
            logs.append(document)
        return logs

    async def list_users(self, limit: int = 50) -> list:
        cursor = self.user_profile.find(
            {},
            {
                "full_name": 1,
                "username": 1,
                "email": 1,
                "created_at": 1,
            },
        ).sort("created_at", -1).limit(limit)
        users = []
        async for document in cursor:
            document["_id"] = str(document["_id"])
            users.append(document)
        return users
