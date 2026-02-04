import httpx
from fastapi import HTTPException, status
from core.config import settings

class OAuthService:
    @staticmethod
    async def verify_line_token(code: str):
        async with httpx.AsyncClient() as client:
            token_resp = await client.post(
                "https://api.line.me/oauth2/v2.1/token",
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": settings.LINE_REDIRECT_URI,
                    "client_id": settings.LINE_CHANNEL_ID,
                    "client_secret": settings.LINE_CHANNEL_SECRET,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            if token_resp.status_code != 200:
                print("LINE login failed:", token_resp.text)
                raise HTTPException(status_code=400, detail="LINE login failed: Invalid code or config")

            token_data = token_resp.json()
            access_token = token_data.get("access_token")
            id_token = token_data.get("id_token")
            profile_resp = await client.get(
                "https://api.line.me/v2/profile",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            if profile_resp.status_code != 200:
                 raise HTTPException(status_code=400, detail="Failed to get LINE profile")
            profile = profile_resp.json()
            email = None
            if id_token:
                try:
                    verify_resp = await client.post(
                        "https://api.line.me/oauth2/v2.1/verify",
                        data={
                            "id_token": id_token,
                            "client_id": settings.LINE_CHANNEL_ID
                        }
                    )
                    if verify_resp.status_code == 200:
                        email = verify_resp.json().get("email")
                except Exception as e:
                    print(f"Error decoding LINE email: {e}")
            return profile.get("userId"), profile.get("displayName"), profile.get("pictureUrl"), email

    @staticmethod
    async def verify_google_token(id_token: str):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://oauth2.googleapis.com/tokeninfo",
                params={"id_token": id_token}
            )
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="Google token verification failed")
            
            data = response.json()
            return data.get("sub"), data.get("name"), data.get("picture"), data.get("email")

    @staticmethod
    async def verify_facebook_token(access_token: str):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://graph.facebook.com/me",
                params={
                    "access_token": access_token,
                    "fields": "id,name,email,picture.type(large)"
                }
            )
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="Facebook token verification failed")
            
            data = response.json()
            picture = data.get("picture", {}).get("data", {}).get("url")
            return data.get("id"), data.get("name"), picture

def get_oauth_service() -> OAuthService:
    return OAuthService()