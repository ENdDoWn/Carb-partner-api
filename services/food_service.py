import google.generativeai as genai
import base64
import json
from core.config import settings
from typing import Dict, Any
from repositories.health_repo import HealthRepository

class FoodService:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel("gemini-2.5-flash")
        self.health_repo = HealthRepository()

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
            - "food_type": A brief classification of the food (e.g., "rice", "bread", "fruit", etc.) if identifiable, otherwise "unknown".

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
            carb_log_data = {
                "amount": 1, 
                "food_type": result.get("food_type", "unknown"),
                "carb": float(result.get("carbs_estimate_g", 0))
            }
            
            await self.health_repo.insert_carb(carb_log_data, user_id)
            
            return result
        except Exception as e:
            raise Exception(f"Failed to analyze and save food image: {str(e)}")
