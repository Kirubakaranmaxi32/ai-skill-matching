"""
Demonstration Service (Local Synthetic Dataset)
==============================================
Provides local, deterministic demonstration data and recommendations when
the remote Supabase database has zero/insufficient real records.

Guarantees:
- Never executes Supabase queries or mutations (no INSERT, UPDATE, DELETE).
- Never writes demo records to any database table.
- Reuses the existing Phase 5 Step 3 PyTorch CompatibilityMLP checkpoint and FeatureEngineer.
- Generates real model predictions; zero hardcoded or fabricated scores.
- Clearly flags all demo outputs with synthetic metadata.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import logging
from uuid import UUID
from fastapi import HTTPException, status

from app.core.config import settings
from app.schemas.recommendation import (
    ProjectRecommendationResponse,
    StudentRecommendation,
    FactualExplanation,
    MatchedSkillInfo,
    MissingSkillInfo,
)

# Root workspace path
root_workspace = Path(__file__).resolve().parent.parent.parent.parent
DEMO_DATA_DIR = root_workspace / "data" / "demo"

logger = logging.getLogger(__name__)


def is_demo_mode_active() -> bool:
    """Check if demonstration mode is globally enabled via settings."""
    return bool(getattr(settings, "DEMO_MODE", False))


def load_demo_students() -> List[Dict[str, Any]]:
    """
    Loads local synthetic student profiles from data/demo/students.json.
    Validates metadata and ensures records are clearly marked as synthetic.
    """
    students_file = DEMO_DATA_DIR / "students.json"
    if not students_file.exists():
        raise FileNotFoundError(f"Demo students dataset not found at {students_file}")

    with open(students_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    meta = data.get("_metadata", {})
    if meta.get("dataset_type") != "DEMO" or not meta.get("synthetic"):
        raise ValueError("Invalid demo students file: missing DEMO synthetic metadata")

    return data.get("students", [])


def load_demo_projects() -> List[Dict[str, Any]]:
    """
    Loads local synthetic projects from data/demo/projects.json.
    Validates metadata and ensures records are clearly marked as synthetic.
    """
    projects_file = DEMO_DATA_DIR / "projects.json"
    if not projects_file.exists():
        raise FileNotFoundError(f"Demo projects dataset not found at {projects_file}")

    with open(projects_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    meta = data.get("_metadata", {})
    if meta.get("dataset_type") != "DEMO" or not meta.get("synthetic"):
        raise ValueError("Invalid demo projects file: missing DEMO synthetic metadata")

    return data.get("projects", [])


def get_demo_project_by_id(project_id: str) -> Dict[str, Any]:
    """Retrieve a single demo project by its UUID or identifier."""
    projects = load_demo_projects()
    for p in projects:
        if str(p.get("id")) == str(project_id):
            return p
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Demo project not found with ID: {project_id}",
    )


class DemoRecommendationService:
    """
    Executes the recommendation engine against local synthetic demo records.
    Strictly read-only; never touches Supabase.
    """

    def __init__(self, engine: Optional[Any] = None):
        # Lazy import of RecommendationEngine to reuse existing PyTorch MLP
        from ai.recommendation import RecommendationEngine
        self._engine = engine or RecommendationEngine()

    @property
    def model_version(self) -> str:
        return f"{self._engine.model_version}-demo"

    def get_demo_recommendations(
        self,
        project_id: str,
        top_k: int = 10,
        min_score: float = 0.0,
    ) -> ProjectRecommendationResponse:
        """
        Runs candidate discovery, feature engineering, and PyTorch MLP inference
        on demo data using the existing recommendation engine.
        """
        # 1. Retrieve target demo project
        demo_project = get_demo_project_by_id(project_id)
        owner_id = str(demo_project.get("owner_id"))
        existing_members = {str(m.get("student_id")) for m in demo_project.get("members", [])}
        excluded_ids = {owner_id} | existing_members

        # 2. Retrieve demo students and filter eligible candidates
        all_students = load_demo_students()
        eligible_candidates: List[Dict[str, Any]] = []

        for s in all_students:
            sid = str(s["id"])
            if sid in excluded_ids:
                continue

            # Format candidate into the structure expected by RecommendationEngine
            candidate_record = {
                "student": {
                    "id": sid,
                    "full_name": s.get("full_name"),
                    "academic_year": s.get("academic_year"),
                    "department": s.get("department"),
                },
                "skills": [
                    {
                        "skill_id": str(sk.get("skill_id")),
                        "skill_name": sk.get("skill_name"),
                        "proficiency_level": sk.get("proficiency_level", 2),
                        "category": sk.get("category", "ai_ml"),
                    }
                    for sk in s.get("skills", [])
                ],
                "interests": [
                    {
                        "category": i.get("category", "ai_ml"),
                        "name": i.get("name", "Artificial Intelligence"),
                    }
                    for i in s.get("interests", [])
                ],
                "previous_projects": s.get("previous_projects", []),
                "certifications": s.get("certifications", []),
            }
            eligible_candidates.append(candidate_record)

        # 3. Format project into structure expected by RecommendationEngine
        project_data = {
            "project": {
                "id": str(demo_project["id"]),
                "title": demo_project["title"],
                "description": demo_project["description"],
            },
            "required_skills": [
                {
                    "skill_id": str(rs.get("skill_id")),
                    "skill_name": rs.get("skill_name"),
                    "required_proficiency": rs.get("required_proficiency", 2),
                    "category": rs.get("category", "ai_ml"),
                }
                for rs in demo_project.get("required_skills", [])
            ],
        }

        # 4. Score and Rank candidates using the real trained MLP
        scored_recommendations = self._engine.score_and_rank_candidates(
            project_data=project_data,
            eligible_candidates=eligible_candidates,
            top_k=top_k,
            min_score=min_score,
        )

        # 5. Format into ProjectRecommendationResponse with invitation tracking
        from app.services.invitation_service import _demo_invitations_store
        demo_proj_id = str(demo_project["id"])
        demo_invs_by_student = {
            inv["invited_student_id"]: inv
            for inv in _demo_invitations_store.values()
            if inv["project_id"] == demo_proj_id
        }

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
            demo_inv = demo_invs_by_student.get(sid_str)
            inv_status = demo_inv.get("status") if demo_inv else None
            inv_id = UUID(str(demo_inv["id"])) if demo_inv and demo_inv.get("id") else None

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
            project_id=UUID(demo_project["id"]),
            project_title=demo_project["title"],
            total_eligible_candidates=len(eligible_candidates),
            returned_recommendations_count=len(formatted_recs),
            min_score_threshold=min_score,
            model_version=self.model_version,
            recommendations=formatted_recs,
        )
