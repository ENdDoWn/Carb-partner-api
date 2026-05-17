from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
from repositories.admin_repo import AdminRepository

class AdminService:
    def __init__(self):
        self.admin_repo = AdminRepository()
        self.tz = ZoneInfo("Asia/Bangkok")

    async def get_dashboard(self, from_date: str, to_date: str, user_id: str | None = None) -> dict:
        if not from_date or not to_date:
            raise ValueError("from and to are required")

        start_date = self._parse_date(from_date)
        end_date = self._parse_date(to_date)
        if end_date < start_date:
            raise ValueError("to must be after from")

        start_at = datetime.combine(start_date, time.min, tzinfo=self.tz)
        end_at = datetime.combine(end_date, time.min, tzinfo=self.tz) + timedelta(days=1)

        if user_id:
            user = await self.admin_repo.find_user_profile(user_id)
        else:
            user = await self.admin_repo.find_latest_user_profile()

        if not user:
            raise ValueError("User not found")

        resolved_user_id = user.get("_id")
        carb_logs = await self.admin_repo.find_carb_logs_by_range(resolved_user_id, start_at, end_at)
        sugar_logs = await self.admin_repo.find_blood_sugar_logs_by_range(resolved_user_id, start_at, end_at)

        last_active = self._resolve_last_active(carb_logs, sugar_logs)
        profile = self._build_profile_payload(user, last_active)

        return {
            "profile": profile,
            "carb_logs": [self._normalize_carb_log(item) for item in carb_logs],
            "blood_sugar_logs": [self._normalize_sugar_log(item) for item in sugar_logs],
        }

    async def list_users(self, limit: int = 50) -> list:
        safe_limit = max(1, min(limit, 200))
        users = await self.admin_repo.list_users(safe_limit)
        return [
            {
                "id": user.get("_id"),
                "name": user.get("full_name") or user.get("username") or user.get("name"),
                "full_name": user.get("full_name"),
                "username": user.get("username"),
                "email": user.get("email"),
                "created_at": self._format_datetime(user.get("created_at")),
            }
            for user in users
        ]

    def _parse_date(self, value: str):
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except Exception:
            raise ValueError("Invalid date format. Use yyyy-mm-dd")

    def _resolve_last_active(self, carb_logs: list, sugar_logs: list) -> str | None:
        timestamps = []
        for item in carb_logs + sugar_logs:
            created_at = item.get("created_at")
            if isinstance(created_at, datetime):
                timestamps.append(created_at)
        if not timestamps:
            return None
        latest = max(timestamps)
        return latest.isoformat()

    def _build_profile_payload(self, user: dict, last_active: str | None) -> dict:
        return {
            "id": user.get("_id"),
            "name": user.get("full_name") or user.get("username") or user.get("name"),
            "full_name": user.get("full_name"),
            "username": user.get("username"),
            "email": user.get("email"),
            "phone": user.get("phone") or user.get("phone_number"),
            "weight": user.get("weight"),
            "height": user.get("height"),
            "age": user.get("age"),
            "birth_date": user.get("birth_date"),
            "sex": user.get("sex"),
            "active": user.get("active"),
            "bmi": user.get("bmi"),
            "carb_expect": user.get("carb_expect"),
            "chronic_conditions": user.get("chronic_conditions"),
            "has_profile": user.get("has_profile"),
            "last_active": last_active,
        }

    def _normalize_carb_log(self, item: dict) -> dict:
        return {
            "created_at": self._format_datetime(item.get("created_at")),
            "amount": item.get("amount"),
            "food_type": item.get("food_type"),
            "carb": item.get("carb"),
            "meal_key": item.get("meal_key"),
        }

    def _normalize_sugar_log(self, item: dict) -> dict:
        return {
            "created_at": self._format_datetime(item.get("created_at")),
            "sugar_level": item.get("sugar_level"),
        }

    def _format_datetime(self, value):
        if isinstance(value, datetime):
            return value.isoformat()
        return value
