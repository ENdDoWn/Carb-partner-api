from repositories.health_repo import HealthRepository
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

class HealthService:
    def __init__(self):
        self.health_repo = HealthRepository()
        self.tz = ZoneInfo("Asia/Bangkok")

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

    async def get_daily_carb_total(self, user_id: str) -> dict:
        now_bkk = datetime.now(self.tz)
        today = now_bkk.date()
        start_at = datetime.combine(today, time.min, tzinfo=self.tz)
        end_at = start_at + timedelta(days=1)

        carb_logs = await self.health_repo.find_carb_by_range(user_id, start_at, end_at)
        total_carb = sum(self._safe_number(item.get("carb")) for item in carb_logs)

        return {
            "date": today.isoformat(),
            "totalCarb": round(total_carb, 2),
            "entries": len(carb_logs),
        }

    async def get_daily_totals_by_date(self, user_id: str, selected_date: str) -> dict:
        try:
            target_date = datetime.strptime(selected_date, "%d/%m/%Y").date()
        except Exception:
            raise ValueError("Invalid date format. Use dd/mm/yyyy")

        start_at = datetime.combine(target_date, time.min, tzinfo=self.tz)
        end_at = start_at + timedelta(days=1)

        carb_logs = await self.health_repo.find_carb_by_range(user_id, start_at, end_at)
        blood_logs = await self.health_repo.find_blood_sugar_by_range(user_id, start_at, end_at)

        total_carb = sum(self._safe_number(item.get("carb")) for item in carb_logs)
        total_blood_sugar = sum(self._safe_number(item.get("sugar_level")) for item in blood_logs)

        return {
            "queryDate": selected_date,
            "totalCarb": round(total_carb, 2),
            "totalBloodSugar": round(total_blood_sugar, 2),
            "carbEntries": len(carb_logs),
            "bloodEntries": len(blood_logs),
        }

    def _to_bkk_datetime(self, value: date) -> datetime:
        return datetime.combine(value, time.min, tzinfo=self.tz)

    def _safe_number(self, value, default: float = 0.0) -> float:
        try:
            return float(value)
        except Exception:
            return default

    def _average(self, values: list[float]) -> float:
        if not values:
            return 0.0
        return sum(values) / len(values)

    def _trend(self, current: float, previous: float, lower_is_better: bool) -> tuple[str, bool]:
        if previous == 0:
            improvement = 0.0
        else:
            raw_change = ((current - previous) / previous) * 100.0
            improvement = -raw_change if lower_is_better else raw_change

        is_positive = improvement >= 0
        trend_text = f"{'+' if improvement >= 0 else '-'}{abs(round(improvement))}%"
        return trend_text, is_positive

    def _target_success_percent(self, sugar_logs: list[dict]) -> float:
        if not sugar_logs:
            return 0.0
        in_range = 0
        for item in sugar_logs:
            sugar = self._safe_number(item.get("sugar_level"))
            if 70 <= sugar <= 180:
                in_range += 1
        return (in_range / len(sugar_logs)) * 100.0

    def _build_day_axis(self) -> tuple[list[str], list[int]]:
        labels = ["06", "09", "12", "15", "18", "21", "24"]
        cutoffs = [6, 9, 12, 15, 18, 21, 24]
        return labels, cutoffs

    def _bucket_index_for_hour(self, hour: int, cutoffs: list[int]) -> int:
        for idx, cutoff in enumerate(cutoffs):
            if hour <= cutoff:
                return idx
        return len(cutoffs) - 1

    def _build_week_labels(self) -> list[str]:
        return ["จ.", "อ.", "พ.", "พฤ.", "ศ.", "ส.", "อา."]

    def _build_month_labels(self) -> list[str]:
        return ["สัปดาห์ 1", "สัปดาห์ 2", "สัปดาห์ 3", "สัปดาห์ 4"]

    def _bucket_week(self, value: datetime, start_dt: datetime) -> int:
        diff_days = (value.date() - start_dt.date()).days
        return max(0, min(6, diff_days))

    def _bucket_month(self, value: datetime) -> int:
        day_num = value.day
        if day_num <= 7:
            return 0
        if day_num <= 14:
            return 1
        if day_num <= 21:
            return 2
        return 3

    def _build_series_points(self, labels: list[str], sugar_values: list[float], carb_values: list[float]) -> tuple[list[dict], dict]:
        sugar_points = [{"x": labels[idx], "value": round(sugar_values[idx], 2)} for idx in range(len(labels))]
        carb_points = [{"x": labels[idx], "value": round(carb_values[idx], 2)} for idx in range(len(labels))]
        highlight_index = 0
        if sugar_values:
            max_value = max(sugar_values)
            highlight_index = sugar_values.index(max_value)

        return (
            [
                {
                    "key": "sugar",
                    "label": "น้ำตาล",
                    "points": sugar_points,
                },
                {
                    "key": "carb",
                    "label": "คาร์บ",
                    "points": carb_points,
                },
            ],
            {"seriesKey": "sugar", "index": highlight_index},
        )

    async def _build_period_payload(self, user_id: str, period: str, anchor_date: date) -> dict:
        if period == "day":
            start = anchor_date
            end = anchor_date + timedelta(days=1)
            prev_start = anchor_date - timedelta(days=1)
            prev_end = anchor_date
            labels, cutoffs = self._build_day_axis()
            comparison_label = "เมื่อวาน"
            goal_multiplier = 1
        elif period == "week":
            start = anchor_date - timedelta(days=anchor_date.weekday())
            end = start + timedelta(days=7)
            prev_start = start - timedelta(days=7)
            prev_end = start
            labels = self._build_week_labels()
            cutoffs = []
            comparison_label = "สัปดาห์ที่แล้ว"
            goal_multiplier = 7
        elif period == "month":
            start = anchor_date.replace(day=1)
            if start.month == 12:
                end = start.replace(year=start.year + 1, month=1)
            else:
                end = start.replace(month=start.month + 1)

            if start.month == 1:
                prev_start = start.replace(year=start.year - 1, month=12)
            else:
                prev_start = start.replace(month=start.month - 1)
            prev_end = start

            labels = self._build_month_labels()
            cutoffs = []
            comparison_label = "เดือนที่แล้ว"
            goal_multiplier = 28
        else:
            raise ValueError("Invalid period. Use day, week, or month.")

        start_dt = self._to_bkk_datetime(start)
        end_dt = self._to_bkk_datetime(end)
        prev_start_dt = self._to_bkk_datetime(prev_start)
        prev_end_dt = self._to_bkk_datetime(prev_end)

        sugar_logs = await self.health_repo.find_blood_sugar_by_range(user_id, start_dt, end_dt)
        carb_logs = await self.health_repo.find_carb_by_range(user_id, start_dt, end_dt)
        prev_sugar_logs = await self.health_repo.find_blood_sugar_by_range(user_id, prev_start_dt, prev_end_dt)
        prev_carb_logs = await self.health_repo.find_carb_by_range(user_id, prev_start_dt, prev_end_dt)

        sugar_values = [0.0 for _ in labels]
        sugar_counts = [0 for _ in labels]
        carb_values = [0.0 for _ in labels]
        carb_counts = [0 for _ in labels]

        for item in sugar_logs:
            created_at = item.get("created_at")
            if not isinstance(created_at, datetime):
                continue
            if period == "day":
                idx = self._bucket_index_for_hour(created_at.hour, cutoffs)
            elif period == "week":
                idx = self._bucket_week(created_at, start_dt)
            else:
                idx = self._bucket_month(created_at)
            sugar_values[idx] += self._safe_number(item.get("sugar_level"))
            sugar_counts[idx] += 1

        for item in carb_logs:
            created_at = item.get("created_at")
            if not isinstance(created_at, datetime):
                continue
            if period == "day":
                idx = self._bucket_index_for_hour(created_at.hour, cutoffs)
            elif period == "week":
                idx = self._bucket_week(created_at, start_dt)
            else:
                idx = self._bucket_month(created_at)
            carb_values[idx] += self._safe_number(item.get("carb"))
            carb_counts[idx] += 1

        sugar_bucket_avg = [
            (sugar_values[idx] / sugar_counts[idx]) if sugar_counts[idx] > 0 else 0.0
            for idx in range(len(labels))
        ]
        carb_bucket_avg = [
            (carb_values[idx] / carb_counts[idx]) if carb_counts[idx] > 0 else 0.0
            for idx in range(len(labels))
        ]

        chart_series, highlight = self._build_series_points(labels, sugar_bucket_avg, carb_bucket_avg)

        current_avg_sugar = self._average([self._safe_number(item.get("sugar_level")) for item in sugar_logs])
        previous_avg_sugar = self._average([self._safe_number(item.get("sugar_level")) for item in prev_sugar_logs])
        sugar_trend_text, sugar_is_positive = self._trend(current_avg_sugar, previous_avg_sugar, lower_is_better=True)

        current_avg_carb = self._average([self._safe_number(item.get("carb")) for item in carb_logs])
        previous_avg_carb = self._average([self._safe_number(item.get("carb")) for item in prev_carb_logs])
        carb_trend_text, carb_is_positive = self._trend(current_avg_carb, previous_avg_carb, lower_is_better=True)

        current_target_success = self._target_success_percent(sugar_logs)
        previous_target_success = self._target_success_percent(prev_sugar_logs)
        target_trend_text, target_is_positive = self._trend(
            current_target_success,
            previous_target_success,
            lower_is_better=False,
        )

        carb_goal_daily = await self.health_repo.find_user_carb_goal(user_id)
        carb_goal_total = round(carb_goal_daily * goal_multiplier, 2)
        carb_consumed_total = round(sum([self._safe_number(item.get("carb")) for item in carb_logs]), 2)

        return {
            "comparisonLabel": comparison_label,
            "chart": {
                "yAxis": {"min": 60, "max": 220, "unit": "mg/dL"},
                "labels": labels,
                "series": chart_series,
                "highlight": highlight,
            },
            "summaryCards": [
                {
                    "id": "avgSugar",
                    "title": "ระดับน้ำตาลในเลือดเฉลี่ย",
                    "value": round(current_avg_sugar, 2),
                    "unit": "มก./ดล.",
                    "trendText": sugar_trend_text,
                    "isPositive": sugar_is_positive,
                },
                {
                    "id": "avgCarb",
                    "title": "ปริมาณคาร์บเฉลี่ย",
                    "value": round(current_avg_carb, 2),
                    "unit": "ก.",
                    "trendText": carb_trend_text,
                    "isPositive": carb_is_positive,
                },
            ],
            "targetSuccess": {
                "percent": round(current_target_success, 2),
                "trendText": target_trend_text,
                "isPositive": target_is_positive,
            },
            "carbGoal": {
                "consumed": carb_consumed_total,
                "goal": carb_goal_total,
                "unit": "ก.",
            },
        }

    async def get_stats(self, user_id: str, period: str, anchor_date: date | None = None) -> dict:
        selected_period = (period or "week").lower()
        selected_date = anchor_date or datetime.now(self.tz).date()
        payload = await self._build_period_payload(user_id, selected_period, selected_date)
        return {
            "period": selected_period,
            "anchorDate": selected_date.isoformat(),
            **payload,
        }
