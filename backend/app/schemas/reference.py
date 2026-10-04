from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class DepartmentResponse(BaseModel):
    id: UUID
    name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SkillResponse(BaseModel):
    id: UUID
    name: str
    category: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InterestResponse(BaseModel):
    id: UUID
    name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
