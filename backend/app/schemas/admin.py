"""
Phase 15: Admin Dashboard Pydantic Schemas
==========================================
Structured response models for administrative analytics, platform monitoring,
and AI model readiness.
"""

from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class StudentProfileCompleteness(BaseModel):
    with_skills: int = 0
    with_interests: int = 0
    with_previous_projects: int = 0
    with_certifications: int = 0
    completion_rate_percentage: float = 0.0


class SkillProficiencyDistribution(BaseModel):
    beginner: int = 0
    intermediate: int = 0
    advanced: int = 0
    expert: int = 0


class AdminStudentStats(BaseModel):
    total_students: int
    students_by_department: List[Dict[str, Any]]
    students_by_year: Dict[str, int]
    profile_completeness: StudentProfileCompleteness
    total_skills: int
    skills_by_category: Dict[str, int]
    most_common_skills: List[Dict[str, Any]]
    proficiency_distribution: SkillProficiencyDistribution
    project_skill_demand: List[Dict[str, Any]]
    demo_mode: bool = False


class ProjectInvitationStats(BaseModel):
    total_invitations: int
    invitations_by_status: Dict[str, int]
    acceptance_rate: float


class AdminProjectStats(BaseModel):
    total_projects: int
    projects_by_status: Dict[str, int]
    recent_projects: List[Dict[str, Any]]
    total_project_members: int
    avg_team_size: float
    max_team_size: int
    invitation_stats: ProjectInvitationStats
    demo_mode: bool = False


class AdminProgressStats(BaseModel):
    avg_project_progress: float
    projects_by_progress_status: Dict[str, int]
    total_tasks: int
    tasks_by_status: Dict[str, int]
    completed_tasks: int
    pending_tasks: int
    blocked_tasks: int
    tasks_by_priority: Dict[str, int]
    demo_mode: bool = False


class AdminFeedbackStats(BaseModel):
    total_feedback: int
    avg_rating: Optional[float] = None
    rating_distribution: Dict[str, int]
    recent_feedback: List[Dict[str, Any]]
    demo_mode: bool = False


class RecommendationReadiness(BaseModel):
    eligible_candidates_count: int
    projects_with_skills_count: int


class AdminAiMatchingStats(BaseModel):
    model_loaded: bool
    model_type: str
    model_version: str
    input_features_count: int
    hidden_layers: List[int]
    trainable_parameters: int
    checkpoint_present: bool
    sentence_transformer_available: bool
    sentence_transformer_model: str
    recommendation_readiness: RecommendationReadiness
    feedback_satisfaction_avg: Optional[float] = None
    feedback_total_count: int = 0
    historical_tracking_available: bool = False
    historical_tracking_notice: str = (
        "Detailed session-by-session historical recommendation logging is planned as a future enhancement."
    )
    demo_mode: bool = False


class AdminSystemStats(BaseModel):
    status: str = "healthy"
    database_connected: bool
    database_mode: str
    demo_mode: bool
    api_version: str = "v1"
    ai_subsystem_healthy: bool
    checkpoint_verified: bool


class AdminOverviewResponse(BaseModel):
    total_students: int
    total_projects: int
    total_project_members: int
    total_invitations: int
    avg_project_progress: float
    total_feedback: int
    avg_feedback_rating: Optional[float] = None
    ai_model_loaded: bool
    ai_model_version: str
    database_connected: bool
    demo_mode: bool
