"""
Feedback Service
================
Manages post-collaboration and recommendation feedback:
- Ensures only verified project owners and accepted team members can submit or view feedback.
- Enforces single feedback submission per student per project (prevents duplicates with 409 Conflict).
- Computes aggregate metrics (average rating, skills alignment ratio).
- Supports isolated in-memory Demo Mode with zero Supabase mutations.
"""

from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID
from datetime import datetime
import uuid
from fastapi import HTTPException, status

from app.services.db_adapter import db, _now_iso
from app.services.student_service import get_or_create_student
from app.schemas.feedback import (
    FeedbackCreate,
    FeedbackResponse,
    FeedbackSummaryResponse,
)

_demo_feedback_store: Dict[str, Dict[str, Any]] = {}


def reset_demo_feedback() -> None:
    _demo_feedback_store.clear()


class FeedbackService:
    """Service managing project collaboration and matching feedback."""

    def _verify_membership(
        self, project_id: str, user_id: str
    ) -> Tuple[Dict[str, Any], Dict[str, Any], bool]:
        """
        Validates caller access:
        Returns (student, project, is_owner).
        Raises 403 Forbidden if student is neither owner nor accepted team member.
        """
        student = get_or_create_student(user_id)
        student_id = str(student["id"])

        project = db.select_by_id("projects", project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project not found with ID: {project_id}",
            )

        is_owner = str(project.get("owner_id")) == student_id
        if is_owner:
            return student, project, True

        # Check accepted membership in project_members
        members = db.select_by_field("project_members", "project_id", project_id)
        is_member = any(str(m.get("student_id")) == student_id for m in members)

        if not is_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized: Only the project owner and accepted team members can submit or view collaboration feedback.",
            )

        return student, project, False

    def submit_feedback(
        self, project_id: str, user_id: str, payload: FeedbackCreate
    ) -> FeedbackResponse:
        """Submit collaboration feedback for a project team."""
        if project_id.startswith("00000000-de00"):
            return self._submit_demo_feedback(project_id, payload)

        student, _, _ = self._verify_membership(project_id, user_id)
        student_id = str(student["id"])

        # Check duplicate feedback submission
        existing = db.select_by_field("recommendation_feedback", "project_id", project_id)
        if any(str(f.get("student_id")) == student_id for f in existing):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You have already submitted collaboration feedback for this project.",
            )

        now_ts = _now_iso()
        record = {
            "project_id": project_id,
            "student_id": student_id,
            "rating": payload.rating,
            "feedback_text": payload.feedback_text,
            "collaboration_quality": payload.collaboration_quality,
            "skills_aligned": payload.skills_aligned,
            "created_at": now_ts,
            "updated_at": now_ts,
        }
        created = db.insert("recommendation_feedback", record)
        return self._format_feedback(created, student_name=student.get("full_name"))

    def get_project_feedback(
        self, project_id: str, user_id: str
    ) -> FeedbackSummaryResponse:
        """Retrieve feedback summary and list for an authenticated project."""
        if project_id.startswith("00000000-de00"):
            return self._get_demo_feedback_summary(project_id)

        self._verify_membership(project_id, user_id)
        records = db.select_by_field("recommendation_feedback", "project_id", project_id)
        records.sort(key=lambda x: str(x.get("created_at", "")), reverse=True)

        total_count = len(records)
        if total_count > 0:
            avg_rating = round(sum(r.get("rating", 0) for r in records) / total_count, 1)
            aligned_count = sum(1 for r in records if r.get("skills_aligned", True))
            aligned_pct = round((aligned_count / total_count) * 100, 1)
        else:
            avg_rating = 0.0
            aligned_pct = 100.0

        return FeedbackSummaryResponse(
            project_id=UUID(project_id),
            average_rating=avg_rating,
            total_feedback_count=total_count,
            skills_aligned_percentage=aligned_pct,
            feedback_list=[self._format_feedback(r) for r in records],
        )

    def _format_feedback(
        self, f: Dict[str, Any], student_name: Optional[str] = None
    ) -> FeedbackResponse:
        s_id = f.get("student_id")
        if not student_name and s_id:
            s_rec = db.select_by_id("students", str(s_id))
            if s_rec:
                student_name = s_rec.get("full_name")

        created_dt = f.get("created_at")
        if isinstance(created_dt, str):
            created_dt = datetime.fromisoformat(created_dt.replace("Z", "+00:00"))

        updated_dt = f.get("updated_at")
        if isinstance(updated_dt, str):
            updated_dt = datetime.fromisoformat(updated_dt.replace("Z", "+00:00"))

        return FeedbackResponse(
            id=UUID(str(f["id"])),
            project_id=UUID(str(f["project_id"])),
            student_id=UUID(str(s_id)),
            student_name=student_name,
            rating=f["rating"],
            feedback_text=f.get("feedback_text"),
            collaboration_quality=f.get("collaboration_quality"),
            skills_aligned=bool(f.get("skills_aligned", True)),
            created_at=created_dt,
            updated_at=updated_dt,
        )

    # --------------------------------------------------------------------------
    # Demo Mode Implementations
    # --------------------------------------------------------------------------
    def _submit_demo_feedback(
        self, project_id: str, payload: FeedbackCreate
    ) -> FeedbackResponse:
        f_id = str(uuid.uuid4())
        now = _now_iso()
        record = {
            "id": f_id,
            "project_id": project_id,
            "student_id": "00000000-de00-0000-0000-000000000002",
            "rating": payload.rating,
            "feedback_text": payload.feedback_text,
            "collaboration_quality": payload.collaboration_quality,
            "skills_aligned": payload.skills_aligned,
            "created_at": now,
            "updated_at": now,
        }
        _demo_feedback_store[f_id] = record
        return self._format_feedback(record, student_name="Student B (Demo)")

    def _get_demo_feedback_summary(
        self, project_id: str
    ) -> FeedbackSummaryResponse:
        items = [f for f in _demo_feedback_store.values() if f["project_id"] == project_id]
        if not items:
            # Seed 1 initial demo feedback record for presentation
            f_id = str(uuid.uuid4())
            now = _now_iso()
            demo_f = {
                "id": f_id,
                "project_id": project_id,
                "student_id": "00000000-de00-0000-0000-000000000002",
                "rating": 5,
                "feedback_text": "Great collaboration! The AI skill recommendation was accurate; PyTorch and computer vision skills aligned smoothly with project goals.",
                "collaboration_quality": "exceptional",
                "skills_aligned": True,
                "created_at": now,
                "updated_at": now,
            }
            _demo_feedback_store[f_id] = demo_f
            items = [demo_f]

        total = len(items)
        avg = round(sum(i["rating"] for i in items) / total, 1)
        aligned = round((sum(1 for i in items if i["skills_aligned"]) / total) * 100, 1)

        return FeedbackSummaryResponse(
            project_id=UUID(project_id),
            average_rating=avg,
            total_feedback_count=total,
            skills_aligned_percentage=aligned,
            feedback_list=[self._format_feedback(i, student_name="Student B (Demo)") for i in items],
        )


feedback_service = FeedbackService()
