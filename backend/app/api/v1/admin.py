"""
Phase 15: Admin Dashboard API Router
====================================
Exposes administrative analytics, AI model readiness, and platform monitoring.

Security Guarantees:
- Every endpoint is protected by `Depends(get_current_admin)`.
- Rejects unauthenticated requests with HTTP 401 Unauthorized.
- Rejects non-admin authenticated users with HTTP 403 Forbidden.
- Strictly read-only GET endpoints (no database mutations).
- Never leaks API keys, service-role keys, or JWT secrets.
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, status

from app.core.auth import get_current_admin
from app.services.admin_service import admin_service
from app.schemas.admin import (
    AdminOverviewResponse,
    AdminStudentStats,
    AdminProjectStats,
    AdminProgressStats,
    AdminFeedbackStats,
    AdminAiMatchingStats,
    AdminSystemStats,
)

router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])


@router.get(
    "/status",
    summary="Verify current user admin status",
    response_model=Dict[str, Any],
)
async def check_admin_status(
    admin: Dict[str, Any] = Depends(get_current_admin),
) -> Dict[str, Any]:
    """Confirms whether the current authenticated user has administrative privileges."""
    return {
        "is_admin": True,
        "user_id": admin.get("id"),
        "email": admin.get("email"),
    }


@router.get(
    "/overview",
    response_model=AdminOverviewResponse,
    summary="Get overall administrative metrics overview",
)
async def get_admin_overview(
    _admin: Dict[str, Any] = Depends(get_current_admin),
) -> AdminOverviewResponse:
    """Returns top-level KPIs across all system domains."""
    return admin_service.get_overview()


@router.get(
    "/students",
    response_model=AdminStudentStats,
    summary="Get student demographics and skill analytics",
)
async def get_admin_students(
    _admin: Dict[str, Any] = Depends(get_current_admin),
) -> AdminStudentStats:
    """Returns student counts by department, academic year, and skill proficiencies."""
    return admin_service.get_student_stats()


@router.get(
    "/projects",
    response_model=AdminProjectStats,
    summary="Get project and team formation analytics",
)
async def get_admin_projects(
    _admin: Dict[str, Any] = Depends(get_current_admin),
) -> AdminProjectStats:
    """Returns project lifecycle status, team sizes, and invitation acceptance metrics."""
    return admin_service.get_project_stats()


@router.get(
    "/progress",
    response_model=AdminProgressStats,
    summary="Get project progress and task distribution",
)
async def get_admin_progress(
    _admin: Dict[str, Any] = Depends(get_current_admin),
) -> AdminProgressStats:
    """Returns average project completion percentages and task status/priority breakdowns."""
    return admin_service.get_progress_stats()


@router.get(
    "/feedback",
    response_model=AdminFeedbackStats,
    summary="Get collaboration feedback analytics",
)
async def get_admin_feedback(
    _admin: Dict[str, Any] = Depends(get_current_admin),
) -> AdminFeedbackStats:
    """Returns rating distributions, average rating, and recent feedback entries."""
    return admin_service.get_feedback_stats()


@router.get(
    "/ai-matching",
    response_model=AdminAiMatchingStats,
    summary="Get AI model readiness and matching health",
)
async def get_admin_ai_matching(
    _admin: Dict[str, Any] = Depends(get_current_admin),
) -> AdminAiMatchingStats:
    """Returns verified CompatibilityMLP metadata, sentence transformer status, and readiness pools."""
    return admin_service.get_ai_matching_stats()


@router.get(
    "/system",
    response_model=AdminSystemStats,
    summary="Get system and subsystem health status",
)
async def get_admin_system(
    _admin: Dict[str, Any] = Depends(get_current_admin),
) -> AdminSystemStats:
    """Returns operational status for backend, database, and AI subsystems without secrets."""
    return admin_service.get_system_stats()
