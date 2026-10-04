"""
Feedback Schemas
================
Defines Pydantic schemas for Phase 14: Collaboration & Recommendation Feedback.
"""

from typing import Optional, List, Literal
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


CollaborationQuality = Literal["exceptional", "good", "adequate", "challenging"]


class FeedbackCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="Collaboration rating between 1 and 5")
    feedback_text: Optional[str] = Field(None, max_length=2000, description="Constructive written feedback")
    collaboration_quality: Optional[CollaborationQuality] = Field(None, description="Qualitative feedback category")
    skills_aligned: bool = Field(True, description="Whether recommended/matched skills were accurately aligned")

    @field_validator("feedback_text")
    @classmethod
    def validate_feedback_text(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            trimmed = v.strip()
            return trimmed if trimmed else None
        return v


class FeedbackResponse(BaseModel):
    id: UUID
    project_id: UUID
    student_id: UUID
    student_name: Optional[str] = None
    rating: int
    feedback_text: Optional[str] = None
    collaboration_quality: Optional[CollaborationQuality] = None
    skills_aligned: bool
    created_at: datetime
    updated_at: Optional[datetime] = None


class FeedbackSummaryResponse(BaseModel):
    project_id: UUID
    average_rating: float
    total_feedback_count: int
    skills_aligned_percentage: float
    feedback_list: List[FeedbackResponse] = []
