# Models Directory (`models/`)

## Purpose & Organization
This directory holds serialized deep learning model weights, training checkpoints, and benchmark metadata.

```
models/
├── checkpoints/    # Serialized PyTorch state dicts (.pt / .pth)
└── metadata/       # Model hyperparameters, training logs, evaluation metrics JSON
```

## Important Development Note
- **Model Checkpointing is scheduled for Phase 9 & Phase 10.**
- In Phase 1, only the directory structure and gitkeep placeholders are established.
- No dummy weights or fabricated metrics are stored here.
