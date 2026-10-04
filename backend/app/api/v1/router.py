from fastapi import APIRouter
from typing import Dict, Any
from app.api.v1.auth import router as auth_router
from app.api.v1.students import router as students_router
from app.api.v1.reference import router as reference_router
from app.api.v1.projects import router as projects_router
from app.api.v1.matching import router as matching_router
from app.api.v1.demo import router as demo_router
from app.api.v1.invitations import router as invitations_router
from app.api.v1.admin import router as admin_router

api_router = APIRouter()


@api_router.get("/health", tags=["Health"])
async def v1_health_check() -> Dict[str, Any]:
    """
    API v1 health status endpoint.
    Verifies that the versioned API router is online and receiving requests.
    """
    return {
        "status": "healthy",
        "service": "ai-skill-matching-backend",
        "version": "v1"
    }

# Mount sub-routers
api_router.include_router(auth_router)
api_router.include_router(students_router)
api_router.include_router(reference_router)
api_router.include_router(projects_router)
api_router.include_router(matching_router)
api_router.include_router(demo_router)
api_router.include_router(invitations_router)
api_router.include_router(admin_router)

