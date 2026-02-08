from database.mongodb import mongodb
from datetime import datetime

class HealthRepository:
    def __init__(self):
        self.blood = mongodb.get_collection("blood-sugar-logs")
        self.carb = mongodb.get_collection("carb-logs")

    async def insert_sugar(self, sugar_data: dict, user_id: str) -> dict:
        sugar_data["created_at"] = datetime.now()
        sugar_data["user_id"] = user_id
        result = await self.blood.insert_one(sugar_data)
        return result.inserted_id

    async def insert_carb(self, carb_data: dict, user_id: str) -> dict:
        carb_data["created_at"] = datetime.now()
        carb_data["user_id"] = user_id
        result = await self.carb.insert_one(carb_data)
        return result.inserted_id
