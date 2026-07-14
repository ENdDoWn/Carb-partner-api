from database.mongodb import mongodb
from bson import ObjectId
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

class HealthRepository:
    def __init__(self):
        self.blood = mongodb.get_collection("blood-sugar-logs")
        self.carb = mongodb.get_collection("carb-logs")
        self.user_profile = mongodb.get_collection("user_profile")

    async def has_sugar_log_today(self, user_id: str) -> bool:
        """Check if the user already has a blood sugar log for today (Asia/Bangkok)."""
        tz = ZoneInfo("Asia/Bangkok")
        now_bkk = datetime.now(tz)
        start_of_day = now_bkk.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        count = await self.blood.count_documents({
            "user_id": user_id,
            "created_at": {"$gte": start_of_day, "$lt": end_of_day},
        })
        return count > 0

    async def insert_sugar(self, sugar_data: dict, user_id: str) -> dict:
        sugar_data["created_at"] = datetime.now(ZoneInfo("Asia/Bangkok"))
        sugar_data["user_id"] = user_id
        result = await self.blood.insert_one(sugar_data)
        return result.inserted_id

    async def insert_carb(self, carb_data: dict, user_id: str) -> dict:
        carb_data["created_at"] = datetime.now(ZoneInfo("Asia/Bangkok"))
        carb_data["user_id"] = user_id
        result = await self.carb.insert_one(carb_data)
        return result.inserted_id

    async def find_blood_sugar_report(self, user_id: str) -> list:
        cursor = self.blood.find({"user_id": user_id}).sort("created_at", -1)
        report = []
        async for document in cursor:
            document["_id"] = str(document["_id"])
            report.append(document)
        return report

    async def find_carb_report(self, user_id: str) -> list:
        cursor = self.carb.find({"user_id": user_id}).sort("created_at", -1)
        report = []
        async for document in cursor:
            document["_id"] = str(document["_id"])
            report.append(document)
        return report

    async def find_blood_sugar_by_range(self, user_id: str, start_at: datetime, end_at: datetime) -> list:
        cursor = self.blood.find(
            {
                "user_id": user_id,
                "created_at": {"$gte": start_at, "$lt": end_at},
            }
        ).sort("created_at", 1)
        report = []
        async for document in cursor:
            document["_id"] = str(document["_id"])
            report.append(document)
        return report

    async def find_carb_by_range(self, user_id: str, start_at: datetime, end_at: datetime) -> list:
        cursor = self.carb.find(
            {
                "user_id": user_id,
                "created_at": {"$gte": start_at, "$lt": end_at},
            }
        ).sort("created_at", 1)
        report = []
        async for document in cursor:
            document["_id"] = str(document["_id"])
            report.append(document)
        return report

    async def find_user_carb_goal(self, user_id: str) -> float:
        try:
            user = await self.user_profile.find_one({"_id": ObjectId(user_id)})
        except Exception:
            return 0.0

        if not user:
            return 0.0

        if user.get("carbGoal") is not None:
            try:
                return float(user.get("carbGoal"))
            except Exception:
                return 0.0

        if user.get("carb_expect") is not None:
            try:
                return float(user.get("carb_expect"))
            except Exception:
                return 0.0

        return 0.0
