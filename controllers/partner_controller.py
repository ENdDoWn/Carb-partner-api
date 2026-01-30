from fastapi import APIRouter, Depends
from typing import List, Optional
from pydantic import BaseModel
from services.auth_services import AuthService, get_auth_service

router = APIRouter()

class PartnerResponse(BaseModel):
    name: str
    description: Optional[str] = None
    # Add other fields as necessary, using strict typing or Optional

@router.get("/partners", response_model=List[dict])  # Simpler for skeleton
async def get_all_partners(service: AuthService = Depends(get_auth_service)):
    """Get all partners"""
    return await service.get_all_partners()
