# AI Skill Matching

### *AI-Driven Student Skill Gap Analysis and Project Team Recommendation System Using Deep Learning*

> **"Find the right skills. Build the right team."**

---

## 1. Project Overview

**AI Skill Matching** is an intelligent, explainable web application designed for university students, educators, and project leads. The platform solves the challenge of student team formation by combining deterministic skill-gap analysis with a trained **PyTorch Multi-Layer Perceptron (MLP)** neural network.

The platform analyzes project technical requirements, identifies unfulfilled team skills, calculates mathematical skill gaps, and evaluates candidate students across multi-dimensional compatibility vectors to provide rank-ordered, explainable recommendations. Team formation remains strictly voluntary through a bilateral invitation and acceptance workflow.

---

## 2. Problem Statement

In academic and collegiate engineering settings, collaborative project teams frequently encounter:
* **Ad-hoc Team Formation:** Teams formed primarily through friendship networks rather than complementary technical skill sets, leading to severe skill deficits during development.
* **Opaque Skill Deficits:** Project leads often struggle to define and quantify exactly which technical competencies are lacking from their prospective teams.
* **Black-Box Matching:** Traditional algorithmic matchers often provide arbitrary similarity scores without explainable justification, eroding student trust in automated suggestions.
* **Involuntary Assignment Friction:** Automated group assignment tools impose teams on students, decreasing motivation and accountability.

---

## 3. Project Objectives

1. **Deterministic Skill-Gap Analysis:** Compute exact mathematical set differences ($S_{required} \setminus S_{team}$) and proficiency deficits between project requirements and student capabilities.
2. **Trainable Neural Compatibility:** Train and evaluate a dedicated PyTorch Multi-Layer Perceptron (MLP) on fused student-project feature tensors rather than relying solely on surface-level cosine similarity.
3. **Semantic Text Representation:** Leverage pretrained Sentence Transformers (`all-MiniLM-L6-v2`) to derive 384-dimensional dense semantic embeddings from project descriptions.
4. **Factual Explainability:** Accompany every compatibility recommendation with transparent metrics (skill coverage, proficiency alignment, interest overlap, experience signal, and exact matched/missing skills).
5. **Voluntary Collaboration:** Enforce bilateral consent (Invite $\rightarrow$ Accept/Decline) so teams assemble voluntarily.
6. **Full Project Lifecycle:** Support milestones, progress tracking (percentages, milestone statuses), task management (`todo`, `in_progress`, `completed`), and collaboration feedback ratings.
7. **Administrative Oversight:** Provide authorized administrators with a data-driven monitoring console to audit user demographics, skills distribution, project health, AI model readiness, and system operations.

---

## 4. Key Implemented Features

* **Student Profile Management:** Student bios, university departments, academic year (1â€“5), contact information, GitHub profiles, and portfolio URLs.
* **Technical Skills & Proficiency:** Categorized skill taxonomy with student-declared proficiency levels (Level 1: Beginner, Level 2: Intermediate, Level 3: Advanced, Level 4: Expert).
* **Interests & Academic History:** Academic research interests, previous project portfolios, and verified certifications.
* **Project Creation & Specification:** Project titles, descriptions, recruitment lifecycle status (`open`, `in_progress`, `completed`, `archived`), and required skills with minimum target proficiencies.
* **AI Project Text Analysis:** Automatic extraction of candidate technical skills and semantic representation using pretrained Sentence Transformers.
* **Mathematical Skill-Gap Analysis:** Instant breakdown of matched skills, partial skill deficits, and missing requirements with overall coverage percentage.
* **Candidate Discovery & Eligibility Filtering:** Automatic exclusion of project owners and active team members from candidate recommendation pools.
* **PyTorch Compatibility Scoring:** Real-time neural inference generating continuous compatibility scores ($0.0 \le \hat{y} \le 1.0$) using the trained MLP checkpoint.
* **Explainable Recommendations:** Detailed candidate cards displaying rank, match score, skill coverage ratio, proficiency alignment, interest overlap, and specific skill matches/gaps.
* **Voluntary Team Invitations:** Project owners send invitations; prospective members review, accept, or decline from a dedicated Invitations hub.
* **Project Progress & Task Tracking:** Progress percentage tracking, status badges (`not_started`, `in_progress`, `completed`, `blocked`), task CRUD with assignee, priority (`low`, `medium`, `high`), and status.
* **Collaboration Feedback:** 1â€“5 star rating submissions and qualitative feedback entries upon project collaboration.
* **Admin Intelligence Dashboard:** Server-authorized 6-tab monitoring dashboard (Overview, Students & Skills, Projects & Teams, Progress & Tasks, AI Matching & Feedback, System Health).
* **Demonstration Mode:** Isolated local dataset mode with pre-seeded synthetic students and projects for evaluation without mutating production database tables.

