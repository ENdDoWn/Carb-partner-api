from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from services.auth_services import AuthService, get_auth_service

router = APIRouter()

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    confirm_password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(user: UserRegister, service: AuthService = Depends(get_auth_service)):
    try:
        return await service.register_user(user.model_dump())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/signin")
async def signin(login_data: UserLogin, service: AuthService = Depends(get_auth_service)):
    user = await service.authenticate_user(login_data.model_dump())
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    return {
        "message": "Login successful",
        "access_token": user.get("access_token"),
        "token_type": "bearer",
        "user": user.get("user")
    }
