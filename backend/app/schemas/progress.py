"""
Progress & Task Schemas
=======================
Defines Pydantic schemas for Phase 14: Project Progress, Tasks, and Milestones.
"""

from typing import Optional, List, Literal
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


ProgressStatus = Literal["on_track", "at_risk", "delayed", "completed"]
TaskStatus = Literal["todo", "in_progress", "completed", "blocked"]
TaskPriority = Literal["low", "medium", "high", "urgent"]


class ProjectProgressCreate(BaseModel):
    title: str = Field(..., max_length=150, description="Milestone or progress checkpoint title")
    description: Optional[str] = Field(None, description="Detailed progress description")
    progress_percentage: int = Field(0, ge=0, le=100, description="Completion percentage (0-100)")
    status: ProgressStatus = Field("on_track", description="Milestone status")

    @field_validator("title")
    @classmethod
    def validate_title_not_empty(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Title must not be empty or whitespace only")
        return trimmed


class ProjectProgressUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=150)
    description: Optional[str] = None
    progress_percentage: Optional[int] = Field(None, ge=0, le=100)
    status: Optional[ProgressStatus] = None

    @field_validator("title")
    @classmethod
    def validate_title_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            trimmed = v.strip()
            if not trimmed:
                raise ValueError("Title must not be empty or whitespace only")
            return trimmed
        return v


class ProjectProgressResponse(BaseModel):
    id: UUID
    project_id: UUID
    title: str
    description: Optional[str] = None
    progress_percentage: int
    status: ProgressStatus
    created_by: UUID
    created_by_name: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ProjectTaskCreate(BaseModel):
    title: str = Field(..., max_length=150, description="Task title")
    description: Optional[str] = Field(None, description="Detailed task description")
    assigned_student_id: Optional[UUID] = Field(None, description="Assigned team member student UUID")
    status: TaskStatus = Field("todo", description="Task workflow status")
    priority: TaskPriority = Field("medium", description="Task priority")
    due_date: Optional[datetime] = Field(None, description="Target completion timestamp")

    @field_validator("title")
    @classmethod
    def validate_title_not_empty(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Task title must not be empty or whitespace only")
        return trimmed


class ProjectTaskUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=150)
    description: Optional[str] = None
    assigned_student_id: Optional[UUID] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[datetime] = None

    @field_validator("title")
    @classmethod
    def validate_title_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            trimmed = v.strip()
            if not trimmed:
                raise ValueError("Task title must not be empty or whitespace only")
            return trimmed
        return v


class ProjectTaskResponse(BaseModel):
    id: UUID
    project_id: UUID
    title: str
    description: Optional[str] = None
    assigned_student_id: Optional[UUID] = None
    assigned_student_name: Optional[str] = None
    status: TaskStatus
    priority: TaskPriority
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_by: UUID
    created_by_name: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class ProjectProgressOverviewResponse(BaseModel):
    project_id: UUID
    overall_progress_percentage: int
    total_tasks: int
    completed_tasks: int
    in_progress_tasks: int
    blocked_tasks: int
    todo_tasks: int
    latest_milestone_status: str
    tasks: List[ProjectTaskResponse] = []
    updates: List[ProjectProgressResponse] = []
