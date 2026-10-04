"""
Invitation Schemas
==================
Defines Pydantic schemas for Phase 13: Voluntary Team Formation & Invitations.
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class InvitationStatus(str, Enum):
    """Lifecycle status of a project team invitation."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class InvitationCreate(BaseModel):
    """Payload to invite a candidate student to a project."""
    student_id: UUID = Field(..., description="Target candidate student UUID to invite")


class SafeStudentSummary(BaseModel):
    """Sanitized, privacy-safe student summary."""
    id: UUID
    full_name: str
    academic_year: Optional[int] = None
    department: Optional[str] = None


class SafeProjectSummary(BaseModel):
    """Sanitized, privacy-safe project summary."""
    id: UUID
    title: str
    description: str
    status: str
    owner_id: UUID


class InvitationResponse(BaseModel):
    """Detailed response for an invitation."""
    id: UUID
    project_id: UUID
    inviter_id: UUID
    invited_student_id: UUID
    status: InvitationStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    responded_at: Optional[datetime] = None
    project: Optional[SafeProjectSummary] = None
    inviter: Optional[SafeStudentSummary] = None
    invited_student: Optional[SafeStudentSummary] = None


class ProjectTeamMemberResponse(BaseModel):
    """Details of a project team member."""
    id: UUID
    project_id: UUID
    student_id: UUID
    role: str = Field(..., description="'owner' or 'member'")
    joined_at: datetime
    full_name: str
    academic_year: Optional[int] = None
    department: Optional[str] = None
