from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from services.auth_services import AuthService, get_auth_service

router = APIRouter()


@router.get("/partners", response_model=List[PartnerResponse])
async def get_all_partners(service: AuthService = Depends(get_auth_service)):
    """Get all partners"""
    return await service.get_all_partners()


