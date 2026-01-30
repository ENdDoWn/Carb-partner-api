from typing import List, Optional
from repositories.partner_repository import PartnerRepository

class AuthService:
    def __init__(self):
        self.repository = PartnerRepository()

    async def get_all_partners(self) -> List[dict]:
        return await self.repository.find_all()

# Dependency injection
def get_auth_service() -> AuthService:
    return AuthService()
