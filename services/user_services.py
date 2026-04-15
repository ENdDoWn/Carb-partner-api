from fastapi import Depends, HTTPException, status
from repositories.user_repo import UserRepository
from core.config import settings
from datetime import date

class UserService:
    def __init__(self):
        self.repository = UserRepository()

    def _calculate_carb_expect(self, sex: str, active: str, weight: float, height: float, age: int) -> float | None:
        try:
            sex_normalized = str(sex or "").strip().lower()
            active_normalized = str(active or "").strip().lower()

            if sex_normalized == "male":
                bmr = 66 + (13.7 * weight) + (5 * height) - (6.8 * age)
            elif sex_normalized == "female":
                bmr = 665 + (9.6 * weight) + (1.8 * height) - (4.7 * age)
            else:
                return None

            activity_factor_map = {
                "low": 1.375,
                "medium": 1.55,
                "high": 1.725,
            }
            activity_factor = activity_factor_map.get(active_normalized)
            if activity_factor is None:
                return None

            tdee = bmr * activity_factor
            carb_kcal = tdee * 0.20
            carb_grams = carb_kcal / 4
            return round(carb_grams, 2)
        except Exception:
            return None

    def _calculate_age_from_birth_date(self, birth_date_str: str) -> int | None:
        if not birth_date_str or not isinstance(birth_date_str, str):
            return None
        try:
            day_str, month_str, year_str = birth_date_str.split("/")
            day = int(day_str)
            month = int(month_str)
            year = int(year_str)

            # Support Thai Buddhist Era (B.E.) years like 2542 by converting to C.E.
            if year > 2400:
                year -= 543

            birth_dt = date(year, month, day)
            today = date.today()
            age = today.year - birth_dt.year - ((today.month, today.day) < (birth_dt.month, birth_dt.day))
            return max(age, 0)
        except Exception:
            return None

    async def add_additional_info(self, user_id: str, info_data: dict) -> dict:
        payload = dict(info_data or {})
        try:
            height = float(payload.get("height"))
            weight = float(payload.get("weight"))
            if height > 0 and weight > 0:
                height_m = height / 100.0
                bmi = weight / (height_m * height_m)
                payload["bmi"] = round(bmi, 2)

                carb_expect = self._calculate_carb_expect(
                    payload.get("sex"),
                    payload.get("active"),
                    weight,
                    height,
                    self._calculate_age_from_birth_date(payload.get("birth_date")) or 0,
                )
                if carb_expect is not None:
                    payload["carb_expect"] = carb_expect
        except Exception as e:
            print("Error calculating BMI, skipping BMI calculation:", str(e))
        payload["has_profile"] = True
        updated_user = await self.repository.update_additional_info(user_id, payload)
        if not updated_user:
            raise ValueError("Failed to update user info")
        return updated_user

    async def update_profile(self, data_profile: dict, user_id: str) -> dict:
        payload = dict(data_profile or {})
        updated_user = await self.repository.update_profile(user_id, payload)
        if not updated_user:
            raise ValueError("Failed to update user profile")
        return updated_user
