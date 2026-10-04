"""
AI Skill Matching - PyTorch MLP Compatibility Model
===================================================
A Multi-Layer Perceptron (MLP) neural network designed to estimate continuous
compatibility scores in [0.0, 1.0] between a student profile and a project requirement
vector.

Architecture:
  Input (10 features)
    │
  Linear(10 -> 64)
    │
   ReLU
    │
  Dropout(p=0.1)
    │
  Linear(64 -> 32)
    │
   ReLU
    │
  Dropout(p=0.1)
    │
  Linear(32 -> 1)
    │
  Sigmoid
    │
  Compatibility Score [0.0, 1.0]
"""

from typing import List, Dict, Any, Tuple
import torch
import torch.nn as nn

DEFAULT_INPUT_DIM: int = 10
DEFAULT_HIDDEN_DIMS: Tuple[int, int] = (64, 32)
DEFAULT_DROPOUT: float = 0.1


class CompatibilityMLP(nn.Module):
    """
    Feed-Forward PyTorch Neural Network for student-project compatibility scoring.
    """

    def __init__(
        self,
        input_dim: int = DEFAULT_INPUT_DIM,
        hidden_dims: Tuple[int, int] = DEFAULT_HIDDEN_DIMS,
        dropout: float = DEFAULT_DROPOUT,
    ):
        super().__init__()
        self.input_dim = input_dim
        self.hidden_dims = hidden_dims
        self.dropout_rate = dropout

        # Fully connected layers
        self.fc1 = nn.Linear(input_dim, hidden_dims[0])
        self.relu1 = nn.ReLU()
        self.dropout1 = nn.Dropout(dropout)

        self.fc2 = nn.Linear(hidden_dims[0], hidden_dims[1])
        self.relu2 = nn.ReLU()
        self.dropout2 = nn.Dropout(dropout)

        self.fc3 = nn.Linear(hidden_dims[1], 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.
        Args:
            x: Input tensor of shape (batch_size, input_dim)
        Returns:
            Compatibility score tensor of shape (batch_size, 1) in range [0.0, 1.0]
        """
        out = self.fc1(x)
        out = self.relu1(out)
        out = self.dropout1(out)

        out = self.fc2(out)
        out = self.relu2(out)
        out = self.dropout2(out)

        out = self.fc3(out)
        out = self.sigmoid(out)
        return out

    def predict_score(self, feature_vector: List[float]) -> float:
        """
        Performs CPU inference for a single 10-dimensional feature vector.
        Safe against training mode artifacts (eval mode, no grad).
        """
        self.eval()
        with torch.no_grad():
            tensor_in = torch.tensor([feature_vector], dtype=torch.float32, device="cpu")
            score_tensor = self.forward(tensor_in)
            return float(score_tensor.item())

    def get_model_config(self) -> Dict[str, Any]:
        """Returns architectural hyperparameters and layer dimensions."""
        return {
            "model_type": "CompatibilityMLP",
            "input_dim": self.input_dim,
            "hidden_dims": list(self.hidden_dims),
            "dropout": self.dropout_rate,
            "activation": "ReLU",
            "output_activation": "Sigmoid",
            "target_range": [0.0, 1.0],
            "total_trainable_parameters": sum(p.numel() for p in self.parameters() if p.requires_grad),
        }


__all__ = [
    "CompatibilityMLP",
    "DEFAULT_INPUT_DIM",
    "DEFAULT_HIDDEN_DIMS",
    "DEFAULT_DROPOUT",
]
