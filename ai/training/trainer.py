"""
AI Skill Matching - Model Training Pipeline
===========================================
Executes reproducible training for the PyTorch CompatibilityMLP model
using train/validation splits, DataLoader batches, MSE loss tracking,
and best-model checkpointing.
"""

from typing import Dict, Any, List, Optional
import json
import time
from pathlib import Path
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader

from ai.matching_model import CompatibilityMLP
from ai.feature_engineering import FeatureEngineer

DEFAULT_SEED = 42
DEFAULT_LR = 0.001
DEFAULT_BATCH_SIZE = 32
DEFAULT_EPOCHS = 40
DEFAULT_WEIGHT_DECAY = 1e-4


class CompatibilityModelTrainer:
    """
    Orchestrates PyTorch MLP training with validation tracking and checkpointing.
    """

    def __init__(
        self,
        model: Optional[CompatibilityMLP] = None,
        learning_rate: float = DEFAULT_LR,
        batch_size: int = DEFAULT_BATCH_SIZE,
        epochs: int = DEFAULT_EPOCHS,
        weight_decay: float = DEFAULT_WEIGHT_DECAY,
        seed: int = DEFAULT_SEED,
    ):
        self.seed = seed
        self.learning_rate = learning_rate
        self.batch_size = batch_size
        self.epochs = epochs
        self.weight_decay = weight_decay

        # Enforce CPU reproducibility
        torch.manual_seed(self.seed)
        self.device = torch.device("cpu")

        self.model = model or CompatibilityMLP()
        self.model.to(self.device)

        self.criterion = nn.MSELoss()
        self.optimizer = torch.optim.Adam(
            self.model.parameters(),
            lr=self.learning_rate,
            weight_decay=self.weight_decay,
        )

    def train(
        self,
        X_train: torch.Tensor,
        y_train: torch.Tensor,
        X_val: torch.Tensor,
        y_val: torch.Tensor,
        models_dir: Path,
    ) -> Dict[str, Any]:
        """
        Executes training and validation loops, saving the best checkpoint.
        """
        torch.manual_seed(self.seed)
        train_dataset = TensorDataset(X_train, y_train)
        val_dataset = TensorDataset(X_val, y_val)

        train_loader = DataLoader(train_dataset, batch_size=self.batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=self.batch_size, shuffle=False)

        history: List[Dict[str, Any]] = []
        best_val_loss = float("inf")
        best_epoch = 0
        best_state_dict = None

        checkpoints_dir = models_dir / "checkpoints"
        metadata_dir = models_dir / "metadata"
        checkpoints_dir.mkdir(parents=True, exist_ok=True)
        metadata_dir.mkdir(parents=True, exist_ok=True)

        start_time = time.time()

        for epoch in range(1, self.epochs + 1):
            # Training epoch
            self.model.train()
            train_running_loss = 0.0
            train_batches = 0

            for batch_x, batch_y in train_loader:
                batch_x, batch_y = batch_x.to(self.device), batch_y.to(self.device)
                self.optimizer.zero_grad()
                predictions = self.model(batch_x)
                loss = self.criterion(predictions, batch_y)
                loss.backward()
                self.optimizer.step()

                train_running_loss += loss.item()
                train_batches += 1

            epoch_train_loss = train_running_loss / max(1, train_batches)

            # Validation epoch
            self.model.eval()
            val_running_loss = 0.0
            val_batches = 0

            with torch.no_grad():
                for batch_x, batch_y in val_loader:
                    batch_x, batch_y = batch_x.to(self.device), batch_y.to(self.device)
                    predictions = self.model(batch_x)
                    loss = self.criterion(predictions, batch_y)
                    val_running_loss += loss.item()
                    val_batches += 1

            epoch_val_loss = val_running_loss / max(1, val_batches)

            # Track best checkpoint
            is_best = epoch_val_loss < best_val_loss
            if is_best:
                best_val_loss = epoch_val_loss
                best_epoch = epoch
                best_state_dict = {k: v.cpu().clone() for k, v in self.model.state_dict().items()}

            history.append({
                "epoch": epoch,
                "train_loss": round(float(epoch_train_loss), 6),
                "val_loss": round(float(epoch_val_loss), 6),
                "is_best": is_best,
            })

        duration = time.time() - start_time

        # Save best model checkpoint
        best_checkpoint_path = checkpoints_dir / "best_matching_mlp.pt"
        if best_state_dict is not None:
            torch.save(
                {
                    "epoch": best_epoch,
                    "model_state_dict": best_state_dict,
                    "val_loss": best_val_loss,
                    "model_config": self.model.get_model_config(),
                },
                best_checkpoint_path,
            )
            # Load best weights into active model instance
            self.model.load_state_dict(best_state_dict)

        # Save metadata artifacts
        feature_metadata = FeatureEngineer.get_feature_metadata()
        with open(metadata_dir / "feature_metadata.json", "w", encoding="utf-8") as f:
            json.dump(feature_metadata, f, indent=2)

        with open(metadata_dir / "model_config.json", "w", encoding="utf-8") as f:
            json.dump(self.model.get_model_config(), f, indent=2)

        training_summary = {
            "model_type": "CompatibilityMLP",
            "epochs_total": self.epochs,
            "best_epoch": best_epoch,
            "best_val_loss": round(float(best_val_loss), 6),
            "final_train_loss": history[-1]["train_loss"],
            "final_val_loss": history[-1]["val_loss"],
            "training_duration_seconds": round(duration, 2),
            "learning_rate": self.learning_rate,
            "batch_size": self.batch_size,
            "weight_decay": self.weight_decay,
            "random_seed": self.seed,
            "device": "cpu",
            "history": history,
        }
        with open(metadata_dir / "training_history.json", "w", encoding="utf-8") as f:
            json.dump(training_summary, f, indent=2)

        return training_summary
