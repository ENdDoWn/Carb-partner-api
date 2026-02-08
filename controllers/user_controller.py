from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from services.auth_services import AuthService
from services.user_services import UserService

router = APIRouter()

@router.get("/users/me/")
async def read_users_me(user: dict = Depends(AuthService.get_current_user)):
    return {"user": user}


class UserInfoRequest(BaseModel):
    sex: str
    active: str
    height: float
    weight: float
    birth_date: str

@router.post("/users/add_info/")
async def add_user_info(
    info_body: UserInfoRequest, 
    current_user: dict = Depends(AuthService.get_current_user)
):  
    try:
        result = await UserService().add_additional_info(current_user["id"], info_body.model_dump())
        if not result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to add user info",
            )
        return "OK"
    except Exception as e:
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
