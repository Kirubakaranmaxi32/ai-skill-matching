# Scripts Directory (`scripts/`)

## Purpose
This directory will contain administrative, data-generation, training, and benchmarking CLI scripts.

## Planned Scripts
- **`seed_taxonomy.py` (Phase 3):** Populates the PostgreSQL database with canonical academic and technical skills, proficiency descriptions, and category hierarchies.
- **`generate_synthetic_data.py` (Phase 7):** Executes the synthetic generation pipeline to produce representative student profiles, project requirements, and calibrated compatibility ground-truth values.
- **`train_model.py` (Phase 10):** Command-line entry point to train the PyTorch `SkillMatchingMLP` on GPU/CPU with configurable hyperparameters, logging, and checkpointing.
- **`evaluate_model.py` (Phase 10):** Evaluates trained checkpoints on held-out test splits, generating empirical regression (MAE, RMSE, $R^2$) and ranking (Precision@K, NDCG@K) metrics.

## Development Status
Scripts will be implemented incrementally within their respective designated phases.
