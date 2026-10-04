"""
Recommendation Service
======================
Coordinates database lookups, candidate discovery, eligibility filtering,
and PyTorch MLP scoring/ranking for project team recommendations.
"""

from typing import Dict, Any, List, Optional, Set
import sys
from pathlib import Path
from uuid import UUID
from fastapi import HTTPException, status

from app.services.db_adapter import db
from app.services.student_service import get_or_create_student
from app.services.reference_service import get_skills
from app.schemas.recommendation import (
    ProjectRecommendationResponse,
    StudentRecommendation,
    FactualExplanation,
    MatchedSkillInfo,
    MissingSkillInfo,
)

# Ensure root workspace is available for ai package imports
root_workspace = Path(__file__).resolve().parent.parent.parent.parent
if str(root_workspace) not in sys.path:
    sys.path.insert(0, str(root_workspace))

from ai.recommendation import RecommendationEngine


class RecommendationService:
    """
    Coordinates data retrieval, eligibility filtering, and recommendation generation.
    """

    def __init__(self, engine: Optional[RecommendationEngine] = None):
        self._engine = engine or RecommendationEngine()

    @property
    def model_version(self) -> str:
        return self._engine.model_version

    def get_project_recommendations(
        self,
        project_id: str,
        user_id: str,
        top_k: int = 10,
        min_score: float = 0.0,
    ) -> ProjectRecommendationResponse:
        """
        Retrieves Top-K candidate student recommendations for a project.
        
        Security & Privacy:
        - Authenticated user must be the verified owner of the project (403 if unauthorized).
        - Project must exist (404 if not found).
        - Does NOT expose private user credentials or sensitive attributes.
        - Strictly read-only; does not mutate database or add members.
        """
        # 1. Retrieve project
        project = db.select_by_id("projects", project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        # 2. Verify requesting user is the project owner
        requesting_student = get_or_create_student(user_id)
        requesting_student_id = str(requesting_student["id"])
        project_owner_id = str(project.get("owner_id"))

        if project_owner_id != requesting_student_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the project owner can view candidate recommendations for this project",
            )

        # 3. Retrieve taxonomy map for skill enrichment
        taxonomy_skills: Dict[str, Dict[str, Any]] = {
            str(s["id"]): s for s in get_skills()
        }

        # 4. Retrieve project required skills
        project_skills = db.select_by_field("project_skills", "project_id", project_id)
        enriched_req_skills: List[Dict[str, Any]] = []
        for ps in project_skills:
            tax = taxonomy_skills.get(str(ps.get("skill_id")), {})
            enriched_req_skills.append({
                **ps,
                "skill_name": tax.get("name", "Technical Skill"),
                "category": tax.get("category", "general"),
            })

        project_data = {
            "project": project,
            "required_skills": enriched_req_skills,
        }

        # 5. Candidate Discovery & Eligibility Filtering
        # Exclude: (a) project owner, (b) existing project members, (c) invalid student records
        project_members = db.select_by_field("project_members", "project_id", project_id)
        excluded_student_ids: Set[str] = {project_owner_id}
        for pm in project_members:
            if pm.get("student_id"):
                excluded_student_ids.add(str(pm["student_id"]))

        all_students = db.select_all("students")
        eligible_candidates: List[Dict[str, Any]] = []

        for student_row in all_students:
            sid = str(student_row.get("id") or "")
            if not sid or not student_row.get("user_id"):
                continue  # Skip invalid records
            if sid in excluded_student_ids:
                continue  # Excluded owner or existing member

            # Retrieve candidate student profile relationships
            stu_skills = db.select_by_field("student_skills", "student_id", sid)
            enriched_stu_skills: List[Dict[str, Any]] = []
            for sk in stu_skills:
                tax = taxonomy_skills.get(str(sk.get("skill_id")), {})
                enriched_stu_skills.append({
                    **sk,
                    "skill_name": tax.get("name", "Technical Skill"),
                    "category": tax.get("category", "general"),
                })

            stu_interests = db.select_by_field("student_interests", "student_id", sid)
            stu_projects = db.select_by_field("previous_projects", "student_id", sid)
            stu_certs = db.select_by_field("certifications", "student_id", sid)

            eligible_candidates.append({
                "student": student_row,
                "skills": enriched_stu_skills,
                "interests": stu_interests,
                "previous_projects": stu_projects,
                "certifications": stu_certs,
            })

        # 6. Score, Rank, and Factual Explanation via RecommendationEngine
        scored_recommendations = self._engine.score_and_rank_candidates(
            project_data=project_data,
            eligible_candidates=eligible_candidates,
            top_k=top_k,
            min_score=min_score,
        )

        # 7. Query existing project invitations to attach status
        invitations = db.select_by_field("invitations", "project_id", project_id)
        inv_by_student: Dict[str, Dict[str, Any]] = {}
        for inv in sorted(invitations, key=lambda x: str(x.get("created_at", ""))):
            inv_by_student[str(inv.get("invited_student_id"))] = inv

        # 8. Format into strongly typed Pydantic response
        formatted_recs: List[StudentRecommendation] = []
        for rec in scored_recommendations:
            expl_dict = rec["explanation"]
            explanation = FactualExplanation(
                matched_skills=[
                    MatchedSkillInfo(**m) for m in expl_dict["matched_skills"]
                ],
                missing_skills=[
                    MissingSkillInfo(**m) for m in expl_dict["missing_skills"]
                ],
                skill_coverage_ratio=expl_dict["skill_coverage_ratio"],
                proficiency_alignment=expl_dict["proficiency_alignment"],
                interest_overlap=expl_dict["interest_overlap"],
                experience_signal=expl_dict["experience_signal"],
            )

            sid_str = str(rec["student_id"])
            student_inv = inv_by_student.get(sid_str)
            inv_status = student_inv.get("status") if student_inv else None
            inv_id = UUID(str(student_inv["id"])) if student_inv and student_inv.get("id") else None

            formatted_recs.append(
                StudentRecommendation(
                    rank=rec["rank"],
                    student_id=UUID(rec["student_id"]),
                    student_name=rec["student_name"],
                    academic_year=rec["academic_year"],
                    compatibility_score=rec["compatibility_score"],
                    matched_skill_count=rec["matched_skill_count"],
                    required_skill_count=rec["required_skill_count"],
                    skill_coverage_ratio=rec["skill_coverage_ratio"],
                    mean_proficiency_matched=rec["mean_proficiency_matched"],
                    proficiency_deficit_ratio=rec["proficiency_deficit_ratio"],
                    interest_domain_overlap=rec["interest_domain_overlap"],
                    prior_project_experience_norm=rec["prior_project_experience_norm"],
                    certification_count_norm=rec["certification_count_norm"],
                    explanation=explanation,
                    invitation_status=inv_status,
                    invitation_id=inv_id,
                )
            )

        return ProjectRecommendationResponse(
            project_id=UUID(project_id),
            project_title=project.get("title", "Project"),
            total_eligible_candidates=len(eligible_candidates),
            returned_recommendations_count=len(formatted_recs),
            min_score_threshold=min_score,
            model_version=self._engine.model_version,
            recommendations=formatted_recs,
        )


recommendation_service = RecommendationService()
