from fastapi import Depends, HTTPException, status
from repositories.user_repo import UserRepository
from core.config import settings

class UserService:
    def __init__(self):
        self.repository = UserRepository()

    async def add_additional_info(self, user_id: str, info_data: dict) -> dict:
        payload = dict(info_data or {})
        try:
            height = float(payload.get("height"))
            weight = float(payload.get("weight"))
            if height > 0 and weight > 0:
                height_m = height / 100.0
                bmi = weight / (height_m * height_m)
                payload["bmi"] = round(bmi, 2)
        except Exception as e:
            print("Error calculating BMI, skipping BMI calculation:", str(e))
        payload["has_profile"] = True
        updated_user = await self.repository.update_additional_info(user_id, payload)
        if not updated_user:
            raise Exception("Failed to update user info")
        return updated_user

    async def update_profile(self, data_profile: dict, user_id: str) -> dict:
        updated_user = await self.repository.update_profile(user_id, data_profile)
        if not updated_user:
            raise Exception("Failed to update user profile")
        return updated_user
