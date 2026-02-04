from fastapi import APIRouter, Depends, HTTPException, Body
from services.auth_services import AuthService
from services.oauth_service import OAuthService, get_oauth_service
from repositories.auth_repo import AuthRepository

router = APIRouter()

@router.post("/line/login")
async def login_with_line(
    code: str = Body(..., embed=True),
    oauth_service: OAuthService = Depends(get_oauth_service)
):
    line_id, name, picture, email = await oauth_service.verify_line_token(code)
    repo = AuthRepository()
    user = await repo.find_by_line_id(line_id)
    if not user:
        social_data = {
            "name": name,
            "email": email,
            "line": {
                "userId": line_id,
                "displayName": name,
                "picture": picture
            }
        }
        user = await repo.create_social_user(provider="line", profile_data=social_data)
    auth_service = AuthService()
    access_token = auth_service.create_access_token(data={"sub": str(user["_id"])})
    return {
        "access_token": access_token, 
        "token_type": "bearer", 
        "user_id": str(user["_id"])
    }


@router.post("/google/login")
async def login_with_google(
    id_token: str = Body(..., embed=True),
    oauth_service: OAuthService = Depends(get_oauth_service)
):
    google_sub, name, picture, email = await oauth_service.verify_google_token(id_token)
    repo = AuthRepository()
    user = await repo.find_by_google_sub(google_sub)

    if not user:
        social_data = {
            "name": name,
            "email": email,
            "google": {
                "sub": google_sub,
                "name": name,
                "picture": picture
            }
        }
        user = await repo.create_social_user(provider="google", profile_data=social_data)
    auth_service = AuthService()
    access_token = auth_service.create_access_token(data={"sub": str(user["_id"])})
    
    return {"access_token": access_token, "token_type": "bearer", "user_id": str(user["_id"])}
