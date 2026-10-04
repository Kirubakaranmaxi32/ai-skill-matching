"""
Demonstration Mode API Endpoints
================================
Provides endpoints for local synthetic demonstration data and recommendations.
Never touches the Supabase database.
"""

from typing import List, Dict, Any, Optional
from uuid import UUID
from fastapi import APIRouter, Query, HTTPException, status

from app.core.config import settings
from app.services.demo_service import (
    is_demo_mode_active,
    load_demo_students,
    load_demo_projects,
    get_demo_project_by_id,
    DemoRecommendationService,
)
from app.schemas.recommendation import ProjectRecommendationResponse
from app.schemas.skill_gap import SkillGapResponse
from app.schemas.progress import (
    ProjectProgressOverviewResponse,
    ProjectProgressResponse,
    ProjectProgressCreate,
    ProjectTaskResponse,
    ProjectTaskCreate,
    ProjectTaskUpdate,
)
from app.schemas.feedback import (
    FeedbackResponse,
    FeedbackCreate,
    FeedbackSummaryResponse,
)
from app.services.skill_gap_service import skill_gap_service
from app.services.progress_service import progress_service
from app.services.feedback_service import feedback_service

router = APIRouter(prefix="/demo", tags=["Demonstration Mode"])

_demo_rec_service = DemoRecommendationService()


@router.get("/status")
def get_demo_status() -> Dict[str, Any]:
    """Returns the current Demonstration Mode configuration and metadata."""
    return {
        "demo_mode_configured": is_demo_mode_active(),
        "dataset_type": "DEMO",
        "synthetic": True,
        "source": "local demonstration dataset",
        "description": "Safe demonstration mode using local synthetic records and the real trained PyTorch MLP.",
    }


@router.get("/students")
def list_demo_students() -> Dict[str, Any]:
    """Retrieve all local synthetic demo students."""
    students = load_demo_students()
    return {
        "count": len(students),
        "synthetic": True,
        "students": students,
    }


@router.get("/projects")
def list_demo_projects() -> List[Dict[str, Any]]:
    """Retrieve all local synthetic demo projects."""
    return load_demo_projects()


@router.get("/projects/{project_id}")
def get_demo_project(project_id: str) -> Dict[str, Any]:
    """Retrieve a single local synthetic demo project."""
    return get_demo_project_by_id(project_id)


@router.get(
    "/projects/{project_id}/recommendations",
    response_model=ProjectRecommendationResponse,
)
def get_demo_recommendations(
    project_id: str,
    top_k: int = Query(10, ge=1, le=50, description="Top K recommendations"),
    min_score: float = Query(0.0, ge=0.0, le=1.0, description="Minimum compatibility score threshold"),
) -> ProjectRecommendationResponse:
    """
    Computes candidate recommendations for a demo project using local synthetic
    students and the real trained PyTorch MLP checkpoint.
    """
    return _demo_rec_service.get_demo_recommendations(
        project_id=project_id,
        top_k=top_k,
        min_score=min_score,
    )


@router.get(
    "/projects/{project_id}/skill-gap",
    response_model=SkillGapResponse,
    summary="Get Skill-Gap Analysis for a demo project using local synthetic data",
)
def get_demo_skill_gap(
    project_id: str,
    student_id: Optional[str] = Query(None, description="Optional demo student UUID"),
) -> SkillGapResponse:
    """
    Computes skill-gap analysis for a demo project and demo student using local
    synthetic datasets. Never queries or writes to Supabase.
    """
    return skill_gap_service.get_demo_project_skill_gap(
        project_id=project_id,
        student_id=student_id,
    )


# ------------------------------------------------------------------------------
# Phase 14: Demo Progress, Tasks & Feedback Endpoints
# ------------------------------------------------------------------------------

@router.get(
    "/projects/{project_id}/progress",
    response_model=ProjectProgressOverviewResponse,
    summary="Get demo project progress overview, milestones, and tasks",
)
def get_demo_project_progress(project_id: str) -> ProjectProgressOverviewResponse:
    """Retrieve demo project progress overview using local in-memory data."""
    return progress_service.get_project_progress_overview(
        project_id=project_id,
        user_id="00000000-de00-0000-0000-000000000001",
    )


@router.post(
    "/projects/{project_id}/progress",
    response_model=ProjectProgressResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create demo progress update",
)
def create_demo_project_progress(
    project_id: str,
    payload: ProjectProgressCreate,
) -> ProjectProgressResponse:
    """Create a demo progress update."""
    return progress_service.create_progress_update(
        project_id=project_id,
        user_id="00000000-de00-0000-0000-000000000001",
        payload=payload,
    )


@router.get(
    "/projects/{project_id}/tasks",
    response_model=List[ProjectTaskResponse],
    summary="List demo project tasks",
)
def list_demo_project_tasks(project_id: str) -> List[ProjectTaskResponse]:
    """List tasks for a demo project."""
    return progress_service.get_project_tasks(
        project_id=project_id,
        user_id="00000000-de00-0000-0000-000000000001",
    )


@router.post(
    "/projects/{project_id}/tasks",
    response_model=ProjectTaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create demo project task",
)
def create_demo_project_task(
    project_id: str,
    payload: ProjectTaskCreate,
) -> ProjectTaskResponse:
    """Create a new demo project task."""
    return progress_service.create_task(
        project_id=project_id,
        user_id="00000000-de00-0000-0000-000000000001",
        payload=payload,
    )


@router.patch(
    "/projects/{project_id}/tasks/{task_id}",
    response_model=ProjectTaskResponse,
    summary="Update demo project task",
)
def update_demo_project_task(
    project_id: str,
    task_id: str,
    payload: ProjectTaskUpdate,
) -> ProjectTaskResponse:
    """Update a demo project task."""
    return progress_service.update_task(
        project_id=project_id,
        task_id=task_id,
        user_id="00000000-de00-0000-0000-000000000001",
        payload=payload,
    )


@router.delete(
    "/projects/{project_id}/tasks/{task_id}",
    summary="Delete demo project task",
)
def delete_demo_project_task(
    project_id: str,
    task_id: str,
) -> Dict[str, str]:
    """Delete a demo project task."""
    return progress_service.delete_task(
        project_id=project_id,
        task_id=task_id,
        user_id="00000000-de00-0000-0000-000000000001",
    )


@router.get(
    "/projects/{project_id}/feedback",
    response_model=FeedbackSummaryResponse,
    summary="Get demo project feedback summary",
)
def get_demo_project_feedback(project_id: str) -> FeedbackSummaryResponse:
    """Retrieve demo project collaboration feedback."""
    return feedback_service.get_project_feedback(
        project_id=project_id,
        user_id="00000000-de00-0000-0000-000000000001",
    )


@router.post(
    "/projects/{project_id}/feedback",
    response_model=FeedbackResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit demo project feedback",
)
def submit_demo_project_feedback(
    project_id: str,
    payload: FeedbackCreate,
) -> FeedbackResponse:
    """Submit feedback for a demo project."""
    return feedback_service.submit_feedback(
        project_id=project_id,
        user_id="00000000-de00-0000-0000-000000000002",
        payload=payload,
    )
