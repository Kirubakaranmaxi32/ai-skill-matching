# Skill Extraction Module (`ai/skill_extraction`)

## Phase Implementation Notice
*Scheduled for implementation in **Phase 5: AI Project Analysis**.*

## Planned Functionality
- **Candidate Skill Detection:** Employs hybrid extraction (regular expressions, domain keywords, and cosine similarity against the canonical skill taxonomy) to extract technical and non-technical skill mentions from project descriptions.
- **Normalization:** Maps colloquial skill names to standard database skill entities (e.g., "React.js", "ReactJS" $\to$ "React").
- **Human-in-the-Loop:** Suggestions are delivered to the frontend for explicit creator confirmation and weight adjustments before persistence.
