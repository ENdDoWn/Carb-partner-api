from repositories.auth_repo import AuthRepository
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from jose import jwt
from core.config import settings
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/signin")

class AuthService:
    def __init__(self):
        self.repository = AuthRepository()
        self.crypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def create_access_token(self, data: dict): # JWT Token Generator
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    async def register_user(self, user_data: dict) -> dict:
        existing_user = await self.repository.find_by_email(user_data["email"])
        if existing_user:
            raise ValueError("Email already registered")

        password = str(user_data.get("password", "")).strip()
        confirm_password = str(user_data.get("confirm_password", "")).strip()
        if password != confirm_password:
            raise ValueError("Passwords do not match")

        hashed_password = self.crypt_context.hash(password)
        insert_query = {
            "email": user_data["email"],
            "password": hashed_password
        }
        return await self.repository.create(insert_query)

    async def authenticate_user(self, login_data: dict) -> dict:
        user = await self.repository.find_by_email(login_data["email"])
        if not user or not self.crypt_context.verify(login_data["password"], user["password"]):
            return None
        # JWT Token Creation
        token_data = {"sub": str(user["_id"]), "email": user["email"]}
        access_token = self.create_access_token(token_data)
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": str(user["_id"]),
                "email": user["email"]
            }
        }

    @staticmethod
    async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id: str = payload.get("sub")
            if user_id is None:
                raise credentials_exception
        except Exception: 
            raise credentials_exception

        from repositories.auth_repo import AuthRepository
        repository = AuthRepository() 
        user = await repository.find_by_id(user_id)
        if user is None:
            raise credentials_exception

        user["id"] = str(user.pop("_id"))
        user.pop("password", None) 

        return user

# Dependency injection
def get_auth_service() -> AuthService:
    return AuthService()
