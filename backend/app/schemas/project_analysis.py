"""
Pydantic Schemas for Project AI Analysis
========================================
Defines strongly typed payloads for AI project analysis, candidate skill extraction,
and embedding status reporting.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class ExtractedSkill(BaseModel):
    """
    Structured representation of a technical skill identified in project text.
    """
    skill_name: str = Field(..., description="Canonical or extracted name of the skill")
    skill_id: Optional[str] = Field(None, description="UUID matching master taxonomy if resolved")
    category: Optional[str] = Field(None, description="Domain category from taxonomy (e.g. ai_ml, backend)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score of the identification [0.0 - 1.0]")
    source: str = Field(..., description="Method of extraction (e.g., taxonomy_exact, taxonomy_alias, nlp_entity)")


class ProjectAnalysisResult(BaseModel):
    """
    Structured output returned by the project NLP analysis pipeline.
    """
    project_id: str = Field(..., description="Identifier of the analyzed project")
    normalized_description: str = Field(..., description="Preprocessed clean text used for downstream analysis")
    embedding_available: bool = Field(..., description="Whether a dense embedding vector was successfully generated")
    embedding_dimension: Optional[int] = Field(None, description="Dimensionality of the embedding model (e.g., 384)")
    model_name: Optional[str] = Field(None, description="Pretrained Sentence Transformer model identifier")
    extracted_skills: List[ExtractedSkill] = Field(
        default_factory=list,
        description="Identified skills aligned with the taxonomy",
    )
    analysis_status: str = Field(
        ...,
        description="Lifecycle status: 'completed' | 'partial' | 'not_ready'",
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Diagnostic warnings, model availability notices, or text quality notes",
    )
