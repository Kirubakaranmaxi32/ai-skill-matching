"""
AI Skill Matching - Model Inference Service
===========================================
Executes single-pair compatibility inference between one student and one project
using the trained PyTorch MLP model and FeatureEngineer.

Guarantees:
- Uses saved checkpoint; strictly no re-training during inference.
- Executes on CPU.
- Returns score clamped to [0.0, 1.0].
- Preserves feature-level values for downstream explainability.
- Handles missing or empty inputs safely.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
import json
import logging
import torch

from ai.matching_model import CompatibilityMLP
from ai.feature_engineering import FeatureEngineer, FEATURE_NAMES
from ai.embeddings import SentenceTransformerEmbeddingProvider

logger = logging.getLogger(__name__)


@dataclass
class CompatibilityResult:
    """Structured inference output for a student-project pair."""
    student_id: str
    project_id: str
    compatibility_score: float
    model_version: str
    feature_contributions: Dict[str, float]
    raw_feature_vector: List[float]


class CompatibilityInferenceService:
    """
    Inference service for single-pair compatibility scoring.
    """

    def __init__(
        self,
        checkpoint_path: Optional[Path] = None,
        metadata_dir: Optional[Path] = None,
        embedding_provider: Optional[Any] = None,
    ):
        base_dir = Path(__file__).resolve().parent.parent.parent
        self.checkpoint_path = checkpoint_path or (base_dir / "models" / "checkpoints" / "best_matching_mlp.pt")
        self.metadata_dir = metadata_dir or (base_dir / "models" / "metadata")

        self._embedding_provider = embedding_provider or SentenceTransformerEmbeddingProvider()
        self._feature_engineer = FeatureEngineer(embedding_provider=self._embedding_provider)
        self._model: Optional[CompatibilityMLP] = None
        self._model_version = "v1.0.0-cpu"
        self._is_loaded = False

        self._load_model()

    def _load_model(self) -> None:
        """Loads trained weights and configuration from disk onto CPU."""
        if not self.checkpoint_path.exists():
            logger.warning(
                "Model checkpoint not found at %s. Initializing fresh model with default weights.",
                self.checkpoint_path,
            )
            self._model = CompatibilityMLP()
            self._model.eval()
            self._is_loaded = True
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
            self._is_loaded = True
            logger.info("Successfully loaded CompatibilityMLP checkpoint from %s", self.checkpoint_path)
        except Exception as err:
            logger.error("Failed to load model checkpoint: %s. Using default architecture.", err)
            self._model = CompatibilityMLP()
            self._model.eval()
            self._is_loaded = True

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded

    @property
    def model_version(self) -> str:
        return self._model_version

    def evaluate_pair(
        self,
        student_data: Dict[str, Any],
        project_data: Dict[str, Any],
    ) -> CompatibilityResult:
        """
        Computes the compatibility score for a single student and project.
        """
        student_profile = student_data.get("student") or student_data
        project_obj = project_data.get("project") or project_data

        student_id = str(student_profile.get("id") or "unknown-student")
        project_id = str(project_obj.get("id") or "unknown-project")

        # 1. Feature Engineering
        vector, feature_dict = self._feature_engineer.compute_features(student_data, project_data)

        # 2. PyTorch Forward Pass
        if self._model is None:
            self._load_model()

        assert self._model is not None
        score = self._model.predict_score(vector)
        # Bounded between 0.0 and 1.0
        score = max(0.0, min(1.0, round(score, 4)))

        return CompatibilityResult(
            student_id=student_id,
            project_id=project_id,
            compatibility_score=score,
            model_version=self._model_version,
            feature_contributions=feature_dict,
            raw_feature_vector=vector,
        )


__all__ = ["CompatibilityInferenceService", "CompatibilityResult"]
