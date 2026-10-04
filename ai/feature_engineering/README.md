# Feature Engineering Module (`ai/feature_engineering`)

## Phase Implementation Notice
*Scheduled for implementation across **Phase 6: Skill-Gap Analysis** and **Phase 8: Feature Engineering**.*

## Planned Functionality
- **Deterministic Skill Gap Analysis (Phase 6):**
  - Set-difference computation: $G_{proj} = S_{req} \setminus S_{team}$
  - Candidate gap fill assessment: $G_{filled} = G_{proj} \cap S_{cand}$
- **Feature Fusion Pipeline (Phase 8):**
  - Synthesizes 48 continuous and categorical feature dimensions spanning skill overlap ratios, gap coverage, proficiency deficits, semantic similarity, interest Jaccard scores, and workload headroom.
  - Normalizes and verifies all inputs before feeding into the PyTorch MLP.
