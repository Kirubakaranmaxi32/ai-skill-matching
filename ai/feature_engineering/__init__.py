"""
AI Skill Matching - Feature Engineering Module
==============================================
Constructs numerical feature vectors representing compatibility between a candidate
student and a target project specification.

Guarantees:
- Deterministic and reproducible calculations.
- Fixed input dimensionality for the PyTorch MLP.
- Strictly uses available database schema data; no fabricated attributes.
- Features are normalized to [0.0, 1.0].
- Exposes feature names, meanings, and explainability metadata.
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
import math
import logging

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FeatureMetadata:
    """Metadata specification for a single matching feature."""
    name: str
    index: int
    min_value: float
    max_value: float
    description: str


# Canonical 10-dimensional matching feature definitions
FEATURE_DEFINITIONS: List[FeatureMetadata] = [
    FeatureMetadata(
        name="skill_coverage_ratio",
        index=0,
        min_value=0.0,
        max_value=1.0,
        description="Proportion of project required skills possessed by the student.",
    ),
    FeatureMetadata(
        name="mean_proficiency_matched",
        index=1,
        min_value=0.0,
        max_value=1.0,
        description="Mean proficiency (normalized to [0,1]) of the student for matched skills.",
    ),
    FeatureMetadata(
        name="proficiency_deficit_ratio",
        index=2,
        min_value=0.0,
        max_value=1.0,
        description="Average normalized deficit below required proficiency across all required skills.",
    ),
    FeatureMetadata(
        name="proficiency_surplus_ratio",
        index=3,
        min_value=0.0,
        max_value=1.0,
        description="Average normalized surplus where student proficiency exceeds required proficiency.",
    ),
    FeatureMetadata(
        name="unmatched_skills_count_norm",
        index=4,
        min_value=0.0,
        max_value=1.0,
        description="Proportion of project required skills missing from the student profile.",
    ),
    FeatureMetadata(
        name="semantic_description_similarity",
        index=5,
        min_value=0.0,
        max_value=1.0,
        description="Cosine similarity between project description and student portfolio embeddings.",
    ),
    FeatureMetadata(
        name="interest_domain_overlap",
        index=6,
        min_value=0.0,
        max_value=1.0,
        description="Jaccard overlap between student interest categories and project skill domain categories.",
    ),
    FeatureMetadata(
        name="academic_seniority_norm",
        index=7,
        min_value=0.0,
        max_value=1.0,
        description="Student academic year normalized from year 1 (0.0) to year 5 (1.0).",
    ),
    FeatureMetadata(
        name="prior_project_experience_norm",
        index=8,
        min_value=0.0,
        max_value=1.0,
        description="Count of previous completed projects, normalized and saturated at 5.",
    ),
    FeatureMetadata(
        name="certification_count_norm",
        index=9,
        min_value=0.0,
        max_value=1.0,
        description="Count of verified technical certifications, normalized and saturated at 4.",
    ),
]

FEATURE_NAMES: List[str] = [f.name for f in FEATURE_DEFINITIONS]
FEATURE_COUNT: int = len(FEATURE_DEFINITIONS)


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Computes cosine similarity between two float vectors."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 <= 1e-9 or norm2 <= 1e-9:
        return 0.0
    return dot / (norm1 * norm2)


class FeatureEngineer:
    """
    Constructs normalized 10-dimensional numerical vectors and explainability
    breakdowns for student-project pairs.
    """

    def __init__(self, embedding_provider: Optional[Any] = None):
        self._embedding_provider = embedding_provider

    @property
    def feature_names(self) -> List[str]:
        return list(FEATURE_NAMES)

    @property
    def feature_count(self) -> int:
        return FEATURE_COUNT

    @classmethod
    def get_feature_metadata(cls) -> List[Dict[str, Any]]:
        return [asdict(f) for f in FEATURE_DEFINITIONS]

    def compute_features(
        self,
        student_data: Dict[str, Any],
        project_data: Dict[str, Any],
    ) -> Tuple[List[float], Dict[str, float]]:
        """
        Calculates the feature vector for ONE student and ONE project.
        
        Args:
            student_data: Dictionary containing:
                - student: profile dict (academic_year, etc.)
                - skills: list of dicts with skill_id, proficiency_level (1-4), category
                - interests: list of dicts with interest_id, category/name
                - previous_projects: list of previous project dicts
                - certifications: list of certification dicts
            project_data: Dictionary containing:
                - project: project dict (id, title, description)
                - required_skills: list of dicts with skill_id, required_proficiency (1-4), category
        
        Returns:
            Tuple of (numerical_vector [len=10], feature_dict {name: value})
        """
        student_profile = student_data.get("student") or student_data
        student_skills = student_data.get("skills") or []
        student_interests = student_data.get("interests") or []
        previous_projects = student_data.get("previous_projects") or []
        certifications = student_data.get("certifications") or []

        project_obj = project_data.get("project") or project_data
        required_skills = project_data.get("required_skills") or []

        # ----------------------------------------------------------------------
        # A. Skill Coverage & Proficiency Analysis
        # ----------------------------------------------------------------------
        # Map student skills: {skill_id: proficiency_level (1-4)}
        student_skill_map: Dict[str, int] = {}
        for s in student_skills:
            sid = str(s.get("skill_id") or s.get("id") or "")
            if sid:
                prof = int(s.get("proficiency_level") or s.get("proficiency") or 1)
                student_skill_map[sid] = max(1, min(4, prof))

        # Map required skills: {skill_id: required_proficiency (1-4)}
        project_req_map: Dict[str, int] = {}
        project_skill_categories: set = set()
        for r in required_skills:
            rid = str(r.get("skill_id") or r.get("id") or "")
            if rid:
                r_prof = int(r.get("required_proficiency") or r.get("proficiency") or 1)
                project_req_map[rid] = max(1, min(4, r_prof))
                cat = r.get("category")
                if cat:
                    project_skill_categories.add(cat.lower())

        num_required = len(project_req_map)

        if num_required == 0:
            # When project specifies no formal required skills
            coverage_ratio = 1.0
            mean_matched_prof = 0.5
            deficit_ratio = 0.0
            surplus_ratio = 0.0
            unmatched_norm = 0.0
        else:
            matched_ids = [sid for sid in project_req_map if sid in student_skill_map]
            num_matched = len(matched_ids)

            # Feature 0: skill_coverage_ratio
            coverage_ratio = num_matched / float(num_required)

            # Feature 1: mean_proficiency_matched (normalized to [0,1])
            if num_matched > 0:
                mean_matched_prof = sum(student_skill_map[sid] for sid in matched_ids) / (4.0 * num_matched)
            else:
                mean_matched_prof = 0.0

            # Feature 2: proficiency_deficit_ratio
            total_deficit = 0.0
            for rid, req_prof in project_req_map.items():
                stu_prof = student_skill_map.get(rid, 0)
                if stu_prof < req_prof:
                    total_deficit += (req_prof - stu_prof)
            deficit_ratio = total_deficit / (4.0 * num_required)

            # Feature 3: proficiency_surplus_ratio
            total_surplus = 0.0
            for rid, req_prof in project_req_map.items():
                stu_prof = student_skill_map.get(rid, 0)
                if stu_prof > req_prof:
                    total_surplus += (stu_prof - req_prof)
            # Max possible surplus per skill is 3 (level 4 vs level 1)
            surplus_ratio = total_surplus / (3.0 * num_required)

            # Feature 4: unmatched_skills_count_norm
            unmatched_norm = (num_required - num_matched) / float(num_required)

        # ----------------------------------------------------------------------
        # C. Semantic Description Similarity
        # ----------------------------------------------------------------------
        # Feature 5: semantic_description_similarity
        semantic_sim = 0.5  # Neutral fallback
        if self._embedding_provider and hasattr(self._embedding_provider, "embed_text"):
            proj_text = f"{project_obj.get('title', '')} {project_obj.get('description', '')}".strip()
            
            # Formulate student profile text from skills and past projects
            stu_skill_names = [
                s.get("skill_name") or s.get("name") or ""
                for s in student_skills
                if s.get("skill_name") or s.get("name")
            ]
            stu_proj_texts = [
                f"{p.get('title', '')} {p.get('description', '')}"
                for p in previous_projects
            ]
            stu_text = f"{' '.join(stu_skill_names)} {' '.join(stu_proj_texts)}".strip()

            if proj_text and stu_text:
                try:
                    p_emb = self._embedding_provider.embed_text(proj_text)
                    s_emb = self._embedding_provider.embed_text(stu_text)
                    if p_emb and s_emb:
                        cos = cosine_similarity(p_emb, s_emb)
                        # Scale cosine from [-1.0, 1.0] to [0.0, 1.0]
                        semantic_sim = max(0.0, min(1.0, (1.0 + max(-1.0, min(1.0, cos))) / 2.0))
                except Exception as err:
                    logger.debug("Semantic embedding comparison failed, using neutral fallback: %s", err)
                    semantic_sim = 0.5

        # ----------------------------------------------------------------------
        # D. Interest Domain Alignment
        # ----------------------------------------------------------------------
        # Feature 6: interest_domain_overlap
        student_interest_domains: set = set()
        for i in student_interests:
            cat = i.get("category") or i.get("name") or ""
            if cat:
                student_interest_domains.add(cat.lower())

        if project_skill_categories and student_interest_domains:
            common = project_skill_categories.intersection(student_interest_domains)
            total = project_skill_categories.union(student_interest_domains)
            interest_overlap = len(common) / float(len(total)) if total else 0.0
        elif not project_skill_categories and student_interest_domains:
            interest_overlap = 0.5
        else:
            interest_overlap = 0.0

        # ----------------------------------------------------------------------
        # E. Academic Seniority & Experience
        # ----------------------------------------------------------------------
        # Feature 7: academic_seniority_norm (years 1-5 -> 0.0-1.0)
        academic_year = student_profile.get("academic_year")
        if academic_year is None:
            academic_year = 1
        try:
            ay_int = max(1, min(5, int(academic_year)))
            seniority_norm = (ay_int - 1) / 4.0
        except (ValueError, TypeError):
            seniority_norm = 0.0

        # Feature 8: prior_project_experience_norm (saturated at 5 projects)
        prior_projects_count = len(previous_projects)
        experience_norm = min(5, prior_projects_count) / 5.0

        # Feature 9: certification_count_norm (saturated at 4 certifications)
        cert_count = len(certifications)
        cert_norm = min(4, cert_count) / 4.0

        # Construct vector and dictionary
        feature_dict: Dict[str, float] = {
            "skill_coverage_ratio": round(float(coverage_ratio), 4),
            "mean_proficiency_matched": round(float(mean_matched_prof), 4),
            "proficiency_deficit_ratio": round(float(deficit_ratio), 4),
            "proficiency_surplus_ratio": round(float(surplus_ratio), 4),
            "unmatched_skills_count_norm": round(float(unmatched_norm), 4),
            "semantic_description_similarity": round(float(semantic_sim), 4),
            "interest_domain_overlap": round(float(interest_overlap), 4),
            "academic_seniority_norm": round(float(seniority_norm), 4),
            "prior_project_experience_norm": round(float(experience_norm), 4),
            "certification_count_norm": round(float(cert_norm), 4),
        }

        # Vector in canonical order matching FEATURE_DEFINITIONS
        vector = [feature_dict[name] for name in FEATURE_NAMES]
        return vector, feature_dict


__all__ = [
    "FeatureMetadata",
    "FEATURE_DEFINITIONS",
    "FEATURE_NAMES",
    "FEATURE_COUNT",
    "FeatureEngineer",
    "cosine_similarity",
]
