"""
AI Skill Matching - Model Evaluation Module
===========================================
Calculates standard continuous regression metrics (MAE, MSE, RMSE, R²)
for student-project compatibility models on held-out test datasets.

IMPORTANT NOTICE:
Metrics evaluated here are strictly computed on synthetic development data.
They establish model learning fidelity under defined mathematical dynamics,
NOT validated performance across human students or live university cohorts.
"""

from typing import Dict, Any
import math
import json
from pathlib import Path
import torch
import torch.nn as nn


class ModelEvaluator:
    """
    Computes statistical evaluation metrics on held-out datasets.
    """

    @staticmethod
    def evaluate(
        model: nn.Module,
        X_test: torch.Tensor,
        y_test: torch.Tensor,
        save_path: Path = None,
    ) -> Dict[str, float]:
        """
        Evaluates the model and computes MAE, MSE, RMSE, and R2.
        """
        model.eval()
        device = torch.device("cpu")
        model.to(device)

        with torch.no_grad():
            preds = model(X_test.to(device))
            y_true = y_test.to(device)

            diff = preds - y_true
            abs_diff = torch.abs(diff)
            sq_diff = diff ** 2

            n = float(y_true.size(0))
            mae = float(torch.sum(abs_diff).item() / max(1.0, n))
            mse = float(torch.sum(sq_diff).item() / max(1.0, n))
            rmse = float(math.sqrt(mse))

            # R-squared calculation: 1 - (SS_res / SS_tot)
            y_mean = torch.mean(y_true)
            ss_tot = float(torch.sum((y_true - y_mean) ** 2).item())
            ss_res = float(torch.sum(sq_diff).item())

            if ss_tot > 1e-9:
                r2 = float(1.0 - (ss_res / ss_tot))
            else:
                r2 = 0.0

        metrics = {
            "evaluation_type": "synthetic_held_out_test_set",
            "samples_evaluated": int(n),
            "mae": round(mae, 6),
            "mse": round(mse, 6),
            "rmse": round(rmse, 6),
            "r2": round(r2, 6),
            "disclaimer": "Evaluated exclusively on synthetic development data; does not establish live human recommendation accuracy.",
        }

        if save_path:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(metrics, f, indent=2)

        return metrics
