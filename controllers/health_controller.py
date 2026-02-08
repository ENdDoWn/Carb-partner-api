from fastapi import APIRouter, Depends
from pydantic import BaseModel
from services.auth_services import AuthService
from services.health_services import HealthService

router = APIRouter()

class SugarLevelRequest(BaseModel):
    sugar_level: float

class CarbInfoRequest(BaseModel):
    amount: int
    food_type: str
    carb: float

@router.post("/add_sugars")
async def add_sugar(
    sugar_level_request: SugarLevelRequest,
    health_service: HealthService = Depends(HealthService),
    current_user: dict = Depends(AuthService.get_current_user)
):
    return await health_service.add_sugars(sugar_level_request.model_dump(), current_user["id"])

@router.post("/add_carbs")
async def add_carbs(
    carb_info_request: CarbInfoRequest,
    health_service: HealthService = Depends(HealthService),
    current_user: dict = Depends(AuthService.get_current_user)
):
    return await health_service.add_carbs(carb_info_request.model_dump(), current_user["id"])
