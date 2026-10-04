# Safe Local Demonstration Mode (Demo Mode)

## 1. Overview and Purpose
**Demonstration Mode (Demo Mode)** provides a strictly local, deterministic, and sandboxed dataset enabling full end-to-end evaluation of the **AI Skill Matching** platform—including candidate filtering, 10-feature vector generation, real PyTorch MLP inference, and factual explainability—even when the remote Supabase database has zero or insufficient real student/project records.

This mode allows developers, evaluators, and stakeholders to test and verify the entire user interface and machine learning pipeline without manual account seeding or polluting production databases.

---

## 2. Strict Guarantees and Architecture
- **Zero Database Mutations**: Demo Mode operates in complete isolation from the remote Supabase database. It executes zero `INSERT`, `UPDATE`, or `DELETE` SQL operations.
- **No Remote User/Project Creation**: No fake authentication accounts, user rows, or project records are ever written to Supabase.
- **Real PyTorch MLP Inference**: Recommendation scores are **not hardcoded or fabricated**. They are actively calculated by running the real trained PyTorch Multi-Layer Perceptron (`models/checkpoints/best_matching_mlp.pt`) using CPU inference over extracted 10-dimensional feature vectors.
- **Production Mode by Default**: In `app/core/config.py`, `DEMO_MODE: bool = False` by default. Production behavior and authentication checks remain strictly preserved unless explicitly toggled.
- **Explicit Synthetic Labelling**: All demo records and recommendation responses are explicitly tagged with `dataset_type: "DEMO"` and `synthetic: true`.

---

## 3. Configuration and Activation

### Backend Environment Configuration
Demo Mode can be controlled via environment variable or application configuration:
```env
# backend/.env or environment variable
DEMO_MODE=false   # Default: production mode
# Set to true for local demonstration
DEMO_MODE=true
```

In `backend/app/core/config.py`:
```python
class Settings(BaseSettings):
    ...
    DEMO_MODE: bool = False
```

### Dedicated Demo Endpoints
The backend provides dedicated endpoints under `/api/v1/demo` that allow frontend interfaces to access demo records directly:
- `GET /api/v1/demo/status`: Retrieves demo configuration and synthetic metadata.
- `GET /api/v1/demo/students`: Lists all local synthetic students.
- `GET /api/v1/demo/projects`: Lists all local synthetic projects.
- `GET /api/v1/demo/projects/{project_id}`: Retrieves details of a specific demo project.
- `GET /api/v1/demo/projects/{project_id}/recommendations`: Computes real MLP candidate recommendations for the demo project.

### Frontend Integration
On the Recommendations page (`/recommendations`), users can toggle **Demo Mode** via an interactive switch:
- When activated, a prominent amber notification banner appears:
  > **DEMO MODE — Synthetic Local Data**
  > Currently viewing local demonstration data. All student candidates and projects are synthetic records processed through the real trained PyTorch MLP compatibility model. No data is read from or written to Supabase.
- Each candidate card displays a `Demo Candidate` badge.

---

## 4. Local Dataset Location and Structure

Local demonstration datasets are stored exclusively under the repository's `data/demo/` folder:
```
data/
└── demo/
    ├── students.json
    └── projects.json
```

### Students Dataset (`data/demo/students.json`)
Contains 4 deterministic synthetic student profiles across varied skill profiles and academic departments:
- **Student A** (`00000000-de00-0000-0000-000000000001`): AI / ML Specialist (Owner of Project 1).
- **Student B** (`00000000-de00-0000-0000-000000000002`): Computer Vision & Deep Learning Engineer.
- **Student C** (`00000000-de00-0000-0000-000000000003`): Full Stack & Cloud Developer.
- **Student D** (`00000000-de00-0000-0000-000000000004`): Data Science & NLP Practitioner.

Each record includes:
- Canonical taxonomy skills with proficiency levels (1–4).
- Domain interests (`ai_ml`, `web_development`, `cloud_devops`, etc.).
- Previous project histories and technical certifications.
- Explicit metadata: `{"synthetic": true, "dataset_type": "DEMO"}`.

### Projects Dataset (`data/demo/projects.json`)
Contains 3 diverse project specifications:
1. **AI-Powered Sign Language Translator** (Computer Vision, Deep Learning, PyTorch, Python).
2. **Smart Campus Assistant** (NLP, Python, FastAPI, React, PostgreSQL).
3. **Student Expense Prediction System** (Data Science, Python, Pandas, Machine Learning, SQL).

---

## 5. Model Execution and Recommendation Flow

When recommendations are requested for a demo project:
1. **Candidate Discovery & Filtering**:
   - The project owner and any existing team members are excluded from the candidate pool.
   - Remaining synthetic students are loaded from `data/demo/students.json`.
2. **Feature Engineering**:
   - The `FeatureEngineer` calculates the 10-dimensional compatibility feature vector:
     1. Skill coverage ratio
     2. Mean proficiency of matched skills
     3. Proficiency deficit ratio
     4. Domain interest overlap
     5. Prior project experience score
     6. Certification count signal
     7. Academic year similarity
     8. Workstyle alignment
     9. Availability signal
     10. Department cross-collaboration signal
3. **PyTorch MLP Inference**:
   - The loaded checkpoint `models/checkpoints/best_matching_mlp.pt` executes forward-pass inference on CPU.
   - Generates a continuous score $\in [0.0, 1.0]$.
4. **Ranking & Filtering**:
   - Candidates are ranked in descending order of compatibility score.
   - Truncated to Top-$K$ (default: 10) and filtered by `min_score` threshold.
5. **Factual Evidence Breakdown**:
   - Generates objective explanation metrics (matched skills with levels, missing required skills, coverage ratio, proficiency alignment).

---

## 6. Official Disclaimer

> [!IMPORTANT]
> **Demo-mode recommendation results are demonstrations of the implemented pipeline and must not be presented as evidence of performance on real student data.**
