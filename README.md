# AI Skill Matching

### *AI-Driven Student Skill Gap Analysis and Project Team Recommendation System Using Deep Learning*

> **"Find the right skills. Build the right team."**

---

## 1. Project Objective

**AI Skill Matching** is an intelligent, explainable student collaboration platform designed for collegiate engineering and academic environments. The system enables students to assemble complementary project teams by performing deterministic skill-gap analyses on project specifications and using a trainable **PyTorch Multi-Layer Perceptron (MLP)** to evaluate student-project compatibility.

### Key Tenets
- **Voluntary Team Formation:** The AI engine acts strictly as an advisory recommendation system. Teams are formed only with bilateral consent (Invited $\rightarrow$ Accepted); teams are never automatically or forcefully created.
- **Deep Learning Truth:** The core trainable component is a dedicated PyTorch MLP learning non-linear compatibility mappings. NLP (Sentence Transformers) is utilized strictly for text embeddings, and skill gap detection is performed deterministically.
- **Explainability:** All compatibility recommendations are paired with transparent, data-backed rationale grounded in student profile data and unfulfilled project requirements.

---

## 2. Technology Stack

- **Frontend:** React 18, Vite, TypeScript, Tailwind CSS, Lucide React, React Router DOM, Axios, Supabase Client (`@supabase/supabase-js`)
- **Backend:** Python 3.10+, FastAPI, Pydantic v2, Pydantic Settings, Uvicorn, PyJWT, Supabase-py
- **Database & Auth:** PostgreSQL (Supabase Compatible), Supabase Auth with Row-Level Security (RLS)
- **AI & Deep Learning (Future Phases):** PyTorch, Sentence Transformers (`all-MiniLM-L6-v2`), scikit-learn, Pandas, NumPy
- **Testing:** Pytest, pytest-asyncio, HTTPX

---

## 3. Current Development Phase

> **Current Phase:** **Phase 2 — Database and Authentication**
>
> *Status: Completed & Verified*  
> *Important Statement:* **The project is being developed incrementally. AI functionality and the trainable PyTorch MLP will be implemented in later phases.**

---

## 4. 18-Phase Development Roadmap

| Phase | Title | Focus Area | Status |
| :---: | :--- | :--- | :---: |
| 01 | Architecture and Project Setup | Monorepo layout, environments, FastAPI & React skeletons | **Completed** |
| **02** | **Database and Authentication** | **PostgreSQL schema, Supabase Auth, RLS, Protected routes** | **Completed** |
| 03 | Student Profiles and Skills | Profile CRUD, skill taxonomy, proficiency ratings | Next Up |
| 04 | Project Creation and Feed | Project lifecycle, required skills, public project feed | Planned |
| 05 | AI Project Analysis | Sentence Transformers embedding, NLP skill extraction | Planned |
| 06 | Skill-Gap Analysis | Deterministic set-theoretic gap detection ($S_{req} \setminus S_{team}$) | Planned |
| 07 | Synthetic Training Dataset | 35k synthetic student-project interaction dataset | Planned |
| 08 | Feature Engineering | 48-dimensional fused feature extraction pipeline | Planned |
| 09 | PyTorch MLP Architecture | Deep Learning compatibility neural network design | Planned |
| 10 | Model Training & Evaluation | Training loop, loss functions, MAE/RMSE/NDCG benchmarks | Planned |
| 11 | Recommendation Engine | Candidate ranking layer and filtering rules | Planned |
| 12 | Explainability Engine | Natural language attribution of match scores | Planned |
| 13 | Student Matching & Team Formation | Bilateral invitations and voluntary team formation | Planned |
| 14 | Progress and Feedback | Milestones tracking and recommendation rating ingestion | Planned |
| 15 | Admin Dashboard | Platform analytics, taxonomy curation, model auditing | Planned |
| 16 | Security Audit | OWASP Top 10 mitigation, rate limiting, RLS audit | Planned |
| 17 | Testing Suite | Automated unit, integration, and DL invariance tests | Planned |
| 18 | Deployment and Documentation | Docker containerization, OpenAPI docs, production guide | Planned |

---

## 5. Local Setup & Execution Guide

### Prerequisites
- Node.js (v18+ or v20+) and npm
- Python (v3.10+)
- Supabase Project (PostgreSQL & Auth)

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create & activate Python virtual environment
python -m venv venv
.\venv\Scripts\activate   # Windows
# source venv/bin/activate # Linux/macOS

# Install dependencies (Phase 1 & Phase 2)
pip install -r requirements.txt

# Run FastAPI backend
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Start Vite development server
npm run dev
```

---

## 6. Verification & Health Endpoints

- **Root Health:** `GET http://localhost:8000/health` (HTTP 200)
- **V1 API Health:** `GET http://localhost:8000/api/v1/health` (HTTP 200)
- **Current User Identity:** `GET http://localhost:8000/api/v1/auth/me`
  - Unauthenticated: Returns HTTP 401 Unauthorized
  - Authenticated (with Bearer token): Returns authenticated student profile claims
- **Interactive OpenAPI Documentation:** `http://localhost:8000/docs`
- **Frontend Web UI:** `http://localhost:5173`
  - Routes: `/` (Home), `/login` (Login), `/register` (Register), `/dashboard` (Protected)

---

## 7. License & Academic Attribution
Developed as an advanced academic research project on deep learning-driven collaboration systems.
