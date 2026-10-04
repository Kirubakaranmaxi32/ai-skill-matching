"""
Skill-Gap Analysis Schemas
==========================
Defines Pydantic schemas for project skill-gap evaluation, comparing
student skill proficiency against project required proficiency.
"""

from typing import List, Optional
from uuid import UUID
from enum import Enum
from pydantic import BaseModel, Field


class SkillGapStatus(str, Enum):
    """Classification status for a project-required skill."""
    MATCHED = "matched"
    PARTIAL = "partial"
    MISSING = "missing"


class SkillGapItem(BaseModel):
    """Detailed evaluation for a single project-required skill."""
    skill_id: UUID = Field(..., description="Canonical taxonomy skill UUID")
    skill_name: str = Field(..., description="Canonical skill name")
    category: Optional[str] = Field(None, description="Skill domain category")
    required_proficiency: int = Field(..., ge=1, le=4, description="Project required proficiency level (1-4)")
    student_proficiency: Optional[int] = Field(
        None,
        ge=1,
        le=4,
        description="Student proficiency level (1-4) or null if student does not possess the skill",
    )
    status: SkillGapStatus = Field(..., description="Skill status: matched, partial, or missing")
    proficiency_gap: Optional[int] = Field(
        None,
        ge=0,
        description="Deficit points (required - student) when status is partial",
    )


class SkillGapSummary(BaseModel):
    """Aggregated quantitative metrics for skill-gap analysis."""
    total_required_skills: int = Field(..., ge=0, description="Total skills required by the project")
    matched_count: int = Field(..., ge=0, description="Count of skills where student_proficiency >= required_proficiency")
    partial_count: int = Field(..., ge=0, description="Count of skills where student has skill but proficiency < required")
    missing_count: int = Field(..., ge=0, description="Count of project required skills absent from student profile")
    skill_coverage_ratio: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Ratio of fully matched skills (matched_count / total_required_skills), or 1.0 if no skills required",
    )
    proficiency_gap_count: int = Field(
        ...,
        ge=0,
        description="Total number of required skills exhibiting a proficiency deficit",
    )
    overall_gap_summary: str = Field(
        ...,
        description="Concise human-readable breakdown of the skill gap result",
    )


class SkillGapResponse(BaseModel):
    """Complete Skill-Gap analysis report comparing a student against a project."""
    project_id: UUID = Field(..., description="Target project UUID")
    project_title: Optional[str] = Field(None, description="Project title")
    student_id: UUID = Field(..., description="Analyzed student UUID")
    student_name: Optional[str] = Field(None, description="Analyzed student full name")
    summary: SkillGapSummary = Field(..., description="Summary statistics")
    skills: List[SkillGapItem] = Field(default_factory=list, description="Per-skill comparison list")