---

## 5. System Architecture

The application adopts a decoupled three-tier architecture:

```
[ User Browser / Client ]
           â”‚
           â–¼
[ Frontend: React 18 + Vite + TypeScript + Tailwind CSS ]  (Hosted on Vercel)
           â”‚
           â”‚ HTTP REST Requests + Supabase JWT Bearer Tokens
           â–¼
[ Backend: FastAPI (Python 3.11+) + Uvicorn ]               (Hosted on Render)
   â”œâ”€â”€ Core Auth & JWT Verification
   â”œâ”€â”€ API v1 Routers (Students, Projects, Matching, Invitations, Progress, Admin)
   â”œâ”€â”€ Domain Services (Skill Gap, Invitations, Progress, Admin Analytics)
   â”œâ”€â”€ AI Recommendation Engine & Feature Engineer
   â”‚    â”œâ”€â”€ Pretrained Sentence Transformer (all-MiniLM-L6-v2)
   â”‚    â””â”€â”€ PyTorch CompatibilityMLP (models/checkpoints/best_matching_mlp.pt)
   â””â”€â”€ Database Adapter
           â”‚
           â–¼
[ Data Tier: Supabase ]
   â”œâ”€â”€ PostgreSQL Database (Tables with Row Level Security enabled)
   â”œâ”€â”€ Supabase Auth (Cryptographic HS256 JWT Token Issuance)
   â””â”€â”€ Supabase Storage (Portfolio & Profile Asset Buckets)
```

---

## 6. Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | React 18, TypeScript 5.5, Vite 5.4, Tailwind CSS 3.4, Lucide React icons, React Router DOM v6, Axios, Supabase Client (`@supabase/supabase-js`) |
| **Backend** | Python 3.11+ / 3.13, FastAPI, Pydantic v2, Pydantic Settings, Uvicorn, PyJWT (HS256 cryptographic verification), HTTPX |
| **Database & Auth** | Supabase PostgreSQL, PostgreSQL Row Level Security (RLS), Supabase Auth |
| **Machine Learning** | PyTorch (CPU inference), Sentence Transformers (`sentence-transformers/all-MiniLM-L6-v2`), Hugging Face Hub, scikit-learn, SciPy, NumPy |
| **Testing** | Pytest, pytest-asyncio, Vitest, React Testing Library, JSDOM |
| **Deployment** | Vercel (Frontend SPA), Render (FastAPI Web Service), Supabase (Managed Cloud PostgreSQL & Auth) |

---

## 7. AI & Deep Learning Architecture

The AI subsystem consists of two distinct components:

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                        AI Matching Subsystem                           â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚                                                                        â”‚
â”‚   Project Description                                                  â”‚
â”‚          â”‚                                                             â”‚
â”‚          â–¼                                                             â”‚
â”‚  [ Pretrained NLP Model ]  â”€â”€â”€â–º 384-dimensional dense semantic vector  â”‚
â”‚  (Sentence Transformer:                                                â”‚
â”‚   all-MiniLM-L6-v2)                                                    â”‚
â”‚                                                                        â”‚
â”‚   Project Required Skills â”€â”€â”                                          â”‚
â”‚                             â”œâ”€â–º [ Feature Engineer ] â”€â”€â–º 10-D Feature   â”‚
â”‚   Candidate Profile Data  â”€â”€â”˜                            Vector        â”‚
â”‚                                                            â”‚           â”‚
â”‚                                                            â–¼           â”‚
â”‚                                                 [ Trained PyTorch MLP] â”‚
â”‚                                                 (CompatibilityMLP:     â”‚
â”‚                                                  10 -> 64 -> 32 -> 1)  â”‚
â”‚                                                            â”‚           â”‚
â”‚                                                            â–¼           â”‚
â”‚                                                    Compatibility Score â”‚
â”‚                                                    (0.00 to 1.00)      â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

