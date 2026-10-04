from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class StudentSkillCreate(BaseModel):
    skill_id: UUID = Field(..., description="Skill UUID from skills taxonomy")
    proficiency: int = Field(..., ge=1, le=4, description="Skill proficiency level (1=Beginner, 2=Intermediate, 3=Advanced, 4=Expert)")

    model_config = ConfigDict(extra="forbid")


class StudentSkillResponse(BaseModel):
    id: UUID
    student_id: UUID
    skill_id: UUID
    skill_name: Optional[str] = None
    skill_category: Optional[str] = None
    proficiency: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
