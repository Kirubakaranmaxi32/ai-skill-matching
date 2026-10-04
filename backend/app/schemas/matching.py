"""
Matching & Compatibility Schemas
================================
Defines request and response schemas for single-pair compatibility scoring
using the PyTorch CompatibilityMLP model.
"""

from typing import Optional, Dict
from uuid import UUID
from pydantic import BaseModel, Field


class CompatibilityRequest(BaseModel):
    """Payload for evaluating compatibility between a student and a project."""
    project_id: UUID = Field(..., description="Target project UUID")
    student_id: Optional[UUID] = Field(
        None,
        description="Candidate student UUID. If omitted, defaults to the authenticated student.",
    )


class CompatibilityResponse(BaseModel):
    """Inference response containing single-pair compatibility score and explainability values."""
    student_id: UUID = Field(..., description="Evaluated student UUID")
    project_id: UUID = Field(..., description="Target project UUID")
    compatibility_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Predicted compatibility score between 0.0 and 1.0",
    )
    model_version: str = Field(..., description="Identifier of the model checkpoint used")
    feature_contributions: Dict[str, float] = Field(
        default_factory=dict,
        description="Individual feature values computed for this student-project pair",
    )