### 1. Pretrained Text Representation (Sentence Transformers)
* **Model:** `sentence-transformers/all-MiniLM-L6-v2`
* **Role:** Pretrained NLP model used to map unstructured project descriptions into dense 384-dimensional semantic embeddings. It is also used to compare project conceptual similarity and extract taxonomy-aligned skill tokens.
* **Execution:** Loaded onto CPU at runtime via Hugging Face Hub.

### 2. Trainable Compatibility Model (PyTorch CompatibilityMLP)
* **Architecture:** Fully connected neural network:
  * Input Layer: `10` continuous engineered feature dimensions
  * Hidden Layer 1: `64` units with ReLU activation and Dropout ($p=0.1$)
  * Hidden Layer 2: `32` units with ReLU activation and Dropout ($p=0.1$)
  * Output Layer: `1` unit with Sigmoid activation ($0.0 \le \hat{y} \le 1.0$)
  * Total Trainable Parameters: **2,817**
* **Active Checkpoint File:** [`models/checkpoints/best_matching_mlp.pt`](file:///c:/Users/kirubakaran/Desktop/AI%20skill%20matching/models/checkpoints/best_matching_mlp.pt)
* **Verification Evidence:** The checkpoint file exists in the repository, containing verified serialized state dictionaries and model configuration (`input_dim: 10`, `hidden_dims: [64, 32]`, `total_trainable_parameters: 2817`).
* **Input Feature Dimensions (10 Features):**
  1. `skill_coverage_ratio`: Fraction of required project skills possessed by the student.
  2. `avg_proficiency_match`: Mean alignment between student proficiency and target level.
  3. `max_proficiency_deficit`: Greatest single skill deficit for required skills.
  4. `interest_overlap_score`: Binary/normalized overlap between student interests and project domain.
  5. `academic_year_factor`: Normalized academic maturity factor ($year / 5.0$).
  6. `experience_signal`: Scaled count of completed previous projects and certifications.
  7. `project_embedding_similarity`: Cosine similarity between student background text and project description embedding.
  8. `unmatched_skills_ratio`: Ratio of required skills completely absent from candidate profile.
  9. `category_diversity_factor`: Breadth of candidate skills across distinct taxonomy domains.
  10. `profile_completeness_factor`: Completeness score of candidate profile information.

> [!NOTE]
> The checkpoint [`models/checkpoints/best_matching_mlp.pt`](file:///c:/Users/kirubakaran/Desktop/AI%20skill%20matching/models/checkpoints/best_matching_mlp.pt) was trained using the synthetic dataset pipeline in `ai/training/` (`train_data.pt`, `val_data.pt`). Synthetic training was utilized to train non-linear compatibility surfaces without exposing private student evaluation records. No claims of real-world human accuracy benchmarks are made.

---

## 8. Core Workflows

### Student Workflow
```
Register / Login
  â†“
Set up Student Profile (Bio, Department, Year, Portfolio)
  â†“
Add Technical Skills & Specify Proficiency Levels (1 to 4)
  â†“
Add Research Interests & Previous Projects / Certifications
  â†“
Explore Projects Feed (Browse Open Projects across University)
  â†“
Inspect Project Details & Required Technical Competencies
  â†“
Inspect Self Skill-Gap Analysis against Project Requirements
  â†“
Receive Invitation from Project Owner (or decline)
  â†“
Accept Invitation (Voluntarily joins project as Team Member)
  â†“
View Project Tasks & Progress Milestone Status
  â†“
Update Assigned Tasks (Todo â†’ In Progress â†’ Completed)
  â†“
Submit Collaboration Feedback Rating (1â€“5 Stars)
```

### Project Owner Workflow
```
Create Project Specification (Title & Detailed Description)
  â†“
Define Required Technical Skills & Target Proficiency Levels
  â†“
Run AI Project Analysis (Extracts candidate skills & text embeddings)
  â†“
View AI Recommended Candidates (PyTorch MLP compatibility scores)
  â†“
Inspect Candidate Explainability & Candidate Skill-Gap Breakdowns
  â†“
Send Team Invitation to Selected Candidate
  â†“
Monitor Accepted Team Members in Team Roster
  â†“
Create & Assign Project Tasks to Members
  â†“
Update Project Milestone Progress Percentage
  â†“
Review Collaboration Feedback from Team Members
```

### Administrator Workflow
```
Admin Login (Supabase Auth)
  â†“
Access /admin Route
  â†“
Server-Side Verification (backend/app/core/auth.py via public.admin_users)
  â†“
Tab 1: Platform Overview (Total students, projects, members, invitations, avg rating)
Tab 2: Students & Skills (Department distributions, skill proficiencies, project demand)
Tab 3: Projects & Teams (Status breakdowns, team sizes, invitation acceptance rates)
Tab 4: Progress & Tasks (Average progress %, task statuses, priority distributions)
Tab 5: AI Matching & Feedback (MLP checkpoint status, Sentence Transformer health, ratings)
Tab 6: System Health (Backend health, Supabase connectivity, runtime mode)
```

---

## 9. Security & Authorization

* **Server-Side Authorization:** Admin access is enforced strictly server-side by the [`get_current_admin`](file:///c:/Users/kirubakaran/Desktop/AI%20skill%20matching/backend/app/core/auth.py#L99-L136) FastAPI dependency, which performs database lookups in `public.admin_users` and checks cryptographically verified `app_metadata.role` claims.
* **Client-Editable Metadata Excluded:** Client-editable `user_metadata` is completely excluded from authorization decisions, preventing privilege escalation.
* **Secret Isolation:** `SUPABASE_SERVICE_ROLE_KEY` and `SUPABASE_JWT_SECRET` reside strictly on the backend and are never bundled into frontend assets.
* **Row-Level Security (RLS):** All Supabase tables (`students`, `student_skills`, `projects`, `project_skills`, `project_members`, `invitations`, `project_progress`, `project_tasks`, `recommendation_feedback`, `admin_users`) enforce RLS policies restricting unauthorized mutation.
* **Non-Destructive Actions:** Soft archiving is used instead of permanent row deletion for projects.

---

## 10. Demonstration Mode

For local evaluation, demonstrations, and offline testing without live Supabase database requirements, the platform includes a built-in **Demonstration Mode**:
* Toggleable via `DEMO_MODE=True` in `backend/.env`.
* Backed by an in-memory data store (`_in_memory_db`) pre-populated with synthetic student candidates and projects.
* Clearly flagged in both the frontend and backend with `DEMO MODE â€” Synthetic Local Data` notices.
* Completely isolated; zero demo records are written to live Supabase tables.

---

## 11. Verification & Testing Status

Every phase of the project is verified through automated tests:

### Backend Automated Test Suite: 115 / 115 Passed (100%)
* `test_health.py`: Root `/health` and API v1 health verification.
* `test_auth.py`: Token validation, expiration handling, unauthenticated 401 checks.
* `test_students_api.py`: Profile CRUD, skill taxonomy, proficiency levels, ownership guards.
* `test_projects_api.py`: Project lifecycle, required skills, member roster.
* `test_project_analysis.py`: Sentence Transformer embeddings, token preservation, taxonomy matching.
* `test_matching_mlp.py`: Feature engineering ranges, PyTorch MLP forward pass, compatibility endpoints.
* `test_recommendation_engine.py`: Candidate discovery, Top-K ranking, threshold filtering, explainability.
* `test_skill_gap.py`: Deterministic set difference, partial deficits, ownership access controls.
* `test_invitations.py`: Sent/received invitation lifecycle, duplicate prevention, team roster updates.
* `test_progress_feedback.py`: Milestone progress tracking, task CRUD, feedback submission.
* `test_admin_dashboard.py`: Server-side admin authorization, 403 rejection of students, analytics aggregation.
* `test_demo_mode.py`: Synthetic dataset loading and in-memory isolation.

### Frontend Automated Test Suite: 43 / 43 Passed (100%)
* `ProfilePage.test.tsx`: Route protection, profile editing, skill addition.
* `Projects.test.tsx`: Project list rendering, empty states, creation forms.
* `Recommendations.test.tsx`: Recommendation card rendering, compatibility scores, invitation triggers.
* `SkillGap.test.tsx`: Skill-gap drilldown views, matched/missing skill badges.
* `Invitations.test.tsx`: Received/sent tabs, invitation acceptance/rejection flows.
* `ProgressFeedback.test.tsx`: Milestone progress bars, task list filters, feedback forms.
* `AdminDashboard.test.tsx`: AdminRoute guard, 403 Access Denied UI, 6-tab analytics rendering.

### Build Verification
* **TypeScript Compilation:** `PASS` (`tsc --noEmit` reports 0 errors).
* **Vite Production Bundler:** `PASS` (`npm run build` generates production assets in `dist/`).

---

## 12. Completed Phases Summary

| Phase | Description | Status |
| :---: | :--- | :---: |
| **01** | Architecture & Monorepo Setup (FastAPI & Vite skeletons) | **Completed** |
| **02** | Supabase Database & Authentication (JWT validation, RLS) | **Completed** |
| **03** | Student Profiles, Skills Taxonomy & Proficiencies | **Completed** |
| **04** | Project Management, Descriptions & Required Skills | **Completed** |
| **05** | AI Project Text Analysis (Sentence Transformers NLP) | **Completed** |
| **06** | Mathematical Skill-Gap Analysis Engine | **Completed** |
| **07** | Synthetic Compatibility Dataset Generation | **Completed** |
| **08** | Multi-Dimensional Feature Engineering (10 Features) | **Completed** |
| **09** | PyTorch CompatibilityMLP Neural Network Architecture | **Completed** |
| **10** | Model Training, Evaluation & Checkpointing | **Completed** |
| **11** | Candidate Recommendation & Top-K Ranking Engine | **Completed** |
| **12** | Factual Explainability & Attribution Signals | **Completed** |
| **13** | Voluntary Team Formation & Bilateral Invitations | **Completed** |
| **14** | Project Progress Tracking, Tasks & Collaboration Feedback | **Completed** |
| **15** | Admin Intelligence Dashboard & Server Authorization | **Completed** |
| **16** | Production Readiness, SPA Routing & Deployment Setup | **Completed** |

---

## 13. Remaining Work & Future Roadmap

* **Historical Recommendation Tracking:** Persistent logging of past match recommendation sessions for longitudinal longitudinal satisfaction analysis (currently highlighted as planned in Admin UI).
* **Multi-Project Team Optimization:** Algorithmic optimization for global student allocation across multiple competing project proposals simultaneously.
* **Real-time Notifications:** Webhook or WebSocket push notifications when a student receives or accepts an invitation.

---

## 14. Repository Structure

```
AI skill matching/
â”œâ”€â”€ ai/                                    # AI & Deep Learning Core Subsystem
â”‚   â”œâ”€â”€ embeddings/                        # Sentence Transformer text embeddings
â”‚   â”œâ”€â”€ features/                          # 10-D compatibility feature engineering
â”‚   â”œâ”€â”€ matching_model/                    # PyTorch CompatibilityMLP definition
â”‚   â”œâ”€â”€ recommendation/                    # Recommendation engine & factual explanations
â”‚   â””â”€â”€ training/                          # Synthetic dataset generator & training loop
â”œâ”€â”€ backend/                               # FastAPI Application
â”‚   â”œâ”€â”€ app/
â”‚   â”‚   â”œâ”€â”€ api/v1/                        # REST API routes (students, projects, admin, etc.)
â”‚   â”‚   â”œâ”€â”€ core/                          # Config, Supabase clients, auth dependencies
â”‚   â”‚   â”œâ”€â”€ schemas/                       # Pydantic request/response schemas
â”‚   â”‚   â”œâ”€â”€ services/                      # Domain services (skill gap, invitations, admin)
â”‚   â”‚   â””â”€â”€ main.py                        # FastAPI application entry point
â”‚   â”œâ”€â”€ tests/                             # Pytest automated test suite (115 tests)
â”‚   â”œâ”€â”€ Dockerfile                         # Backend containerization file
â”‚   â””â”€â”€ requirements.txt                   # Production Python dependencies
â”œâ”€â”€ frontend/                              # React + Vite Frontend Application
â”‚   â”œâ”€â”€ src/
â”‚   â”‚   â”œâ”€â”€ components/                    # Route guards, SkillGapView, ProgressFeedback
â”‚   â”‚   â”œâ”€â”€ context/                       # Supabase AuthContext provider
â”‚   â”‚   â”œâ”€â”€ layouts/                       # Root navigation layout and footer
â”‚   â”‚   â”œâ”€â”€ pages/                         # Dashboard, Profile, Projects, Invitations, Admin
â”‚   â”‚   â”œâ”€â”€ services/                      # API client, Supabase client, Admin client
â”‚   â”‚   â”œâ”€â”€ types/                         # TypeScript interfaces and response types
â”‚   â”‚   â””â”€â”€ tests/                         # Vitest frontend test suite (43 tests)
â”‚   â”œâ”€â”€ vercel.json                        # Vercel SPA client-side rewrite configuration
â”‚   â””â”€â”€ package.json                       # Frontend dependencies and build scripts
â”œâ”€â”€ data/                                  # Synthetic datasets (train, val, test)
â”œâ”€â”€ docs/                                  # Documentation & SQL Database Migrations
â”‚   â””â”€â”€ database/                          # Phase migrations (schema, tables, RLS policies)
â”œâ”€â”€ models/                                # Model Storage
â”‚   â””â”€â”€ checkpoints/
â”‚       â””â”€â”€ best_matching_mlp.pt           # Active trained PyTorch MLP checkpoint
â”œâ”€â”€ .env.example                           # Root environment variable template
â”œâ”€â”€ .gitignore                             # Git ignore rules (secrets untracked, model whitelisted)
â””â”€â”€ README.md                              # Project documentation
```

---

## 15. Local Setup & Execution Guide

### Prerequisites
* **Node.js:** v18+ or v20+ with `npm`
* **Python:** v3.11+ or v3.13
* **Supabase Account / Project:** PostgreSQL database and Auth credentials

### 1. Clone & Environment Configuration

```bash
# Clone the repository
git clone https://github.com/<your-username>/ai-skill-matching.git
cd ai-skill-matching

# Copy example environment configuration
cp .env.example backend/.env
cp frontend/.env.example frontend/.env
```

Edit `backend/.env` and `frontend/.env` with your Supabase credentials (see section 16).

### 2. Backend Setup & Startup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\activate
# macOS/Linux:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start FastAPI development server
uvicorn app.main:app --reload --port 8000
```

* **Swagger UI:** `http://localhost:8000/docs`
* **Health Check:** `http://localhost:8000/health`

### 3. Frontend Setup & Startup

Open a second terminal window:

```bash
cd frontend

# Install Node dependencies
npm install

# Start Vite dev server
npm run dev
```

* **Frontend UI:** `http://localhost:5173`

---

## 16. Environment Variables Reference

> [!WARNING]
> Never commit `.env` files, service-role keys, or JWT secrets to Git. Only `.env.example` templates with placeholder values should be committed.

### Backend (`backend/.env`)

| Variable | Description | Example (Development) |
| :--- | :--- | :--- |
| `ENVIRONMENT` | Runtime environment mode | `development` or `production` |
| `DEBUG` | FastAPI debug flag (set False in prod) | `True` |
| `API_V1_STR` | Versioned API route prefix | `/api/v1` |
| `SECRET_KEY` | Backend application secret key | `change-me-to-a-secure-secret-key` |
| `FRONTEND_URL` | Primary frontend web address | `http://localhost:5173` |
| `BACKEND_URL` | Backend server base address | `http://localhost:8000` |
| `ALLOWED_ORIGINS` | Comma-separated CORS allowed domains | `http://localhost:5173,http://127.0.0.1:5173` |
| `SUPABASE_URL` | Supabase project API endpoint URL | `https://your-project.supabase.co` |
| `SUPABASE_ANON_KEY` | Supabase public anonymous API key | `sb_publishable_...` |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase private administrative key (backend only) | `sb_secret_...` |
| `SUPABASE_JWT_SECRET` | Supabase JWT signing secret for verification | `your-supabase-jwt-secret` |
| `SENTENCE_TRANSFORMER_MODEL` | Hugging Face NLP embedding model identifier | `sentence-transformers/all-MiniLM-L6-v2` |
| `DEMO_MODE` | Toggle local synthetic data isolation | `False` |

### Frontend (`frontend/.env`)

| Variable | Description | Example (Development) |
| :--- | :--- | :--- |
| `VITE_API_BASE_URL` | Base endpoint for backend API v1 | `http://localhost:8000/api/v1` |
| `VITE_BACKEND_URL` | Base endpoint for backend root | `http://localhost:8000` |
| `VITE_APP_NAME` | Application display title | `AI Skill Matching` |
| `VITE_APP_TAGLINE` | Application tagline | `Find the right skills. Build the right team.` |
| `VITE_SUPABASE_URL` | Supabase project API endpoint URL | `https://your-project.supabase.co` |
| `VITE_SUPABASE_ANON_KEY` | Supabase public anonymous API key | `sb_publishable_...` |

---

## 17. Production Deployment Architecture

The system is configured for cloud deployment across the following stack:

```
                  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                  â”‚          Vercel Cloud Hosting          â”‚
                  â”‚   React 18 + Vite (SPA Rewrites)       â”‚
                  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                                     â”‚ HTTPS
                                     â–¼
                  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                  â”‚          Render Cloud Hosting          â”‚
                  â”‚   FastAPI + Uvicorn + PyTorch (CPU)    â”‚
                  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                                     â”‚ HTTPS / WSS
                                     â–¼
                  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                  â”‚           Supabase Cloud               â”‚
                  â”‚   PostgreSQL + Auth + Storage          â”‚
                  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

1. **Frontend on Vercel:**
   * Root Directory: `frontend`
   * Framework Preset: `Vite`
   * Build Command: `npm run build`
   * Output Directory: `dist`
   * SPA client-side routing rewrites handled via [`frontend/vercel.json`](file:///c:/Users/kirubakaran/Desktop/AI%20skill%20matching/frontend/vercel.json).
2. **Backend on Render:**
   * Root Directory: `.` *(Repository root so `ai/` and `models/` checkpoints remain accessible)*
   * Runtime: `Python 3`
   * Build Command: `pip install -r backend/requirements.txt`
   * Start Command: `uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port $PORT`
   * Health Check: `/health`
3. **Database on Supabase:**
   * PostgreSQL database tables with Row Level Security enabled.
   * `public.admin_users` table for server-side administrator authorization.

---

## 18. Verified REST API Endpoints

### System & Health
* `GET /health` â€” Root health check (`{"status": "healthy"}`)
* `GET /api/v1/health` â€” Versioned v1 health status

### Authentication & Student Profile
* `GET /api/v1/auth/me` â€” Authenticated user claims verification
* `GET /api/v1/students/me` â€” Current student profile
* `PUT /api/v1/students/me` â€” Update student bio, department, and social links
* `GET /api/v1/students/me/skills` â€” List declared student skills
* `POST /api/v1/students/me/skills` â€” Add skill with proficiency level (1â€“4)
* `DELETE /api/v1/students/me/skills/{skill_id}` â€” Remove student skill
* `GET /api/v1/students/me/interests` â€” List student interests
* `POST /api/v1/students/me/interests` â€” Add research interest
* `DELETE /api/v1/students/me/interests/{interest_id}` â€” Remove interest
* `GET /api/v1/students/me/certifications` â€” List verified student certifications
* `POST /api/v1/students/me/certifications` â€” Add certification
* `DELETE /api/v1/students/me/certifications/{cert_id}` â€” Remove certification
* `GET /api/v1/students/me/projects` â€” List previous portfolio projects
* `POST /api/v1/students/me/projects` â€” Add previous project
* `DELETE /api/v1/students/me/projects/{project_id}` â€” Remove previous project

### Projects & Technical Requirements
* `POST /api/v1/projects` â€” Create new project
* `GET /api/v1/projects` â€” List discoverable, joined, or created projects (`?scope=discover|joined|me`)
* `GET /api/v1/projects/me` â€” List projects owned by authenticated student
* `GET /api/v1/projects/{project_id}` â€” Retrieve project details, skills, and members
* `PUT /api/v1/projects/{project_id}` â€” Update title, description, or status (Owner only)
* `POST /api/v1/projects/{project_id}/archive` â€” Soft archive project (Owner only)
* `POST /api/v1/projects/{project_id}/skills` â€” Add required skill with target proficiency
* `GET /api/v1/projects/{project_id}/skills` â€” List project required skills
* `DELETE /api/v1/projects/{project_id}/skills/{skill_id}` â€” Remove required skill

### AI Matching, Skill Gap & Recommendations
* `POST /api/v1/projects/{project_id}/analyze` â€” AI semantic analysis & candidate skill extraction
* `GET /api/v1/projects/{project_id}/skill-gap` â€” Compute deterministic skill-gap against candidate
* `GET /api/v1/projects/{project_id}/recommendations` â€” Top-K candidate recommendations via PyTorch MLP

### Invitations & Voluntary Team Formation
* `POST /api/v1/projects/{project_id}/invitations` â€” Send team invitation to student (Owner only)
* `GET /api/v1/projects/{project_id}/invitations` â€” List invitations for a project (Owner only)
* `GET /api/v1/invitations/me` â€” List current user invitations (`?type=received|sent&status=...`)
* `POST /api/v1/invitations/{invitation_id}/accept` â€” Accept invitation (joins project team)
* `POST /api/v1/invitations/{invitation_id}/reject` â€” Decline invitation
* `POST /api/v1/invitations/{invitation_id}/cancel` â€” Cancel sent invitation (Owner only)

### Progress Tracking & Collaboration Feedback
* `GET /api/v1/projects/{project_id}/progress/overview` â€” Project completion percentage and tasks
* `POST /api/v1/projects/{project_id}/progress` â€” Update milestone progress entry (Owner only)
* `POST /api/v1/projects/{project_id}/tasks` â€” Create project task (Owner or member)
* `PUT /api/v1/projects/{project_id}/tasks/{task_id}` â€” Update task status or assignee
* `DELETE /api/v1/projects/{project_id}/tasks/{task_id}` â€” Delete task (Owner or assignee)
* `POST /api/v1/projects/{project_id}/feedback` â€” Submit collaboration rating and feedback
* `GET /api/v1/projects/{project_id}/feedback` â€” Summary of feedback and average rating

### Admin Intelligence Console (Protected by `get_current_admin`)
* `GET /api/v1/admin/status` â€” Quick admin privilege check
* `GET /api/v1/admin/overview` â€” High-level KPI summary
* `GET /api/v1/admin/students` â€” Demographics and skill frequency analytics
* `GET /api/v1/admin/projects` â€” Project statuses and team sizes
* `GET /api/v1/admin/progress` â€” Average progress percentages and task distributions
* `GET /api/v1/admin/feedback` â€” Collaboration rating distributions and feedback history
* `GET /api/v1/admin/ai-matching` â€” MLP checkpoint inspection, Sentence Transformer status
* `GET /api/v1/admin/system` â€” Subsystem operational health status without secrets

---

## 19. Academic & Research Note

This platform was developed as an engineering capstone and research contribution exploring applied deep learning for human collaboration systems. It investigates the efficacy of fusing dense semantic embeddings from pretrained Transformer encoders with domain-engineered feature representations in a supervised Multi-Layer Perceptron to predict voluntary team compatibility.

---

## 20. License

Developed for academic and educational purposes. All rights reserved.
