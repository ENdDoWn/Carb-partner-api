from fastapi import Depends, HTTPException, status
from repositories.user_repo import UserRepository
from core.config import settings

class UserService:
    def __init__(self):
        self.repository = UserRepository()

    async def add_additional_info(self, user_id: str, info_data: dict) -> dict:
        updated_user = await self.repository.update_additional_info(user_id, info_data)
        if not updated_user:
            raise Exception("Failed to update user info")
        return updated_user

