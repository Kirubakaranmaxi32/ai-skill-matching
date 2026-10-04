"""
AI Skill Matching - Embedding Architecture
==========================================
Provides interfaces and adapters for converting project descriptions
and skills into dense semantic representations using pretrained Sentence Transformers.
"""

from typing import List, Optional, Protocol, Union, Dict, Any
import logging

logger = logging.getLogger(__name__)


class BaseEmbeddingProvider(Protocol):
    """
    Protocol defining the interface for text embedding providers.
    Enables pluggable embedding architectures (Sentence Transformers, Ollama, etc.).
    """

    @property
    def model_name(self) -> str:
        """Name or identifier of the pretrained embedding model."""
        ...

    @property
    def embedding_dimension(self) -> Optional[int]:
        """Expected dimensionality of generated embedding vectors (e.g. 384)."""
        ...

    @property
    def is_available(self) -> bool:
        """Indicates if the model weights and runtime dependencies are available."""
        ...

    @property
    def status_message(self) -> str:
        """Detailed status explanation (e.g., ready, missing weights, not installed)."""
        ...

    def embed_text(self, text: str) -> Optional[List[float]]:
        """
        Convert input text into a dense vector of floats.
        Returns None if model is unavailable or text cannot be embedded.
        """
        ...


class SentenceTransformerEmbeddingProvider:
    """
    Pretrained Sentence Transformer embedding provider.
    
    NOTE:
    The Sentence Transformer model is a pretrained NLP representation component
    (e.g., sentence-transformers/all-MiniLM-L6-v2), NOT our trained Deep Learning model.
    The trainable Deep Learning model will be the PyTorch MLP implemented in subsequent steps.
    """

    # Class-level cache to share model weights across services and eliminate duplicate memory allocations
    _cached_models: Dict[str, Any] = {}

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self._model_name = model_name
        self._model = None
        self._is_available = False
        self._status_message = "Uninitialized"
        self._dimension: Optional[int] = None
        self._initialize()

    def _initialize(self) -> None:
        # Check class-level cache first
        if self._model_name in SentenceTransformerEmbeddingProvider._cached_models:
            cached = SentenceTransformerEmbeddingProvider._cached_models[self._model_name]
            self._model = cached["model"]
            self._dimension = cached["dimension"]
            self._is_available = True
            self._status_message = "Ready"
            return

        try:
            import torch
            if torch.get_num_threads() > 2:
                torch.set_num_threads(2)
        except Exception:
            pass

        try:
            import sentence_transformers  # type: ignore
            # Explicitly load onto CPU device per system requirements
            try:
                self._model = sentence_transformers.SentenceTransformer(self._model_name, device="cpu")
                self._is_available = True
                self._status_message = "Ready"
                if hasattr(self._model, "get_embedding_dimension"):
                    self._dimension = int(self._model.get_embedding_dimension())
                elif hasattr(self._model, "get_sentence_embedding_dimension"):
                    self._dimension = int(self._model.get_sentence_embedding_dimension())
                SentenceTransformerEmbeddingProvider._cached_models[self._model_name] = {
                    "model": self._model,
                    "dimension": self._dimension,
                }
            except Exception as load_err:
                self._is_available = False
                self._status_message = f"Model weights not loaded: {str(load_err)}"
                logger.info("SentenceTransformer model weights unavailable: %s", load_err)
        except ImportError:
            self._is_available = False
            self._status_message = "sentence-transformers package not installed in environment"
            logger.info("sentence-transformers dependency not installed; embedding unavailable.")

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def embedding_dimension(self) -> Optional[int]:
        return self._dimension

    @property
    def is_available(self) -> bool:
        return self._is_available

    @property
    def status_message(self) -> str:
        return self._status_message

    def embed_text(self, text: str) -> Optional[List[float]]:
        if not self._is_available or self._model is None:
            return None
        if not text or not text.strip():
            return None

        try:
            embedding = self._model.encode(text, convert_to_numpy=True)
            return [float(x) for x in embedding.tolist()]
        except Exception as err:
            logger.error("Error generating text embedding: %s", err)
            return None
