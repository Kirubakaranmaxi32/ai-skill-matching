from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class StudentProfileBase(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=150, description="Student's full name")
    department_id: Optional[UUID] = Field(None, description="Department UUID")
    academic_year: Optional[int] = Field(None, ge=1, le=5, description="Academic year (1-5)")


class StudentProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=150, description="Student's full name")
    department_id: Optional[UUID] = Field(None, description="Department UUID")
    academic_year: Optional[int] = Field(None, ge=1, le=5, description="Academic year (1-5)")

    model_config = ConfigDict(extra="forbid")


class StudentProfileResponse(BaseModel):
    id: UUID
    user_id: UUID
    full_name: str
    department_id: Optional[UUID] = None
    department_name: Optional[str] = None
    academic_year: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
