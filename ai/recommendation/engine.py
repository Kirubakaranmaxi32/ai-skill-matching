"""
AI Skill Matching - Recommendation Engine
=========================================
Implements candidate scoring, ranking, filtering, and factual explanation
generation using the trained PyTorch CompatibilityMLP and FeatureEngineer.

Guarantees:
- Reuses the existing trained PyTorch MLP checkpoint (never retrains).
- Evaluates on CPU.
- Real continuous compatibility scores, zero hard-coded scores.
- Candidate discovery filtering (excludes owner and existing project members).
- Deterministic descending rank ordering with Top-K and threshold filtering.
- Factual explanations derived strictly from actual skill and profile signals.
"""

from typing import Dict, Any, List, Optional, Tuple, Union
from pathlib import Path
import logging
import torch

from ai.matching_model import CompatibilityMLP
from ai.feature_engineering import FeatureEngineer
from ai.embeddings import SentenceTransformerEmbeddingProvider

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """
    Core algorithmic engine for scoring and ranking candidate students for projects.
    """

    def __init__(
        self,
        checkpoint_path: Optional[Union[Path, str]] = None,
        embedding_provider: Optional[Any] = None,
    ):
        base_dir = Path(__file__).resolve().parent.parent.parent
        self.checkpoint_path = Path(checkpoint_path) if checkpoint_path else (base_dir / "models" / "checkpoints" / "best_matching_mlp.pt")
        self._embedding_provider = embedding_provider or SentenceTransformerEmbeddingProvider()
        self._feature_engineer = FeatureEngineer(embedding_provider=self._embedding_provider)
        self._model: Optional[CompatibilityMLP] = None
        self._model_version = "v1.0.0-cpu"
        self._load_model()

    def _load_model(self) -> None:
        """Loads trained weights onto CPU once during initialization."""
        if not self.checkpoint_path.exists():
            logger.warning(
                "Model checkpoint not found at %s. Initializing fresh CompatibilityMLP.",
                self.checkpoint_path,
            )
            self._model = CompatibilityMLP()
            self._model.eval()
            return

        try:
            checkpoint = torch.load(self.checkpoint_path, map_location="cpu", weights_only=False)
            config = checkpoint.get("model_config", {})
            input_dim = config.get("input_dim", 10)
            hidden_dims = tuple(config.get("hidden_dims", [64, 32]))
            dropout = config.get("dropout", 0.1)

            self._model = CompatibilityMLP(
                input_dim=input_dim,
                hidden_dims=hidden_dims,
                dropout=dropout,
            )
            self._model.load_state_dict(checkpoint["model_state_dict"])
            self._model.eval()
            logger.info("RecommendationEngine loaded trained MLP from %s", self.checkpoint_path)
        except Exception as err:
            logger.error("Failed to load model checkpoint in RecommendationEngine: %s", err)
            self._model = CompatibilityMLP()
            self._model.eval()

    @property
    def model_version(self) -> str:
        return self._model_version

    @property
    def is_model_loaded(self) -> bool:
        return self._model is not None

    def score_and_rank_candidates(
        self,
        project_data: Dict[str, Any],
        eligible_candidates: List[Dict[str, Any]],
        top_k: int = 10,
        min_score: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """
        Scores all eligible candidates against the project requirements, filters by min_score,
        and returns Top-K ranked candidates in descending order of compatibility score.
        
        Args:
            project_data: Dict with 'project' and 'required_skills'
            eligible_candidates: List of candidate dicts with:
                - 'student': student profile dict
                - 'skills': student skills list
                - 'interests': student interests list
                - 'previous_projects': previous projects list
                - 'certifications': certifications list
            top_k: Maximum number of recommendations to return
            min_score: Minimum compatibility score threshold (0.0 to 1.0)
            
        Returns:
            List of structured recommendation dicts ordered by rank
        """
        if not eligible_candidates:
            return []

        project_obj = project_data.get("project") or project_data
        required_skills = project_data.get("required_skills") or []
        req_map: Dict[str, Dict[str, Any]] = {
            str(r.get("skill_id") or r.get("id")): r
            for r in required_skills
            if r.get("skill_id") or r.get("id")
        }

        scored_records: List[Dict[str, Any]] = []

        if self._model is None:
            self._load_model()

        assert self._model is not None

        for cand in eligible_candidates:
            student_profile = cand.get("student") or cand
            student_skills = cand.get("skills") or []
            student_id = str(student_profile.get("id") or "")
            student_name = student_profile.get("full_name", "Student Candidate")
            academic_year = student_profile.get("academic_year")

            # 1. Feature Engineering (deterministic 10-dim vector)
            vector, feature_dict = self._feature_engineer.compute_features(cand, project_data)

            # 2. PyTorch Forward Pass (CPU, no grad, eval mode)
            raw_score = self._model.predict_score(vector)
            score = max(0.0, min(1.0, round(raw_score, 4)))

            # Threshold Filter
            if score < min_score:
                continue

            # 3. Factual Explanation Generation
            stu_skill_map: Dict[str, int] = {}
            for s in student_skills:
                sid = str(s.get("skill_id") or s.get("id") or "")
                if sid:
                    prof = int(s.get("proficiency_level") or s.get("proficiency") or 1)
                    stu_skill_map[sid] = prof

            matched_skills_info: List[Dict[str, Any]] = []
            missing_skills_info: List[Dict[str, Any]] = []

            for rid, req_item in req_map.items():
                r_prof = int(req_item.get("required_proficiency") or req_item.get("proficiency") or 1)
                s_name = req_item.get("skill_name") or req_item.get("name") or "Technical Skill"
                cat = req_item.get("category")

                if rid in stu_skill_map:
                    stu_prof = stu_skill_map[rid]
                    matched_skills_info.append({
                        "skill_id": rid,
                        "skill_name": s_name,
                        "student_proficiency": stu_prof,
                        "required_proficiency": r_prof,
                        "category": cat,
                    })
                else:
                    missing_skills_info.append({
                        "skill_id": rid,
                        "skill_name": s_name,
                        "required_proficiency": r_prof,
                        "category": cat,
                    })

            # Sort matched skills by proficiency descending
            matched_skills_info.sort(key=lambda x: -x["student_proficiency"])

            explanation = {
                "matched_skills": matched_skills_info,
                "missing_skills": missing_skills_info,
                "skill_coverage_ratio": feature_dict["skill_coverage_ratio"],
                "proficiency_alignment": round(max(0.0, 1.0 - feature_dict["proficiency_deficit_ratio"]), 4),
                "interest_overlap": feature_dict["interest_domain_overlap"],
                "experience_signal": feature_dict["prior_project_experience_norm"],
            }

            scored_records.append({
                "student_id": student_id,
                "student_name": student_name,
                "academic_year": academic_year,
                "compatibility_score": score,
                "matched_skill_count": len(matched_skills_info),
                "required_skill_count": len(req_map),
                "skill_coverage_ratio": feature_dict["skill_coverage_ratio"],
                "mean_proficiency_matched": feature_dict["mean_proficiency_matched"],
                "proficiency_deficit_ratio": feature_dict["proficiency_deficit_ratio"],
                "interest_domain_overlap": feature_dict["interest_domain_overlap"],
                "prior_project_experience_norm": feature_dict["prior_project_experience_norm"],
                "certification_count_norm": feature_dict["certification_count_norm"],
                "explanation": explanation,
            })

        # 4. Deterministic Ranking
        # Sort primary: compatibility_score DESC
        # Secondary: skill_coverage_ratio DESC
        # Tertiary: student_id ASC (for deterministic tie-breaking)
        scored_records.sort(
            key=lambda item: (
                -item["compatibility_score"],
                -item["skill_coverage_ratio"],
                item["student_id"],
            )
        )

        # 5. Assign Rank and Top-K Truncation
        top_records = scored_records[:top_k]
        for rank_idx, record in enumerate(top_records, start=1):
            record["rank"] = rank_idx

        return top_records
