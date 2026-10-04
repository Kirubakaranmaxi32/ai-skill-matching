from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator


class PreviousProjectCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Project title")
    description: Optional[str] = Field(None, max_length=2000, description="Detailed project description")
    technologies: List[str] = Field(default_factory=list, description="Array of technologies/tools used")
    project_url: Optional[str] = Field(None, max_length=500, description="GitHub repository or live URL")

    @field_validator("project_url")
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        if v and not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("project_url must start with http:// or https://")
        return v

    model_config = ConfigDict(extra="forbid")


class PreviousProjectResponse(BaseModel):
    id: UUID
    student_id: UUID
    title: str
    description: Optional[str] = None
    technologies: List[str] = Field(default_factory=list)
    project_url: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
