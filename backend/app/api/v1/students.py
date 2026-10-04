from typing import List, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, status
from app.core.auth import get_current_user
from app.schemas.student import StudentProfileResponse, StudentProfileUpdate
from app.schemas.skill import StudentSkillCreate, StudentSkillResponse
from app.schemas.interest import StudentInterestCreate, StudentInterestResponse
from app.schemas.certification import CertificationCreate, CertificationResponse
from app.schemas.previous_project import PreviousProjectCreate, PreviousProjectResponse
from app.services import (
    student_service,
    student_skills_service,
    student_interests_service,
    certification_service,
    previous_project_service,
)

router = APIRouter(prefix="/students", tags=["Student Profile & Portfolio"])


# ==============================================================================
# STUDENT PROFILE
# ==============================================================================
@router.get("/me", response_model=StudentProfileResponse)
async def get_my_profile(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Retrieve authenticated student's profile."""
    email = current_user.get("email")
    full_name = current_user.get("user_metadata", {}).get("full_name")
    return student_service.get_student_profile(current_user["id"], email=email, full_name=full_name)


@router.put("/me", response_model=StudentProfileResponse)
async def update_my_profile(
    data: StudentProfileUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update authenticated student's profile information."""
    return student_service.update_student_profile(current_user["id"], data)


# ==============================================================================
# STUDENT SKILLS
# ==============================================================================
@router.get("/me/skills", response_model=List[StudentSkillResponse])
async def list_my_skills(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Retrieve all skills associated with the authenticated student."""
    return student_skills_service.get_student_skills(current_user["id"])


@router.post("/me/skills", response_model=StudentSkillResponse, status_code=status.HTTP_201_CREATED)
async def add_my_skill(
    data: StudentSkillCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Add or update a skill proficiency rating."""
    return student_skills_service.add_student_skill(
        current_user["id"],
        str(data.skill_id),
        data.proficiency
    )


@router.delete("/me/skills/{skill_id}")
async def delete_my_skill(
    skill_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Remove a skill rating from authenticated student's profile."""
    student_skills_service.delete_student_skill(current_user["id"], str(skill_id))
    return {"success": True, "message": f"Skill {skill_id} deleted."}


# ==============================================================================
# STUDENT INTERESTS
# ==============================================================================
@router.get("/me/interests", response_model=List[StudentInterestResponse])
async def list_my_interests(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Retrieve all domain interests selected by authenticated student."""
    return student_interests_service.get_student_interests(current_user["id"])


@router.post("/me/interests", response_model=StudentInterestResponse, status_code=status.HTTP_201_CREATED)
async def add_my_interest(
    data: StudentInterestCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Add a project interest area."""
    return student_interests_service.add_student_interest(
        current_user["id"],
        str(data.interest_id)
    )


@router.delete("/me/interests/{interest_id}")
async def delete_my_interest(
    interest_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Remove an interest selection from authenticated student's profile."""
    student_interests_service.delete_student_interest(current_user["id"], str(interest_id))
    return {"success": True, "message": f"Interest {interest_id} deleted."}


# ==============================================================================
# CERTIFICATIONS
# ==============================================================================
@router.get("/me/certifications", response_model=List[CertificationResponse])
async def list_my_certifications(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Retrieve all certifications for the authenticated student."""
    return certification_service.get_student_certifications(current_user["id"])


@router.post("/me/certifications", response_model=CertificationResponse, status_code=status.HTTP_201_CREATED)
async def add_my_certification(
    data: CertificationCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Add a verified accreditation or certification."""
    return certification_service.add_student_certification(current_user["id"], data)


@router.delete("/me/certifications/{certification_id}")
async def delete_my_certification(
    certification_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete a certification. Strictly enforces ownership."""
    certification_service.delete_student_certification(current_user["id"], str(certification_id))
    return {"success": True, "message": f"Certification {certification_id} deleted."}


# ==============================================================================
# PREVIOUS PROJECTS
# ==============================================================================
@router.get("/me/projects", response_model=List[PreviousProjectResponse])
async def list_my_projects(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Retrieve all portfolio projects for the authenticated student."""
    return previous_project_service.get_student_projects(current_user["id"])


@router.post("/me/projects", response_model=PreviousProjectResponse, status_code=status.HTTP_201_CREATED)
async def add_my_project(
    data: PreviousProjectCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Add a past project to portfolio."""
    return previous_project_service.add_student_project(current_user["id"], data)


@router.delete("/me/projects/{project_id}")
async def delete_my_project(
    project_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete a portfolio project. Strictly enforces ownership."""
    previous_project_service.delete_student_project(current_user["id"], str(project_id))
    return {"success": True, "message": f"Project {project_id} deleted."}
