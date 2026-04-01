from repositories.health_repo import HealthRepository

class HealthService:
    def __init__(self):
        self.health_repo = HealthRepository()

    async def add_sugars(self, info_data: dict, user_id: str):
        result = await self.health_repo.insert_sugar(info_data, user_id)
        if not result:
            raise ValueError("Failed to add sugar data")
        return "OK"

    async def add_carbs(self, info_data: dict, user_id: str):
        result = await self.health_repo.insert_carb(info_data, user_id)
        if not result:
            raise ValueError("Failed to add carb data")
        return "OK"

    async def get_blood_sugar_report(self, user_id: str):
        report = await self.health_repo.find_blood_sugar_report(user_id)
        # If report is empty, return empty list instead of error dict for consistency
        return report or []

    async def get_carb_report(self, user_id: str):
        report = await self.health_repo.find_carb_report(user_id)
        # If report is empty, return empty list instead of error dict for consistency
        return report or []
