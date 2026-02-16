from fastapi import Depends, HTTPException, status
from repositories.user_repo import UserRepository
from core.config import settings
from datetime import date

class UserService:
    def __init__(self):
        self.repository = UserRepository()

    def _calculate_age_from_birth_date(self, birth_date_str: str) -> int | None:
        if not birth_date_str or not isinstance(birth_date_str, str):
            return None
        try:
            day_str, month_str, year_str = birth_date_str.split("/")
            day = int(day_str)
            month = int(month_str)
            year = int(year_str)
            if year >= 2400:
                year -= 543
            birth_dt = date(year, month, day)
            today = date.today()
            age = today.year - birth_dt.year - ((today.month, today.day) < (birth_dt.month, birth_dt.day))
            return max(age, 0)
        except Exception:
            return None

    async def add_additional_info(self, user_id: str, info_data: dict) -> dict:
        payload = dict(info_data or {})
        age = self._calculate_age_from_birth_date(payload.get("birth_date"))
        if age is not None:
            payload["age"] = age
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
        payload = dict(data_profile or {})
        if "birth_date" in payload:
            age = self._calculate_age_from_birth_date(payload.get("birth_date"))
            if age is not None:
                payload["age"] = age
        updated_user = await self.repository.update_profile(user_id, data_profile)
        if not updated_user:
            raise Exception("Failed to update user profile")
        return updated_user
