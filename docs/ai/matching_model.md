# PyTorch MLP Compatibility Model (Phase 5 — Step 3)

## 1. Overview
The Compatibility Model is the core Deep Learning component of the **AI Skill Matching** system (*AI-Driven Student Skill Gap Analysis and Project Team Recommendation System Using Deep Learning*). It evaluates the quantitative fit between an individual student profile and a project requirement specification:

$$\text{Student Profile} + \text{Project Requirements} \longrightarrow \text{Feature Engineering (10 Features)} \longrightarrow \text{PyTorch MLP} \longrightarrow \text{Compatibility Score } [0.0, 1.0]$$

> [!IMPORTANT]
> The current training and evaluation results are based on synthetic development data and do not establish real-world student-project recommendation accuracy.

---

## 2. Feature Engineering Architecture
The feature engineering layer (`ai/feature_engineering/__init__.py`) translates raw relational data from the database into a deterministic, normalized 10-dimensional continuous vector:

| Index | Feature Name | Range | Description |
|:---|:---|:---|:---|
| 0 | `skill_coverage_ratio` | $[0.0, 1.0]$ | Proportion of project required skills possessed by the student. |
| 1 | `mean_proficiency_matched` | $[0.0, 1.0]$ | Average normalized proficiency of the student across matched skills. |
| 2 | `proficiency_deficit_ratio` | $[0.0, 1.0]$ | Normalized average shortfall below required proficiency across all required skills. |
| 3 | `proficiency_surplus_ratio` | $[0.0, 1.0]$ | Normalized surplus where student proficiency exceeds project requirements. |
| 4 | `unmatched_skills_count_norm` | $[0.0, 1.0]$ | Proportion of project required skills missing from the student profile. |
| 5 | `semantic_description_similarity` | $[0.0, 1.0]$ | Cosine similarity between project description and student profile Sentence Transformer embeddings. |
| 6 | `interest_domain_overlap` | $[0.0, 1.0]$ | Jaccard overlap between student interest categories and project technical domains. |
| 7 | `academic_seniority_norm` | $[0.0, 1.0]$ | Student academic year normalized from year 1 ($0.0$) to year 5 ($1.0$). |
| 8 | `prior_project_experience_norm` | $[0.0, 1.0]$ | Count of previous completed student projects, saturated at 5 projects ($1.0$). |
| 9 | `certification_count_norm` | $[0.0, 1.0]$ | Count of verified student technical certifications, saturated at 4 ($1.0$). |

---

## 3. PyTorch CompatibilityMLP Architecture
Defined in `ai/matching_model/__init__.py`:

```
Input Vector (10 Dimensions)
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
Output: Compatibility Score in [0.0, 1.0]
```

### Architectural Hyperparameters:
- **Input Dimension**: 10 features
- **Hidden Layers**: Dense Layer 1 (64 units), Dense Layer 2 (32 units)
- **Activations**: ReLU (hidden layers), Sigmoid (output layer)
- **Regularization**: Dropout ($p=0.1$) on hidden activations
- **Trainable Parameters**: 2,817 parameters
- **Execution Target**: CPU (`device="cpu"`)

---

## 4. Synthetic Training Dataset
Because real-world historical student-project match outcomes do not exist prior to production deployment, a synthetic dataset was generated locally:
- **Location**: `data/synthetic/`
- **Total Samples**: 2,000 synthetic student-project pairs
- **Reproducibility Seed**: Fixed random seed `42`
- **Splits**:
  - Training: 1,400 samples (70%) $\rightarrow$ `data/training/train_data.pt`
  - Validation: 300 samples (15%) $\rightarrow$ `data/validation/val_data.pt`
  - Test: 300 samples (15%) $\rightarrow$ `data/test/test_data.pt`
- **Database Safety**: Synthetic data is stored exclusively in local files (`data/`). Zero synthetic rows are inserted into Supabase.

---

## 5. Training Pipeline & Configuration
Implemented in `ai/training/trainer.py`:
- **Criterion**: Mean Squared Error (`nn.MSELoss`)
- **Optimizer**: Adam (`lr = 0.001`, `weight_decay = 1e-4`)
- **Batch Size**: 32
- **Epochs**: 40
- **Device**: CPU
- **Best Model Selection**: Model state dict is saved at minimum validation loss:
  - Best Epoch: 37
  - Best Validation MSE Loss: 0.001525
- **Saved Checkpoint**: `models/checkpoints/best_matching_mlp.pt`

---

## 6. Model Evaluation on Held-Out Test Set
Evaluated via `ai/evaluation/evaluator.py` on the 300 held-out test samples:

| Metric | Measured Value | Description |
|:---|:---|:---|
| **MAE** | `0.027247` | Mean Absolute Error between predicted and synthetic ground-truth score |
| **MSE** | `0.001247` | Mean Squared Error |
| **RMSE** | `0.035316` | Root Mean Squared Error |
| **$R^2$** | `0.959297` | Coefficient of determination on synthetic validation dynamics |

---

## 7. Inference Service & Protected API
### Inference Service (`ai/inference/service.py`):
- Loads the saved checkpoint from `models/checkpoints/best_matching_mlp.pt` in `eval()` mode.
- Evaluates a single student-project pair on CPU without retraining.
- Returns `CompatibilityResult` with continuous compatibility score in $[0.0, 1.0]$ and feature contributions.

### API Endpoint:
`POST /api/v1/matching/compatibility`
- **Authentication**: Requires valid Supabase JWT Bearer token.
- **Authorization**:
  - Any authenticated student can evaluate their own compatibility against any existing project.
  - A project owner can evaluate candidate students against their owned project.
  - Non-owners querying other students receive `HTTP 403 Forbidden`.
- **Response**:
```json
{
  "student_id": "c1000000-0000-0000-0000-000000000001",
  "project_id": "2d2d541b-d887-4e3b-ad87-66efe705d4a7",
  "compatibility_score": 0.8412,
  "model_version": "v1.0.0-cpu",
  "feature_contributions": {
    "skill_coverage_ratio": 1.0,
    "mean_proficiency_matched": 0.75,
    "proficiency_deficit_ratio": 0.0,
    "proficiency_surplus_ratio": 0.33,
    "unmatched_skills_count_norm": 0.0,
    "semantic_description_similarity": 0.68,
    "interest_domain_overlap": 0.5,
    "academic_seniority_norm": 0.5,
    "prior_project_experience_norm": 0.4,
    "certification_count_norm": 0.25
  }
}
```
- **Explainability**: Returns individual `feature_contributions` for downstream explainability layers.
- **No Ranking**: Does NOT return ranked lists or automatic team recommendations (reserved for Phase 5 Step 4).
