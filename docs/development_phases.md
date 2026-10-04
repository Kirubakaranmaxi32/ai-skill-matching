# 18-Phase Development Roadmap

### AI Skill Matching: Project Implementation Plan

---

### Phase 1: Architecture and Project Setup (CURRENT)
- **Objective:** Establish the foundational workspace, clean folder structure, frontend and backend application skeletons, basic health endpoints, environment configurations, and documentation.
- **Deliverables:** Monorepo scaffolding, FastAPI app skeleton, React Vite TypeScript skeleton, `.env.example`, `.gitignore`, root `README.md`, testing foundations.
- **Exit Criteria:** Health endpoints return HTTP 200, frontend routes load successfully, basic tests pass.

### Phase 2: Database and Authentication
- **Objective:** Design and initialize the normalized PostgreSQL database (Supabase-compatible) and Supabase Auth integration.
- **Deliverables:** DDL migrations, Supabase client integration, college email domain verification (`regex: ^[a-zA-Z0-9._%+-]+@([a-zA-Z0-9-]+\.)*college\.edu$`), JWT verification middleware, role-based authorization guards.
- **Exit Criteria:** Registration/login endpoints functional, email restrictions enforced, session tokens verified.

### Phase 3: Student Profiles and Skills
- **Objective:** Implement comprehensive student profile management and standardized skill selection.
- **Deliverables:** Profile CRUD, skill taxonomy with hierarchical categories, proficiency levels (1–4), interests, experience history, portfolio links, availability sliders.
- **Exit Criteria:** Students can manage profiles and skills with composite uniqueness constraints enforced.

### Phase 4: Project Creation and Project Feed
- **Objective:** Enable project ideation, requirement specifications, and public discovery.
- **Deliverables:** Project builder interface, required skills specification with weights and difficulty ratings, project feed with filtering by domain/category.
- **Exit Criteria:** Project creators can create/edit projects; project feed displays active recruiting projects.

### Phase 5: AI Project Analysis
- **Objective:** Integrate pretrained Sentence Transformers for natural language understanding and initial skill suggestion.
- **Deliverables:** Sentence Transformer inference module (`all-MiniLM-L6-v2`), dense project embeddings (384-D), hybrid keyword/cosine similarity skill extractor, human-in-the-loop skill confirmation UI.
- **Exit Criteria:** Submitting project text extracts relevant skills with low latency (<400ms) for creator review.

### Phase 6: Skill-Gap Analysis
- **Objective:** Implement deterministic set-theoretic gap detection between project requirements and active team rosters.
- **Deliverables:** Gap calculation engine ($G_{proj} = S_{req} \setminus S_{team}$), criticality weight assignment, missing skills visualization on project dashboard.
- **Exit Criteria:** 100% mathematical accuracy on gap identification across diverse team states validated by unit tests.

### Phase 7: Synthetic Training Dataset
- **Objective:** Create a statistically representative synthetic dataset simulating collegiate project interactions to resolve the cold-start problem.
- **Deliverables:** Reproducible data generation script producing 2,500 students, 500 projects, and 35,000 interaction samples with ground-truth target $y \in [0, 1]$, stratified 70/15/15 train/val/test splits.
- **Exit Criteria:** Data exported to Parquet/CSV with zero split leakage; metrics verified.

### Phase 8: Feature Engineering
- **Objective:** Construct the 48-dimensional fused feature extraction pipeline.
- **Deliverables:** Vectorizers for skill overlap, gap coverage, proficiency deficit, semantic similarity, interest Jaccard score, and availability headroom.
- **Exit Criteria:** Tensor assembly pipeline compiles feature vector $\mathbf{x} \in \mathbb{R}^{48}$ with boundary validation and zero NaN values.

### Phase 9: PyTorch MLP Architecture
- **Objective:** Implement the core trainable Deep Learning model for compatibility prediction.
- **Deliverables:** PyTorch `SkillMatchingMLP` module (48 $\to$ 128 $\to$ 64 $\to$ 32 $\to$ 1), custom Huber/MSE loss, model configuration and checkpoint serialization utilities.
- **Exit Criteria:** Forward pass verifies tensor output shape `(N, 1)` strictly bounded within $[0.0, 1.0]$.

### Phase 10: Model Training and Evaluation
- **Objective:** Train the PyTorch MLP on the synthetic training split and benchmark against unseen test data.
- **Deliverables:** Training loop with AdamW, learning rate scheduling, early stopping, evaluation scripts reporting MAE, MSE, RMSE, $R^2$, and NDCG@K.
- **Exit Criteria:** Model converges cleanly without overfitting; test metrics systematically recorded in model card.

### Phase 11: Recommendation Engine
- **Objective:** Build the candidate ranking and filtering layer.
- **Deliverables:** Top-$K$ candidate search for projects, project recommendation for students, exclusion of already joined members and overloaded students.
- **Exit Criteria:** Recommendation queries execute in $<150$ ms returning ranked candidate lists.

### Phase 12: Explainability Engine
- **Objective:** Generate transparent, data-backed natural language explanations for every recommendation.
- **Deliverables:** Explanation synthesis algorithm decomposing input feature contributions, specific missing skills covered, and availability alignment.
- **Exit Criteria:** Recommendations include structured explanation objects grounded exclusively in real stored data.

### Phase 13: Student Matching and Team Formation
- **Objective:** Implement bilateral invitation management and voluntary team assembly.
- **Deliverables:** Invitation lifecycle (Send, Accept, Decline, Expire), notifications, team roster updates upon acceptance.
- **Exit Criteria:** Teams are formed exclusively via bilateral consent; no automatic or forced team assignments.

### Phase 14: Progress and Feedback
- **Objective:** Support project tracking and collect user feedback on recommendation quality.
- **Deliverables:** Milestone task management (Kanban/Checklist), recommendation rating ingestion (1–5 stars, accuracy flags).
- **Exit Criteria:** Feedback persisted in `recommendation_feedback` table for offline analysis and continuous improvement.

### Phase 15: Admin Dashboard
- **Objective:** Provide administrative oversight, taxonomy curation, and model performance monitoring.
- **Deliverables:** Admin metrics view (active projects, team completion rates), skill taxonomy editor, model evaluation audit trails.
- **Exit Criteria:** Administrators can manage platform settings and inspect system metrics securely.

### Phase 16: Security Audit
- **Objective:** Harden the platform against common vulnerabilities and enforce strict data protection.
- **Deliverables:** Input sanitization check, SQL injection and XSS defenses, rate-limiting rules, CORS lockdown, secrets verification.
- **Exit Criteria:** Clean OWASP Top 10 compliance audit; zero secrets in codebase.

### Phase 17: Comprehensive Testing
- **Objective:** Establish end-to-end quality assurance across all layers.
- **Deliverables:** Pytest unit and integration test suites (>80% coverage on core services), frontend Vitest component tests, directional DL invariance tests.
- **Exit Criteria:** All automated test suites execute and pass cleanly.

### Phase 18: Deployment and Documentation
- **Objective:** Package the application for production deployment with complete technical documentation.
- **Deliverables:** Multi-stage Dockerfiles, Docker Compose orchestrations, comprehensive API documentation (`openapi.json`), final user and developer manuals.
- **Exit Criteria:** Clean single-command deployment via Docker Compose.
