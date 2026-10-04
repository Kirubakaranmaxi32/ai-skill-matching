# Matching Model Module (`ai/matching_model`)

## Phase Implementation Notice
*Scheduled for implementation in **Phase 9: PyTorch MLP Architecture**.*

## Planned Functionality
- **Deep Learning MLP Definition:** Implements `SkillMatchingMLP` as a PyTorch `nn.Module`.
  - Input: $\mathbf{x} \in \mathbb{R}^{48}$
  - Hidden Layers: 128 $\to$ 64 $\to$ 32 with Batch Normalization, ReLU activations, and Dropout regularization (0.20, 0.15).
  - Output Head: 1 unit with Sigmoid activation outputting continuous compatibility score $\hat{y} \in [0.0, 1.0]$.
- **Checkpoint Serialization:** Handles saving and loading model weights (`.pt` files) with architecture metadata.
