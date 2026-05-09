from fastapi import Depends, HTTPException, status
from repositories.user_repo import UserRepository
from core.config import settings
from datetime import date

class UserService:
    def __init__(self):
        self.repository = UserRepository()

    def _normalize_chronic_conditions(self, raw_value) -> dict | None:
        if not isinstance(raw_value, dict):
            return None

        def _as_bool(value) -> bool:
            return bool(value) if isinstance(value, bool) else str(value).strip().lower() == "true"

        def _as_int(value) -> int | None:
            try:
                return int(str(value).strip())
            except Exception:
                return None

        def _normalize_condition(value) -> dict:
            if not isinstance(value, dict):
                return {"selected": False, "duration": None}
            return {
                "selected": _as_bool(value.get("selected")),
                "duration": _as_int(value.get("duration")),
            }

        normalized = {
            "diabetes": _normalize_condition(raw_value.get("diabetes")),
            "hypertension": _normalize_condition(raw_value.get("hypertension")),
            "hyperlipidemia": _normalize_condition(raw_value.get("hyperlipidemia")),
            "none": _as_bool(raw_value.get("none")),
        }

        other_raw = raw_value.get("other")
        if isinstance(other_raw, dict):
            diseases_raw = other_raw.get("diseases")
            diseases = []
            if isinstance(diseases_raw, list):
                for disease in diseases_raw:
                    if not isinstance(disease, dict):
                        continue
                    name = str(disease.get("name") or "").strip()
                    if not name:
                        continue
                    diseases.append({
                        "name": name,
                        "duration": _as_int(disease.get("duration")),
                    })
            normalized["other"] = {
                "selected": _as_bool(other_raw.get("selected")),
                "diseases": diseases,
            }
        else:
            normalized["other"] = {"selected": False, "diseases": []}

        return normalized

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
        chronic_conditions = self._normalize_chronic_conditions(payload.get("chronic_conditions"))
        if chronic_conditions is not None:
            payload["chronic_conditions"] = chronic_conditions
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

        current_profile = await self.repository.get_user_profile(user_id)
        if current_profile is None:
            raise ValueError("User profile not found")

        def _as_float(value):
            try:
                return float(value)
            except Exception:
                return None

        weight_changed = False
        if "weight" in payload:
            new_weight = _as_float(payload.get("weight"))
            old_weight = _as_float(current_profile.get("weight"))
            if new_weight is None or old_weight is None:
                weight_changed = payload.get("weight") != current_profile.get("weight")
            else:
                weight_changed = new_weight != old_weight

        height_changed = False
        if "height" in payload:
            new_height = _as_float(payload.get("height"))
            old_height = _as_float(current_profile.get("height"))
            if new_height is None or old_height is None:
                height_changed = payload.get("height") != current_profile.get("height")
            else:
                height_changed = new_height != old_height

        active_changed = False
        if "active" in payload:
            new_active = str(payload.get("active") or "").strip().lower()
            old_active = str(current_profile.get("active") or "").strip().lower()
            active_changed = new_active != old_active

        should_recalculate = weight_changed or height_changed or active_changed

        if should_recalculate:
            try:
                effective_weight = float(payload.get("weight", current_profile.get("weight")))
                effective_height = float(payload.get("height", current_profile.get("height")))
                if effective_height > 0 and effective_weight > 0:
                    height_m = effective_height / 100.0
                    payload["bmi"] = round(effective_weight / (height_m * height_m), 2)

                    carb_expect = self._calculate_carb_expect(
                        payload.get("sex", current_profile.get("sex")),
                        payload.get("active", current_profile.get("active")),
                        effective_weight,
                        effective_height,
                        self._calculate_age_from_birth_date(
                            payload.get("birth_date", current_profile.get("birth_date"))
                        ) or 0,
                    )
                    if carb_expect is not None:
                        payload["carb_expect"] = carb_expect
            except Exception as e:
                print("Error recalculating BMI/carb_expect, using incoming payload values:", str(e))

        updated_user = await self.repository.update_profile(user_id, payload)
        if not updated_user:
            raise ValueError("Failed to update user profile")
        return updated_user
