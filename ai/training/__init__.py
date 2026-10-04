"""
AI Skill Matching - Model Training Architecture
==============================================
Training routines, synthetic data generation, and checkpointing for
the PyTorch CompatibilityMLP model.
"""

from ai.training.synthetic_dataset import (
    generate_synthetic_features_and_targets,
    create_and_save_synthetic_datasets,
)
from ai.training.trainer import CompatibilityModelTrainer

__all__ = [
    "generate_synthetic_features_and_targets",
    "create_and_save_synthetic_datasets",
    "CompatibilityModelTrainer",
]
