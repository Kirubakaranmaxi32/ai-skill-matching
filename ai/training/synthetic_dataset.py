"""
AI Skill Matching - Synthetic Dataset Generator
===============================================
Generates synthetic student-project feature vectors and non-linear compatibility
target scores for offline development and PyTorch MLP training.

IMPORTANT NOTICE:
This dataset is strictly SYNTHETIC for development purposes because real-world historical
student-project pairing outcomes do not yet exist in the college deployment.
- It is NOT inserted into Supabase.
- Results trained on this dataset represent development benchmarks, NOT validated real-world accuracy.
"""

from typing import Dict, Any, List, Tuple
import json
import random
import math
from pathlib import Path
import torch

from ai.feature_engineering import FEATURE_NAMES, FEATURE_COUNT

DEFAULT_SEED = 42
DEFAULT_SAMPLE_COUNT = 2000
DEFAULT_TRAIN_RATIO = 0.70
DEFAULT_VAL_RATIO = 0.15
DEFAULT_TEST_RATIO = 0.15


def generate_synthetic_features_and_targets(
    num_samples: int = DEFAULT_SAMPLE_COUNT,
    seed: int = DEFAULT_SEED,
) -> Tuple[List[List[float]], List[float]]:
    """
    Generates realistic 10-dimensional feature vectors and corresponding continuous
    compatibility target values in [0.0, 1.0].
    """
    random.seed(seed)
    features_list: List[List[float]] = []
    targets_list: List[float] = []

    for _ in range(num_samples):
        # 1. Academic Seniority: Year 1 to 5 -> [0.0, 1.0]
        year = random.randint(1, 5)
        seniority = (year - 1) / 4.0

        # 2. Prior Experience & Certifications (correlated with seniority)
        exp_lambda = 0.5 + 2.5 * seniority
        prior_projects = min(5, int(random.expovariate(1.0 / max(0.2, exp_lambda))))
        prior_experience = min(5, prior_projects) / 5.0

        cert_prob = 0.2 + 0.5 * seniority
        certs = sum(1 for _ in range(4) if random.random() < cert_prob)
        cert_norm = certs / 4.0

        # 3. Skill Coverage & Unmatched Skills
        coverage = round(random.betavariate(2.0, 2.0), 4)
        unmatched = round(1.0 - coverage, 4)

        # 4. Proficiencies
        if coverage > 0.05:
            matched_prof = round(random.uniform(0.3, 1.0), 4)
            deficit = round(max(0.0, min(1.0, (1.0 - matched_prof) * (1.0 - coverage * 0.5))), 4)
            surplus = round(max(0.0, min(1.0, (matched_prof - 0.5) * coverage)), 4)
        else:
            matched_prof = 0.0
            deficit = 1.0
            surplus = 0.0

        # 5. Semantic description similarity (beta distribution centered around 0.55)
        semantic_sim = round(random.betavariate(3.0, 2.5), 4)

        # 6. Interest domain overlap
        interest_overlap = round(random.choice([0.0, 0.25, 0.33, 0.5, 0.67, 0.75, 1.0]), 4)

        feature_vector = [
            coverage,           # 0: skill_coverage_ratio
            matched_prof,       # 1: mean_proficiency_matched
            deficit,            # 2: proficiency_deficit_ratio
            surplus,            # 3: proficiency_surplus_ratio
            unmatched,          # 4: unmatched_skills_count_norm
            semantic_sim,       # 5: semantic_description_similarity
            interest_overlap,   # 6: interest_domain_overlap
            seniority,          # 7: academic_seniority_norm
            prior_experience,   # 8: prior_project_experience_norm
            cert_norm,          # 9: certification_count_norm
        ]

        # Target Generation Logic (Non-linear compatibility score)
        # Base linear combination
        raw_score = (
            0.35 * coverage +
            0.20 * matched_prof -
            0.25 * deficit +
            0.08 * surplus +
            0.15 * semantic_sim +
            0.10 * interest_overlap +
            0.08 * seniority +
            0.08 * prior_experience +
            0.05 * cert_norm
        )

        # Non-linear domain dynamics
        # Low coverage penalty
        if coverage < 0.3:
            raw_score *= 0.60
        # High synergy bonus
        if coverage > 0.7 and semantic_sim > 0.65:
            raw_score += 0.06

        # Bounded realistic noise
        noise = random.gauss(0.0, 0.02)
        target = max(0.0, min(1.0, round(raw_score + noise, 4)))

        features_list.append(feature_vector)
        targets_list.append(target)

    return features_list, targets_list


def create_and_save_synthetic_datasets(
    data_dir: Path,
    num_samples: int = DEFAULT_SAMPLE_COUNT,
    seed: int = DEFAULT_SEED,
) -> Dict[str, Any]:
    """
    Generates and splits synthetic dataset into train, validation, and test sets.
    Saves PyTorch tensors and JSON metadata under data/ directories.
    """
    features, targets = generate_synthetic_features_and_targets(num_samples, seed)

    # Convert to PyTorch tensors
    X = torch.tensor(features, dtype=torch.float32)
    y = torch.tensor(targets, dtype=torch.float32).unsqueeze(1)

    num_train = int(num_samples * DEFAULT_TRAIN_RATIO)
    num_val = int(num_samples * DEFAULT_VAL_RATIO)
    num_test = num_samples - num_train - num_val

    # Shuffled split indices
    torch.manual_seed(seed)
    indices = torch.randperm(num_samples).tolist()

    train_idx = indices[:num_train]
    val_idx = indices[num_train:num_train + num_val]
    test_idx = indices[num_train + num_val:]

    X_train, y_train = X[train_idx], y[train_idx]
    X_val, y_val = X[val_idx], y[val_idx]
    X_test, y_test = X[test_idx], y[test_idx]

    # Ensure directories exist
    synthetic_dir = data_dir / "synthetic"
    training_dir = data_dir / "training"
    val_dir = data_dir / "validation"
    test_dir = data_dir / "test"

    for d in (synthetic_dir, training_dir, val_dir, test_dir):
        d.mkdir(parents=True, exist_ok=True)

    # Save PyTorch checkpoints
    torch.save({"X": X_train, "y": y_train}, training_dir / "train_data.pt")
    torch.save({"X": X_val, "y": y_val}, val_dir / "val_data.pt")
    torch.save({"X": X_test, "y": y_test}, test_dir / "test_data.pt")

    # Save complete synthetic dataset in JSON format
    dataset_records = [
        {"features": features[i], "target": targets[i]}
        for i in range(num_samples)
    ]
    with open(synthetic_dir / "synthetic_dataset.json", "w", encoding="utf-8") as f:
        json.dump(dataset_records, f, indent=2)

    metadata = {
        "dataset_type": "synthetic_student_project_compatibility",
        "description": "Synthetic dataset for training and benchmarking PyTorch MLP compatibility model.",
        "random_seed": seed,
        "feature_count": FEATURE_COUNT,
        "feature_names": FEATURE_NAMES,
        "total_samples": num_samples,
        "train_samples": len(train_idx),
        "validation_samples": len(val_idx),
        "test_samples": len(test_idx),
        "target_range": [0.0, 1.0],
        "created_at": "2026-10-02T19:30:00Z",
    }
    with open(synthetic_dir / "dataset_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    return metadata
