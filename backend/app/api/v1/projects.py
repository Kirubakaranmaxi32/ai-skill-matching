from typing import List, Dict, Any, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, status, Query
from app.core.auth import get_current_user
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectDetailResponse,
    ProjectSkillCreate,
    ProjectSkillResponse,
)
from app.schemas.project_analysis import ProjectAnalysisResult
from app.schemas.recommendation import ProjectRecommendationResponse
from app.schemas.skill_gap import SkillGapResponse
from app.schemas.invitation import InvitationCreate, InvitationResponse
from app.schemas.progress import (
    ProjectProgressCreate,
    ProjectProgressUpdate,
    ProjectProgressResponse,
    ProjectTaskCreate,
    ProjectTaskUpdate,
    ProjectTaskResponse,
    ProjectProgressOverviewResponse,
)
from app.schemas.feedback import (
    FeedbackCreate,
    FeedbackResponse,
    FeedbackSummaryResponse,
)
from app.core.config import settings
from app.services import project_service
from app.services.project_analysis import project_analysis_service
from app.services.recommendation_service import recommendation_service
from app.services.skill_gap_service import skill_gap_service
from app.services.invitation_service import invitation_service, _demo_invitations_store
from app.services.progress_service import progress_service
from app.services.feedback_service import feedback_service

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project",
)
async def create_new_project(
    payload: ProjectCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> ProjectResponse:
    """
    Create a project owned by the current authenticated student.
    Automatically assigns the creator as an owner member in project_members.
    """
    project = project_service.create_project(current_user["id"], payload)
    return ProjectResponse.model_validate(project)


@router.get(
    "",
    response_model=List[ProjectResponse],
    summary="List discoverable, joined, or created projects",
)
async def list_projects(
    scope: str = Query("discover", description="Filter scope: 'discover' (open recruitment), 'joined' (teams joined), 'me' (owned)"),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> List[ProjectResponse]:
    """Retrieve projects based on scope (discover, joined, or me)."""
    if getattr(settings, "DEMO_MODE", False):
        from app.services.demo_service import load_demo_projects
        demo_projs = load_demo_projects()
        return [ProjectResponse.model_validate(p) for p in demo_projs]

    if scope == "joined":
        projects = project_service.get_joined_projects(current_user["id"])
    elif scope == "me":
        projects = project_service.get_my_projects(current_user["id"])
    else:
        projects = project_service.get_discoverable_projects(current_user["id"])

    return [ProjectResponse.model_validate(p) for p in projects]


@router.get(
    "/me",
    response_model=List[ProjectResponse],
    summary="List projects owned by current user",
)
async def list_my_projects(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> List[ProjectResponse]:
    """Retrieve all projects created by the authenticated student, ordered newest first."""
    if getattr(settings, "DEMO_MODE", False):
        from app.services.demo_service import load_demo_projects
        demo_projs = load_demo_projects()
        return [ProjectResponse.model_validate(p) for p in demo_projs]
    projects = project_service.get_my_projects(current_user["id"])
    return [ProjectResponse.model_validate(p) for p in projects]


@router.get(
    "/{project_id}",
    response_model=ProjectDetailResponse,
    summary="Get project details by ID",
)
async def get_project(
    project_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> ProjectDetailResponse:
    """
    Retrieve project details, owner information, required skills, and team members.
    Archived projects are only accessible to their owner.
    """
    pid_str = str(project_id)
    if pid_str.startswith("00000000-de00") or getattr(settings, "DEMO_MODE", False):
        try:
            from app.services.demo_service import get_demo_project_by_id
            demo_p = get_demo_project_by_id(pid_str)
            return ProjectDetailResponse(
                id=UUID(demo_p["id"]),
                owner_id=UUID(demo_p["owner_id"]),
                title=demo_p["title"],
                description=demo_p["description"],
                status=demo_p["status"],
                created_at=demo_p["created_at"],
                updated_at=demo_p["updated_at"],
                owner={
                    "id": UUID(demo_p["owner_id"]),
                    "user_id": UUID("00000000-de00-0000-0001-000000000001"),
                    "full_name": demo_p.get("owner_name", "Student A (Demo)"),
                    "academic_year": 4,
                },
                required_skills=[
                    {
                        "id": UUID(f"00000000-de00-0002-0000-{idx+1:012d}"),
                        "project_id": UUID(demo_p["id"]),
                        "skill_id": UUID(rs["skill_id"]),
                        "skill_name": rs["skill_name"],
                        "required_proficiency": rs["required_proficiency"],
                        "category": rs.get("category", "ai_ml"),
                        "created_at": demo_p["created_at"],
                    }
                    for idx, rs in enumerate(demo_p.get("required_skills", []))
                ],
                members=(
                    [
                        {
                            "id": UUID("00000000-de00-0004-0000-000000000001"),
                            "project_id": UUID(demo_p["id"]),
                            "student_id": UUID(demo_p["owner_id"]),
                            "role": "owner",
                            "joined_at": demo_p["created_at"],
                            "student_name": demo_p.get("owner_name", "Student A (Demo)"),
                        }
                    ]
                    + [
                        {
                            "id": UUID(inv["id"]),
                            "project_id": UUID(demo_p["id"]),
                            "student_id": UUID(inv["invited_student_id"]),
                            "role": "member",
                            "joined_at": inv.get("responded_at") or inv["created_at"],
                            "student_name": "Student Candidate (Demo)",
                        }
                        for inv in _demo_invitations_store.values()
                        if inv["project_id"] == pid_str and inv["status"] == "accepted"
                    ]
                ),
            )
        except Exception:
            pass

    project = project_service.get_project_by_id(str(project_id), current_user["id"])
    return ProjectDetailResponse.model_validate(project)


@router.put(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Update project details",
)
async def update_existing_project(
    project_id: UUID,
    payload: ProjectUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> ProjectResponse:
    """
    Update project title, description, or status.
    Strictly restricted to the project owner (returns 403 otherwise).
    """
    project = project_service.update_project(str(project_id), current_user["id"], payload)
    return ProjectResponse.model_validate(project)


@router.post(
    "/{project_id}/archive",
    response_model=ProjectResponse,
    summary="Archive project",
)
async def archive_existing_project(
    project_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> ProjectResponse:
    """
    Archive a project (soft status update, non-destructive).
    Strictly restricted to the project owner (returns 403 otherwise).
    """
    project = project_service.archive_project(str(project_id), current_user["id"])
    return ProjectResponse.model_validate(project)


@router.post(
    "/{project_id}/skills",
    response_model=ProjectSkillResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add required skill to project",
)
async def add_skill_to_project(
    project_id: UUID,
    payload: ProjectSkillCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> ProjectSkillResponse:
    """
    Add a required taxonomy skill and proficiency requirement (1-4) to a project.
    Strictly restricted to the project owner. Prevents duplicates with 409 Conflict.
    """
    skill = project_service.add_project_skill(str(project_id), current_user["id"], payload)
    return ProjectSkillResponse.model_validate(skill)


@router.get(
    "/{project_id}/skills",
    response_model=List[ProjectSkillResponse],
    summary="Get required skills for project",
)
async def get_skills_for_project(
    project_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> List[ProjectSkillResponse]:
    """Retrieve all required skills and proficiency levels for a project."""
    skills = project_service.get_project_skills(str(project_id), current_user["id"])
    return [ProjectSkillResponse.model_validate(s) for s in skills]


@router.delete(
    "/{project_id}/skills/{skill_id}",
    summary="Remove required skill from project",
)
async def remove_skill_from_project(
    project_id: UUID,
    skill_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, str]:
    """
    Remove a required skill from a project.
    Strictly restricted to the project owner.
    """
    project_service.delete_project_skill(str(project_id), str(skill_id), current_user["id"])
    return {"status": "success", "message": "Required skill removed from project"}


@router.post(
    "/{project_id}/analyze",
    response_model=ProjectAnalysisResult,
    summary="Analyze project description using NLP and taxonomy alignment",
)
async def analyze_project_description(
    project_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> ProjectAnalysisResult:
    """
    Analyzes the project description:
    1. Preprocesses text and normalizes formatting while preserving technical tokens.
    2. Interfaces with the Sentence Transformer embedding pipeline.
    3. Identifies candidate skills and aligns them with the master taxonomy.
    4. Returns structured ProjectAnalysisResult without mutating project requirements.
    Strictly restricted to the project owner.
    """
    return project_analysis_service.analyze_project(str(project_id), current_user["id"])


@router.get(
    "/{project_id}/recommendations",
    response_model=ProjectRecommendationResponse,
    summary="Get Top-K recommended candidate students for a project using PyTorch MLP",
)
async def get_project_recommendations(
    project_id: UUID,
    top_k: int = Query(default=10, ge=1, le=50, description="Maximum number of candidates to return"),
    min_score: float = Query(default=0.0, ge=0.0, le=1.0, description="Minimum compatibility score threshold"),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> ProjectRecommendationResponse:
    """
    Retrieves Top-K candidate student recommendations ordered by compatibility score:
    1. Validates project existence and ownership authorization (strictly project owner).
    2. Performs candidate discovery and eligibility filtering (excludes owner and existing members).
    3. Computes 10-dimensional feature vector for each candidate.
    4. Evaluates compatibility using the trained PyTorch MLP model on CPU.
    5. Returns rank-ordered recommendations with factual explainability signals.
    """
    pid_str = str(project_id)
    if pid_str.startswith("00000000-de00") or getattr(settings, "DEMO_MODE", False):
        try:
            from app.services.demo_service import DemoRecommendationService
            demo_rec_svc = DemoRecommendationService()
            return demo_rec_svc.get_demo_recommendations(
                project_id=pid_str,
                top_k=top_k,
                min_score=min_score,
            )
        except Exception:
            pass

    return recommendation_service.get_project_recommendations(
        project_id=str(project_id),
        user_id=current_user["id"],
        top_k=top_k,
        min_score=min_score,
    )


@router.get(
    "/{project_id}/skill-gap",
    response_model=SkillGapResponse,
    summary="Get Skill-Gap Analysis comparing a student against project required skills",
)
async def get_project_skill_gap(
    project_id: UUID,
    student_id: Optional[UUID] = Query(
        None,
        description="Optional target student UUID to analyze. Defaults to the authenticated student.",
    ),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> SkillGapResponse:
    """
    Evaluates skill gaps between a student and a project's required skills:
    1. Compares project required proficiency with student proficiency.
    2. Classifies each skill as 'matched', 'partial', or 'missing'.
    3. Calculates coverage ratio and proficiency deficit gap.
    4. Authenticated students can evaluate their own profile against any project.
    5. Project owners can evaluate candidate students against their project.
    6. Non-owners are forbidden (403) from querying other students' private data.
    """
    pid_str = str(project_id)
    sid_str = str(student_id) if student_id else None

    if pid_str.startswith("00000000-de00") or getattr(settings, "DEMO_MODE", False):
        return skill_gap_service.get_demo_project_skill_gap(
            project_id=pid_str,
            student_id=sid_str,
        )

    return skill_gap_service.get_project_skill_gap(
        project_id=pid_str,
        user_id=current_user["id"],
        student_id=sid_str,
    )


@router.post(
    "/{project_id}/invitations",
    response_model=InvitationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send invitation to join project team (Project Owner only)",
)
async def create_project_invitation(
    project_id: UUID,
    payload: InvitationCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> InvitationResponse:
    """
    Project owner invites an eligible candidate student to join the project team:
    1. Validates project existence, open status, and owner authorization.
    2. Validates candidate existence, prevents self-invitations, and prevents existing team members.
    3. Prevents duplicate pending invitations (returns 409 Conflict).
    4. Creates invitation in 'pending' status.
    """
    return invitation_service.create_invitation(
        project_id=str(project_id),
        user_id=current_user["id"],
        target_student_id=str(payload.student_id),
    )


@router.get(
    "/{project_id}/invitations",
    response_model=List[InvitationResponse],
    summary="List invitations for a project (Project Owner only)",
)
async def list_project_invitations(
    project_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> List[InvitationResponse]:
    """
    Retrieves all sent invitations for a project.
    Strictly restricted to the project owner.
    """
    return invitation_service.get_project_invitations(
        project_id=str(project_id),
        user_id=current_user["id"],
    )


# ==============================================================================
# Phase 14: Project Progress, Tasks & Collaboration Feedback
# ==============================================================================

@router.get(
    "/{project_id}/progress",
    response_model=ProjectProgressOverviewResponse,
    summary="Get project progress overview, milestones, and tasks",
)
async def get_project_progress(
    project_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> ProjectProgressOverviewResponse:
    """
    Retrieve project progress overview including tasks and milestone updates.
    Restricted to verified project owner and accepted team members.
    """
    return progress_service.get_project_progress_overview(
        project_id=str(project_id),
        user_id=current_user["id"],
    )


@router.post(
    "/{project_id}/progress",
    response_model=ProjectProgressResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a progress update or milestone checkpoint",
)
async def create_progress_checkpoint(
    project_id: UUID,
    payload: ProjectProgressCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> ProjectProgressResponse:
    """
    Create a progress update/milestone for an active project.
    Restricted to verified project owner and accepted team members.
    """
    return progress_service.create_progress_update(
        project_id=str(project_id),
        user_id=current_user["id"],
        payload=payload,
    )


@router.patch(
    "/{project_id}/progress/{progress_id}",
    response_model=ProjectProgressResponse,
    summary="Update a progress checkpoint",
)
async def update_progress_checkpoint(
    project_id: UUID,
    progress_id: UUID,
    payload: ProjectProgressUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> ProjectProgressResponse:
    """
    Update a progress checkpoint.
    Restricted to project owner or the original author.
    """
    return progress_service.update_progress_update(
        project_id=str(project_id),
        progress_id=str(progress_id),
        user_id=current_user["id"],
        payload=payload,
    )


@router.delete(
    "/{project_id}/progress/{progress_id}",
    summary="Delete a progress checkpoint (Project Owner only)",
)
async def delete_progress_checkpoint(
    project_id: UUID,
    progress_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, str]:
    """Delete a progress checkpoint. Restricted to the project owner."""
    return progress_service.delete_progress_update(
        project_id=str(project_id),
        progress_id=str(progress_id),
        user_id=current_user["id"],
    )


@router.get(
    "/{project_id}/tasks",
    response_model=List[ProjectTaskResponse],
    summary="List tasks for project team",
)
async def list_project_tasks(
    project_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> List[ProjectTaskResponse]:
    """
    List all tasks associated with a project team.
    Restricted to verified project owner and accepted team members.
    """
    return progress_service.get_project_tasks(
        project_id=str(project_id),
        user_id=current_user["id"],
    )


@router.post(
    "/{project_id}/tasks",
    response_model=ProjectTaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task for the project team",
)
async def create_project_task(
    project_id: UUID,
    payload: ProjectTaskCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> ProjectTaskResponse:
    """
    Create a new task assigned to an owner or accepted team member.
    Restricted to verified project owner and accepted team members.
    """
    return progress_service.create_task(
        project_id=str(project_id),
        user_id=current_user["id"],
        payload=payload,
    )


@router.patch(
    "/{project_id}/tasks/{task_id}",
    response_model=ProjectTaskResponse,
    summary="Update task status, priority, or assignment",
)
async def update_project_task(
    project_id: UUID,
    task_id: UUID,
    payload: ProjectTaskUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> ProjectTaskResponse:
    """
    Update a task's status, priority, or details.
    Restricted to project owner, task creator, or assigned team member.
    """
    return progress_service.update_task(
        project_id=str(project_id),
        task_id=str(task_id),
        user_id=current_user["id"],
        payload=payload,
    )


@router.delete(
    "/{project_id}/tasks/{task_id}",
    summary="Delete a task (Owner or Task Creator only)",
)
async def delete_project_task(
    project_id: UUID,
    task_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, str]:
    """Delete a task. Restricted to the project owner or task creator."""
    return progress_service.delete_task(
        project_id=str(project_id),
        task_id=str(task_id),
        user_id=current_user["id"],
    )


@router.post(
    "/{project_id}/feedback",
    response_model=FeedbackResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit collaboration & recommendation feedback",
)
async def submit_project_feedback(
    project_id: UUID,
    payload: FeedbackCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> FeedbackResponse:
    """
    Submit collaboration rating and feedback for a project.
    Restricted to verified project owner and accepted team members.
    Enforces single submission per student per project (prevents duplicates with 409 Conflict).
    """
    return feedback_service.submit_feedback(
        project_id=str(project_id),
        user_id=current_user["id"],
        payload=payload,
    )


@router.get(
    "/{project_id}/feedback",
    response_model=FeedbackSummaryResponse,
    summary="Get collaboration feedback summary and ratings",
)
async def get_project_feedback_summary(
    project_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> FeedbackSummaryResponse:
    """
    Retrieve aggregate feedback ratings and reviews for a project team.
    Restricted to verified project owner and accepted team members.
    """
    return feedback_service.get_project_feedback(
        project_id=str(project_id),
        user_id=current_user["id"],
    )

