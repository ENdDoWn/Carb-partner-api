from repositories.health_repo import HealthRepository

class HealthService:
    def __init__(self):
        self.health_repo = HealthRepository()

    async def add_sugars(self, info_data: dict, user_id: str):
        result = await self.health_repo.insert_sugar(info_data, user_id)
        if not result:
            return {"error": "Failed to add sugar data"}
        print(result)
        return "OK"

    async def add_carbs(self, info_data: dict, user_id: str):
        result = await self.health_repo.insert_carb(info_data, user_id)
        if not result:
            return {"error": "Failed to add carb data"}
        return "OK"
