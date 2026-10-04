from typing import List
from fastapi import APIRouter
from app.schemas.reference import DepartmentResponse, SkillResponse, InterestResponse
from app.services import reference_service

router = APIRouter(tags=["Reference Data"])


@router.get("/departments", response_model=List[DepartmentResponse])
async def list_departments():
    """Retrieve list of all academic departments."""
    return reference_service.get_departments()


@router.get("/skills", response_model=List[SkillResponse])
async def list_skills():
    """Retrieve master taxonomy of verified skills."""
    return reference_service.get_skills()


@router.get("/interests", response_model=List[InterestResponse])
async def list_interests():
    """Retrieve master taxonomy of project interest domains."""
    return reference_service.get_interests()
