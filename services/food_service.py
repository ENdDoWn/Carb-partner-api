import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted
import base64
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from core.config import settings
from typing import Dict, Any
from repositories.health_repo import HealthRepository

class FoodService:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
        self.health_repo = HealthRepository()
        self.tz = ZoneInfo("Asia/Bangkok")

    def _derive_meal_key_from_time(self, value: datetime | None = None) -> str:
        current_time = (value or datetime.now(self.tz)).astimezone(self.tz).time()
        if current_time < datetime.strptime("10:30", "%H:%M").time():
            return "breakfast"
        if current_time < datetime.strptime("15:00", "%H:%M").time():
            return "lunch"
        if current_time < datetime.strptime("21:00", "%H:%M").time():
            return "dinner"
        return "snack"

    async def confirm_food_upload(
        self,
        result_data: Dict[str, Any],
        user_id: str,
        meal_key: str | None = None,
    ) -> Dict[str, Any]:
        try:
            carbs_estimate = float(result_data.get("carbs_estimate_g", 0))
            food_type = result_data.get("food_type", "ไม่ทราบประเภทอาหาร")
            resolved_meal_key = meal_key or self._derive_meal_key_from_time()

            if carbs_estimate == 0 and food_type == "ไม่ทราบประเภทอาหาร":
                return result_data

            carb_log_data = {
                "amount": 1,
                "food_type": food_type,
                "carb": carbs_estimate,
                "meal_key": resolved_meal_key,
            }

            inserted_id = await self.health_repo.insert_carb(carb_log_data, user_id)
            return {
                "message": "OK",
                "inserted_id": str(inserted_id),
                "result": result_data,
                "meal_key": resolved_meal_key,
            }
        except Exception as e:
            raise Exception(f"Failed to confirm and save food image result: {str(e)}")

    async def analyze_food_image(self, base64_image: str, user_id: str) -> Dict[str, Any]:
        try:
            # Check if base64 string has prefix
            if "base64," in base64_image:
                base64_image = base64_image.split("base64,")[1]
            
            image_bytes = base64.b64decode(base64_image)
            
            prompt = """
            You are an expert clinical dietitian. Analyze the provided food image and estimate its total carbohydrate content in grams for a diabetic patient.

            Provide the result strictly in JSON format with ONLY the following field:
            - "carbs_estimate_g": Estimated total carbohydrate content in grams (number).
            - "food_type": ชื่อเมนูอาหารเป็นภาษาไทยแบบสั้นและชัดเจน เช่น "ข้าวผัด", "ผัดกะเพรา", "ข้าวมันไก่", "ก๋วยเตี๋ยวเรือ", "สลัดผัก", "แกงจืดเต้าหู้".

            Important rules for "food_type":
            - Use the specific dish name, not a generic category.
            - Do NOT return generic words like "ข้าว", "ขนมปัง", "ผลไม้" unless the image truly shows only plain rice/bread/fruit.
            - If you cannot confidently identify the dish, use "ไม่ทราบประเภทอาหาร".

            Do not include any other fields such as food name, confidence, or description.
            Do not include any markdown formatting (like ```json), explanations, units, or extra text.
            Return ONLY the raw, valid JSON object.
            """
            
            # Prepare image part for Gemini
            image_part = {
                "mime_type": "image/jpeg",
                "data": image_bytes
            }
            
            response = await self.model.generate_content_async([prompt, image_part])
            text_response = response.text
            if "```json" in text_response:
                text_response = text_response.split("```json")[1].split("```")[0].strip()
            elif "```" in text_response:
                text_response = text_response.split("```")[1].split("```")[0].strip()

            result = json.loads(text_response)
            print("AI food analysis result:", result)
            return result
        except ResourceExhausted as e:
            print("Gemini rate limit exceeded:", str(e))
            raise Exception(f"Failed to analyze food image: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to analyze food image: {str(e)}")
