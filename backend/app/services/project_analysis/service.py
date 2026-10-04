"""
Project Analysis Service
========================
Coordinates text preprocessing, Sentence Transformer representation interface,
and taxonomy skill alignment for project specifications.
"""

from typing import List, Dict, Any, Optional
import sys
from pathlib import Path
from fastapi import HTTPException, status

from app.core.config import settings
from app.services.db_adapter import db
from app.services.student_service import get_or_create_student
from app.services.reference_service import get_skills
from app.schemas.project_analysis import ProjectAnalysisResult, ExtractedSkill
from app.services.project_analysis.preprocessor import TextPreprocessor

# Ensure root workspace is available for ai package imports
root_workspace = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(root_workspace) not in sys.path:
    sys.path.insert(0, str(root_workspace))

from ai.embeddings import SentenceTransformerEmbeddingProvider
from ai.skill_extraction import TaxonomyMatchSkillExtractor, CandidateSkill


class ProjectAnalysisService:
    """
    Service coordinating NLP analysis for project descriptions.
    """

    def __init__(self, model_name: Optional[str] = None):
        self._model_name = model_name or settings.SENTENCE_TRANSFORMER_MODEL
        self._embedding_provider = SentenceTransformerEmbeddingProvider(model_name=self._model_name)
        self._skill_extractor = TaxonomyMatchSkillExtractor()

    def analyze_project(self, project_id: str, user_id: str) -> ProjectAnalysisResult:
        """
        Executes text cleaning, skill extraction, and representation checks for a project.
        
        Security:
        - Authenticated user must be the verified owner of the project (403 if unauthorized).
        - Project must exist (404 if not found).
        
        Safety:
        - Never fabricates AI outputs or embeddings.
        - Does not write or mutate required project skills automatically.
        """
        # 1. Retrieve project
        project = db.select_by_id("projects", project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        # 2. Verify ownership
        student = get_or_create_student(user_id)
        if str(project.get("owner_id")) != str(student["id"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to analyze this project",
            )

        # 3. Text Preprocessing
        raw_description = project.get("description", "") or ""
        normalized_description = TextPreprocessor.clean(raw_description)
        is_trivial = TextPreprocessor.is_empty_or_trivial(normalized_description, min_length=10)

        warnings: List[str] = []

        if is_trivial:
            warnings.append(
                "Project description is empty or too short (< 10 characters) for comprehensive technical analysis."
            )

        # 4. Dense Text Embedding Representation
        embedding_available = False
        embedding_dimension: Optional[int] = None

        if not is_trivial:
            if self._embedding_provider.is_available:
                vector = self._embedding_provider.embed_text(normalized_description)
                if vector:
                    embedding_available = True
                    embedding_dimension = len(vector)
                else:
                    warnings.append("Text embedding could not be computed by the embedding provider.")
            else:
                warnings.append(
                    f"Sentence Transformer model ({self._model_name}) runtime unavailable: "
                    f"{self._embedding_provider.status_message}."
                )
        else:
            warnings.append("Embedding generation skipped due to insufficient description length.")

        # 5. Taxonomy Skill Identification
        extracted_skills: List[ExtractedSkill] = []
        if not is_trivial:
            taxonomy_skills = get_skills()
            candidates: List[CandidateSkill] = self._skill_extractor.extract_skills(
                normalized_description, taxonomy_skills
            )
            for cand in candidates:
                extracted_skills.append(
                    ExtractedSkill(
                        skill_name=cand.normalized_name,
                        skill_id=cand.matched_skill_id,
                        category=cand.category,
                        confidence=cand.confidence,
                        source=cand.source,
                    )
                )

        # 6. Lifecycle Analysis Status
        if is_trivial:
            analysis_status = "not_ready"
        elif embedding_available and len(extracted_skills) > 0:
            analysis_status = "completed"
        elif len(extracted_skills) > 0 or embedding_available:
            analysis_status = "partial"
        else:
            analysis_status = "completed" if embedding_available else "partial"

        return ProjectAnalysisResult(
            project_id=str(project["id"]),
            normalized_description=normalized_description,
            embedding_available=embedding_available,
            embedding_dimension=embedding_dimension,
            model_name=self._model_name,
            extracted_skills=extracted_skills,
            analysis_status=analysis_status,
            warnings=warnings,
        )


# Singleton service instance
project_analysis_service = ProjectAnalysisService()
