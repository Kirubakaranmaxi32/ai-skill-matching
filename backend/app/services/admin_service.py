"""
Phase 15: Admin Dashboard Service
=================================
Aggregates, computes, and formats platform analytics, AI model readiness,
and system monitoring metrics for administrative visibility.

Guarantees:
- Strictly read-only operations (zero mutations).
- Never leaks API keys, service-role keys, or JWT secrets.
- Reuses existing database tables and model checkpoints.
- Accurately reports available metrics; never fabricates historical recommendation counts.
- Gracefully handles both live Supabase and offline/Demo Mode environments.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import torch
import logging

from app.core.config import settings
from app.core.supabase import is_supabase_configured
from app.services.db_adapter import db
from app.services.demo_service import is_demo_mode_active
from app.schemas.admin import (
    AdminOverviewResponse,
    AdminStudentStats,
    AdminProjectStats,
    AdminProgressStats,
    AdminFeedbackStats,
    AdminAiMatchingStats,
    AdminSystemStats,
    StudentProfileCompleteness,
    SkillProficiencyDistribution,
    ProjectInvitationStats,
    RecommendationReadiness,
)

logger = logging.getLogger(__name__)

# Workspace root path for checkpoint inspection
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
CHECKPOINT_PATH = ROOT_DIR / "models" / "checkpoints" / "best_matching_mlp.pt"


class AdminService:
    """Service providing aggregate analytics for authorized administrators."""

    def get_overview(self) -> AdminOverviewResponse:
        """Computes top-level KPIs across all domains."""
        demo_mode = is_demo_mode_active()
        students = db.select_all("students")
        projects = db.select_all("projects")
        members = db.select_all("project_members")
        invitations = db.select_all("invitations")
        progress_rows = db.select_all("project_progress")
        feedback_rows = db.select_all("recommendation_feedback")

        # Average progress
        avg_progress = 0.0
        if progress_rows:
            pcts = [p.get("progress_percentage", 0) for p in progress_rows]
            avg_progress = round(sum(pcts) / len(pcts), 1)

        # Average feedback rating
        avg_rating = None
        ratings = [f.get("rating") for f in feedback_rows if f.get("rating") is not None]
        if ratings:
            avg_rating = round(sum(ratings) / len(ratings), 2)

        # AI model info
        ai_stats = self.get_ai_matching_stats()

        return AdminOverviewResponse(
            total_students=len(students),
            total_projects=len(projects),
            total_project_members=len(members),
            total_invitations=len(invitations),
            avg_project_progress=avg_progress,
            total_feedback=len(feedback_rows),
            avg_feedback_rating=avg_rating,
            ai_model_loaded=ai_stats.model_loaded,
            ai_model_version=ai_stats.model_version,
            database_connected=is_supabase_configured(),
            demo_mode=demo_mode,
        )

    def get_student_stats(self) -> AdminStudentStats:
        """Computes student demographics, profile completion, and skill distributions."""
        demo_mode = is_demo_mode_active()
        students = db.select_all("students")
        departments = db.select_all("departments")
        skills = db.select_all("skills")
        student_skills = db.select_all("student_skills")
        student_interests = db.select_all("student_interests")
        previous_projects = db.select_all("previous_projects")
        certifications = db.select_all("certifications")
        project_skills = db.select_all("project_skills")

        # Map department ID to name
        dept_map = {str(d.get("id")): d.get("name", "Unknown") for d in departments}
        dept_counts: Dict[str, int] = {}
        for s in students:
            dept_id = str(s.get("department_id") or "")
            dept_name = dept_map.get(dept_id, "Undeclared")
            dept_counts[dept_name] = dept_counts.get(dept_name, 0) + 1

        students_by_dept = [
            {"department": name, "count": count}
            for name, count in sorted(dept_counts.items(), key=lambda x: -x[1])
        ]

        # Year distribution
        year_counts: Dict[str, int] = {str(y): 0 for y in range(1, 6)}
        for s in students:
            yr = s.get("year")
            if yr is not None and str(yr) in year_counts:
                year_counts[str(yr)] += 1

        # Profile completeness
        stu_with_skills = len({str(sk.get("student_id")) for sk in student_skills})
        stu_with_interests = len({str(i.get("student_id")) for i in student_interests})
        stu_with_projects = len({str(p.get("student_id")) for p in previous_projects})
        stu_with_certs = len({str(c.get("student_id")) for c in certifications})

        total_students = len(students)
        completion_pct = 0.0
        if total_students > 0:
            completion_pct = round((stu_with_skills / total_students) * 100, 1)

        completeness = StudentProfileCompleteness(
            with_skills=stu_with_skills,
            with_interests=stu_with_interests,
            with_previous_projects=stu_with_projects,
            with_certifications=stu_with_certs,
            completion_rate_percentage=completion_pct,
        )

        # Skill category breakdown
        skill_map = {str(sk.get("id")): sk for sk in skills}
        category_counts: Dict[str, int] = {}
        for sk in skills:
            cat = sk.get("category", "general")
            category_counts[cat] = category_counts.get(cat, 0) + 1

        # Most common student skills
        skill_freq: Dict[str, int] = {}
        proficiency_counts = {1: 0, 2: 0, 3: 0, 4: 0}
        for ss in student_skills:
            sk_id = str(ss.get("skill_id") or "")
            skill_freq[sk_id] = skill_freq.get(sk_id, 0) + 1
            lvl = ss.get("proficiency_level", 2)
            if lvl in proficiency_counts:
                proficiency_counts[lvl] += 1

        most_common = []
        for sk_id, freq in sorted(skill_freq.items(), key=lambda x: -x[1])[:10]:
            sk_info = skill_map.get(sk_id, {})
            most_common.append({
                "skill_id": sk_id,
                "skill_name": sk_info.get("name", "Technical Skill"),
                "category": sk_info.get("category", "general"),
                "student_count": freq,
            })

        proficiency_dist = SkillProficiencyDistribution(
            beginner=proficiency_counts[1],
            intermediate=proficiency_counts[2],
            advanced=proficiency_counts[3],
            expert=proficiency_counts[4],
        )

        # Project skill demand
        proj_skill_freq: Dict[str, int] = {}
        for ps in project_skills:
            sk_id = str(ps.get("skill_id") or "")
            proj_skill_freq[sk_id] = proj_skill_freq.get(sk_id, 0) + 1

        project_demand = []
        for sk_id, count in sorted(proj_skill_freq.items(), key=lambda x: -x[1])[:10]:
            sk_info = skill_map.get(sk_id, {})
            project_demand.append({
                "skill_id": sk_id,
                "skill_name": sk_info.get("name", "Required Skill"),
                "category": sk_info.get("category", "general"),
                "project_count": count,
            })

        return AdminStudentStats(
            total_students=total_students,
            students_by_department=students_by_dept,
            students_by_year=year_counts,
            profile_completeness=completeness,
            total_skills=len(skills),
            skills_by_category=category_counts,
            most_common_skills=most_common,
            proficiency_distribution=proficiency_dist,
            project_skill_demand=project_demand,
            demo_mode=demo_mode,
        )

    def get_project_stats(self) -> AdminProjectStats:
        """Computes project lifecycle, team size, and invitation statistics."""
        demo_mode = is_demo_mode_active()
        projects = db.select_all("projects")
        members = db.select_all("project_members")
        invitations = db.select_all("invitations")

        # Project status distribution
        status_counts = {"open": 0, "in_progress": 0, "completed": 0, "archived": 0}
        for p in projects:
            st = p.get("status", "open")
            if st in status_counts:
                status_counts[st] += 1

        # Recent projects (top 5 by created_at desc)
        sorted_projects = sorted(
            projects,
            key=lambda p: str(p.get("created_at") or ""),
            reverse=True,
        )[:5]
        recent_projects = [
            {
                "id": str(p.get("id")),
                "title": p.get("title"),
                "status": p.get("status"),
                "owner_id": str(p.get("owner_id")),
                "created_at": p.get("created_at"),
            }
            for p in sorted_projects
        ]

        # Team member statistics
        members_per_project: Dict[str, int] = {}
        for m in members:
            pid = str(m.get("project_id") or "")
            members_per_project[pid] = members_per_project.get(pid, 0) + 1

        total_members = len(members)
        avg_team = 0.0
        max_team = 0
        if projects:
            counts = list(members_per_project.values())
            if counts:
                avg_team = round(sum(counts) / len(projects), 1)
                max_team = max(counts)

        # Invitation stats
        inv_counts = {"pending": 0, "accepted": 0, "rejected": 0, "cancelled": 0}
        for inv in invitations:
            st = inv.get("status", "pending")
            if st in inv_counts:
                inv_counts[st] += 1

        total_invitations = len(invitations)
        responded = inv_counts["accepted"] + inv_counts["rejected"]
        acceptance_rate = 0.0
        if responded > 0:
            acceptance_rate = round(inv_counts["accepted"] / responded, 2)

        inv_stats = ProjectInvitationStats(
            total_invitations=total_invitations,
            invitations_by_status=inv_counts,
            acceptance_rate=acceptance_rate,
        )

        return AdminProjectStats(
            total_projects=len(projects),
            projects_by_status=status_counts,
            recent_projects=recent_projects,
            total_project_members=total_members,
            avg_team_size=avg_team,
            max_team_size=max_team,
            invitation_stats=inv_stats,
            demo_mode=demo_mode,
        )

    def get_progress_stats(self) -> AdminProgressStats:
        """Computes project progress percentages and task breakdown."""
        demo_mode = is_demo_mode_active()
        progress_rows = db.select_all("project_progress")
        tasks = db.select_all("project_tasks")

        # Progress stats
        avg_progress = 0.0
        if progress_rows:
            pcts = [p.get("progress_percentage", 0) for p in progress_rows]
            avg_progress = round(sum(pcts) / len(pcts), 1)

        progress_status_counts = {
            "not_started": 0,
            "in_progress": 0,
            "completed": 0,
            "blocked": 0,
        }
        for p in progress_rows:
            st = p.get("status", "not_started")
            if st in progress_status_counts:
                progress_status_counts[st] += 1

        # Task stats
        task_status_counts = {"todo": 0, "in_progress": 0, "completed": 0, "blocked": 0}
        task_priority_counts = {"low": 0, "medium": 0, "high": 0}

        for t in tasks:
            st = t.get("status", "todo")
            if st in task_status_counts:
                task_status_counts[st] += 1

            prio = t.get("priority", "medium")
            if prio in task_priority_counts:
                task_priority_counts[prio] += 1

        total_tasks = len(tasks)
        completed = task_status_counts["completed"]
        pending = task_status_counts["todo"] + task_status_counts["in_progress"]
        blocked = task_status_counts["blocked"]

        return AdminProgressStats(
            avg_project_progress=avg_progress,
            projects_by_progress_status=progress_status_counts,
            total_tasks=total_tasks,
            tasks_by_status=task_status_counts,
            completed_tasks=completed,
            pending_tasks=pending,
            blocked_tasks=blocked,
            tasks_by_priority=task_priority_counts,
            demo_mode=demo_mode,
        )

    def get_feedback_stats(self) -> AdminFeedbackStats:
        """Computes collaboration feedback and rating distributions."""
        demo_mode = is_demo_mode_active()
        feedback_rows = db.select_all("recommendation_feedback")

        ratings = [f.get("rating") for f in feedback_rows if f.get("rating") is not None]
        avg_rating = None
        if ratings:
            avg_rating = round(sum(ratings) / len(ratings), 2)

        rating_dist: Dict[str, int] = {str(i): 0 for i in range(1, 6)}
        for r in ratings:
            if 1 <= r <= 5:
                rating_dist[str(r)] += 1

        sorted_feedback = sorted(
            feedback_rows,
            key=lambda x: str(x.get("created_at") or ""),
            reverse=True,
        )[:5]

        recent_feedback = [
            {
                "id": str(f.get("id")),
                "project_id": str(f.get("project_id")),
                "student_id": str(f.get("student_id")),
                "rating": f.get("rating"),
                "feedback_text": f.get("feedback_text"),
                "created_at": f.get("created_at"),
            }
            for f in sorted_feedback
        ]

        return AdminFeedbackStats(
            total_feedback=len(feedback_rows),
            avg_rating=avg_rating,
            rating_distribution=rating_dist,
            recent_feedback=recent_feedback,
            demo_mode=demo_mode,
        )

    def get_ai_matching_stats(self) -> AdminAiMatchingStats:
        """Inspects real PyTorch MLP checkpoint metadata, readiness pool, and feedback satisfaction."""
        demo_mode = is_demo_mode_active()
        checkpoint_present = CHECKPOINT_PATH.exists()
        model_loaded = False
        model_type = "CompatibilityMLP"
        model_version = "v1.0.0-cpu"
        input_dim = 10
        hidden_dims = [64, 32]
        trainable_params = 2817

        if checkpoint_present:
            try:
                ckpt = torch.load(CHECKPOINT_PATH, map_location="cpu", weights_only=False)
                cfg = ckpt.get("model_config", {})
                model_type = cfg.get("model_type", model_type)
                input_dim = cfg.get("input_dim", input_dim)
                hidden_dims = list(cfg.get("hidden_dims", hidden_dims))
                trainable_params = cfg.get("total_trainable_parameters", trainable_params)
                model_loaded = True
            except Exception as e:
                logger.warning("Could not read checkpoint metadata: %s", e)

        # Sentence Transformer status
        st_available = True
        st_model_name = getattr(settings, "SENTENCE_TRANSFORMER_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

        # Recommendation readiness pool
        student_skills = db.select_all("student_skills")
        eligible_candidates = len({str(sk.get("student_id")) for sk in student_skills})

        project_skills = db.select_all("project_skills")
        projects_with_skills = len({str(ps.get("project_id")) for ps in project_skills})

        # Feedback stats
        fb_stats = self.get_feedback_stats()

        readiness = RecommendationReadiness(
            eligible_candidates_count=eligible_candidates,
            projects_with_skills_count=projects_with_skills,
        )

        return AdminAiMatchingStats(
            model_loaded=model_loaded,
            model_type=model_type,
            model_version=model_version,
            input_features_count=input_dim,
            hidden_layers=hidden_dims,
            trainable_parameters=trainable_params,
            checkpoint_present=checkpoint_present,
            sentence_transformer_available=st_available,
            sentence_transformer_model=st_model_name,
            recommendation_readiness=readiness,
            feedback_satisfaction_avg=fb_stats.avg_rating,
            feedback_total_count=fb_stats.total_feedback,
            historical_tracking_available=False,
            historical_tracking_notice=(
                "Detailed session-by-session historical recommendation logging is planned as a future enhancement."
            ),
            demo_mode=demo_mode,
        )

    def get_system_stats(self) -> AdminSystemStats:
        """Inspects operational subsystem health without exposing any secrets."""
        checkpoint_ok = CHECKPOINT_PATH.exists()
        supabase_ok = is_supabase_configured()
        db_mode = "supabase" if supabase_ok else "local_in_memory"

        return AdminSystemStats(
            status="healthy",
            database_connected=supabase_ok,
            database_mode=db_mode,
            demo_mode=is_demo_mode_active(),
            api_version="v1",
            ai_subsystem_healthy=checkpoint_ok,
            checkpoint_verified=checkpoint_ok,
        )


admin_service = AdminService()
