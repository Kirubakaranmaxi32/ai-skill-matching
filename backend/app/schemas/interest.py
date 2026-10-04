from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class StudentInterestCreate(BaseModel):
    interest_id: UUID = Field(..., description="Interest UUID from interests taxonomy")

    model_config = ConfigDict(extra="forbid")


class StudentInterestResponse(BaseModel):
    id: UUID
    student_id: UUID
    interest_id: UUID
    interest_name: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
