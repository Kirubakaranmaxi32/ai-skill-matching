# Inference Module (`ai/inference`)

## Phase Implementation Notice
*Scheduled for implementation across **Phase 11: Recommendation Engine** and **Phase 12: Explainability Engine**.*

## Planned Functionality
- **Predictor (Phase 11):** Loads serialized PyTorch MLP checkpoint and executes high-throughput batch scoring on student-project candidates. Applies eligibility filters (e.g. not already a member, active availability).
- **Explainer (Phase 12):** Synthesizes human-readable, data-backed justification objects detailing:
  - Exact missing skills covered by the candidate
  - Proficiency level match
  - Availability headroom
  - Shared interests and complementary domain strengths
