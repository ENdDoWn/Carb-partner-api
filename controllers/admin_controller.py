from fastapi import APIRouter, Depends, HTTPException, status, Query
from services.admin_service import AdminService

router = APIRouter()

@router.get("/admin/dashboard")
async def admin_dashboard(
    from_date: str = Query(..., alias="from"),
    to: str = Query(..., alias="to"),
    user_id: str | None = None,
    admin_service: AdminService = Depends(AdminService),
):
    try:
        return await admin_service.get_dashboard(from_date, to, user_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )

@router.get("/admin/users")
async def admin_users(
    limit: int = 50,
    admin_service: AdminService = Depends(AdminService),
):
    try:
        return {
            "users": await admin_service.list_users(limit),
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )
