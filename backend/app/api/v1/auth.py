from fastapi import APIRouter, Depends
from typing import Dict, Any

from app.core.auth import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/me")
async def get_me(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Get authenticated user information.
    Requires Authorization: Bearer <valid_supabase_jwt>.
    Returns 401 if unauthenticated or token is invalid.
    """
    return {
        "id": current_user["id"],
        "email": current_user.get("email"),
        "role": current_user.get("role", "authenticated"),
        "authenticated": True,
    }
