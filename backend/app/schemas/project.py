from typing import Optional, List, Literal
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


ProjectStatus = Literal["open", "in_progress", "completed", "archived"]


class ProjectCreate(BaseModel):
    title: str = Field(..., max_length=150, description="Project title (1-150 characters)")
    description: str = Field(..., description="Detailed project description")
    status: ProjectStatus = Field(default="open", description="Project status")

    @field_validator("title")
    @classmethod
    def validate_title_not_empty(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Project title must not be empty or whitespace only")
        return trimmed

    @field_validator("description")
    @classmethod
    def validate_description_not_empty(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Project description must not be empty or whitespace only")
        return trimmed


class ProjectUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=150, description="Updated project title")
    description: Optional[str] = Field(None, description="Updated project description")
    status: Optional[ProjectStatus] = Field(None, description="Updated project status")

    @field_validator("title")
    @classmethod
    def validate_title_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            trimmed = v.strip()
            if not trimmed:
                raise ValueError("Project title must not be empty or whitespace only")
            return trimmed
        return v

    @field_validator("description")
    @classmethod
    def validate_description_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            trimmed = v.strip()
            if not trimmed:
                raise ValueError("Project description must not be empty or whitespace only")
            return trimmed
        return v


class ProjectResponse(BaseModel):
    id: UUID
    owner_id: UUID
    title: str
    description: str
    status: str
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class ProjectSkillCreate(BaseModel):
    skill_id: UUID = Field(..., description="ID of the taxonomy skill")
    required_proficiency: int = Field(default=1, ge=1, le=4, description="Proficiency level between 1 and 4")


class ProjectSkillResponse(BaseModel):
    id: UUID
    project_id: UUID
    skill_id: UUID
    required_proficiency: int
    created_at: str
    skill_name: Optional[str] = None
    category: Optional[str] = None

    model_config = {"from_attributes": True}


class ProjectMemberResponse(BaseModel):
    id: UUID
    project_id: UUID
    student_id: UUID
    role: str
    joined_at: str
    student_name: Optional[str] = None

    model_config = {"from_attributes": True}


class ProjectOwnerResponse(BaseModel):
    id: UUID
    user_id: UUID
    full_name: str
    academic_year: Optional[int] = None

    model_config = {"from_attributes": True}


class ProjectDetailResponse(BaseModel):
    id: UUID
    owner_id: UUID
    title: str
    description: str
    status: str
    created_at: str
    updated_at: str
    owner: Optional[ProjectOwnerResponse] = None
    required_skills: List[ProjectSkillResponse] = []
    members: List[ProjectMemberResponse] = []

    model_config = {"from_attributes": True}
