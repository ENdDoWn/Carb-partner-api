from fastapi import APIRouter, Depends, HTTPException, status
from services.auth_services import AuthService
from services.food_service import FoodService
from pydantic import BaseModel
from typing import Any, Dict

router = APIRouter()

class AnalyzeFoodRequest(BaseModel):
    image_base64: str

class ConfirmFoodUploadRequest(BaseModel):
    result: Dict[str, Any]

@router.post("/food/analyze/")
async def analyze_food(
    payload: AnalyzeFoodRequest,
    current_user: dict = Depends(AuthService.get_current_user),
    food_service: FoodService = Depends(FoodService)
):
    try:
        result = await food_service.analyze_food_image(payload.image_base64, current_user["id"])
        return {
            "message": "OK",
            "result": result
        }
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        print("Error :", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/food/confirm_food/")
async def confirm_food_upload(
    payload: ConfirmFoodUploadRequest,
    current_user: dict = Depends(AuthService.get_current_user),
    food_service: FoodService = Depends(FoodService)
):
    try:
        return await food_service.confirm_food_upload(payload.result, current_user["id"])
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        print("Error :", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
