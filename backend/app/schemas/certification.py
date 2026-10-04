from typing import Optional
from uuid import UUID
from datetime import date, datetime
from pydantic import BaseModel, Field, HttpUrl, ConfigDict, field_validator


class CertificationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Certification name / title")
    issuing_organization: str = Field(..., min_length=1, max_length=150, description="Issuing body (e.g. AWS, Coursera)")
    issue_date: date = Field(..., description="Date certification was issued")
    credential_url: Optional[str] = Field(None, max_length=500, description="Verification or credential URL")

    @field_validator("credential_url")
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        if v and not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("credential_url must start with http:// or https://")
        return v

    model_config = ConfigDict(extra="forbid")


class CertificationResponse(BaseModel):
    id: UUID
    student_id: UUID
    name: str
    issuing_organization: str
    issue_date: date
    credential_url: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
