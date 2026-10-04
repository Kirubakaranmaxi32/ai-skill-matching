# Data Directory (`data/`)

## Purpose & Organization
This directory organizes data assets across raw taxonomies, processed skill vocabularies, and synthetic interaction splits.

```
data/
├── raw/            # Raw skill catalogs, ACM/IEEE curricula, industry taxonomies
├── processed/      # Cleaned and canonicalized skill databases
├── synthetic/      # Generated interaction dataset (Parquet / CSV)
├── training/       # 70% Training split for PyTorch MLP
├── validation/     # 15% Validation split for model checkpointing & early stopping
└── test/           # 15% Unseen Test split for unbiased benchmark evaluation
```

## Important Development Note
- **Synthetic Data Generation is scheduled for Phase 7.**
- In Phase 1, only the directory structure and gitkeep placeholders are established.
- No synthetic datasets or fake metrics are generated in this phase.
