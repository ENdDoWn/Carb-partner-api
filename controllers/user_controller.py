from fastapi import APIRouter, Depends, HTTPException, status
from services.auth_services import AuthService

router = APIRouter()

@router.get("/users/me/")
async def read_users_me(user: dict = Depends(AuthService.get_current_user)):
    return {"user": user}

