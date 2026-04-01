from fastapi import APIRouter, Depends, HTTPException, status, Body
from pydantic import BaseModel, ConfigDict
from typing import Optional
from services.auth_services import AuthService
from services.user_services import UserService

router = APIRouter()

@router.get("/users/me/")
async def read_users_me(user: dict = Depends(AuthService.get_current_user)):
    try:
        return {"user": user}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error"
        )

class UserInfoRequest(BaseModel):
    sex: str
    active: str
    height: float
    weight: float
    birth_date: str

class UpdateProfileRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    email: Optional[str] = None
    sex: Optional[str] = None
    active: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    birth_date: Optional[str] = None
    carbGoal: Optional[float] = None
    bmi: Optional[float] = None

@router.post("/users/add_info/")
async def add_user_info(
    info_body: UserInfoRequest, 
    current_user: dict = Depends(AuthService.get_current_user)
):  
    try:
        payload = info_body.model_dump()
        result = await UserService().add_additional_info(current_user["id"], payload)
        if not result:
            raise ValueError("Failed to add user info")
        return "OK"
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )

@router.post("/users/update_profile/")
async def update_profile(
    payload: dict = Body(...),
    current_user: dict = Depends(AuthService.get_current_user),
    user_service: UserService = Depends(UserService)
):
    try:
        data = payload.get("user") if isinstance(payload, dict) and isinstance(payload.get("user"), dict) else payload
        parsed = UpdateProfileRequest(**data)
        update_data = parsed.model_dump(exclude_unset=True, exclude_none=True)
        extra = parsed.model_extra or {}
        update_data = {**extra, **update_data}
        result = await user_service.update_profile(update_data, current_user["id"])
        if not result:
            raise ValueError("Failed to update user profile")
        return "OK"
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )

