# System Architecture: AI Skill Matching

**Project Title:** AI-Driven Student Skill Gap Analysis and Project Team Recommendation System Using Deep Learning  
**Tagline:** Find the right skills. Build the right team.  
**Implementation Progress:** Phase 1 (Foundation) & Phase 2 (Database & Authentication) Complete

---

## 1. System Philosophy & Non-Negotiable Invariants

1. **Voluntary Team Formation:** Teams are formed exclusively through explicit bilateral consent (Invitation $\rightarrow$ Candidate Acceptance). Under no circumstance does the system force-assign any member.
2. **Deep Learning Architectural Truth:**
   - **Sentence Transformers** (`all-MiniLM-L6-v2`) provide pretrained dense text representations for project problem descriptions.
   - **Skill Gap Analysis** is a deterministic, set-theoretic mathematical computation ($G = S_{req} \setminus S_{team}$).
   - **PyTorch MLP** is the core trainable Deep Learning model learning non-linear compatibility mappings from a 48-dimensional fused feature representation.
   - **Recommendation Layer** filters eligible candidates, applies thresholds, and generates human-readable explanations.
3. **Data-Backed Explainability:** Explanations must be strictly derived from stored candidate profiles and project requirements (e.g. gaps covered, skill proficiency levels, availability).

---

## 2. Multi-Tier System Topology

- **Presentation Tier:** React 18 + Vite + TypeScript single-page application. Features responsive UI, client-side route guards (`ProtectedRoute`), `AuthContext` for session lifecycle, and TanStack Query.
- **Application Tier:** FastAPI asynchronous REST API with Pydantic validation, structured versioning (`/api/v1`), Supabase JWT verification dependency (`app.core.auth.get_current_user`), and dependency injection.
- **AI & ML Subsystem:** Standalone inference pipeline handling text embeddings, deterministic gap logic, feature vector assembly ($D=48$), PyTorch model forward pass, and candidate ranking.
- **Persistence Tier:** Normalized PostgreSQL (Supabase-compatible) ensuring 3NF data integrity, foreign key cascades, and Row-Level Security (RLS) policies.

---

## 3. Database & Authentication Implementation (Phase 2)

- **Supabase PostgreSQL Schema:** Defined in `docs/database/schema_phase2.sql`.
  - Tables: `departments`, `students`, `skills`, `student_skills`, `interests`, `student_interests`, `student_certifications`, `student_previous_projects`.
- **Row-Level Security (RLS):** Enabled across all student and profile association tables; ensures students access and mutate exclusively their own records.
- **JWT Authentication:** Reusable FastAPI dependency verifies Supabase access tokens, rejecting unauthenticated requests with HTTP 401.

---

## 4. End-to-End AI Workflow (Upcoming Phases)

```
Project Description
       ↓
Sentence Transformer (MiniLM)
       ↓
Project Embedding (384-D)
       ↓
AI Skill Identification (Hybrid NLP)
       ↓
Student confirms/edits skills (Human-in-the-Loop)
       ↓
Required Project Skills (S_req)
       ↓
Skill Gap Analysis (G_proj = S_req \ S_team)
       ↓
Student + Project Feature Engineering
       ↓
Feature Fusion (Vector X ∈ ℝ^48)
       ↓
PyTorch Neural Matching Model (MLP)
       ↓
Compatibility Score (ŷ ∈ [0, 1])
       ↓
Candidate Ranking
       ↓
Explainable Recommendation
       ↓
Student Invitation
       ↓
Voluntary Team Formation
```

---

## 5. Development Boundaries

- **Phase 1:** Monorepo architecture & setup verified.
- **Phase 2:** Database schema DDL, RLS policies, Supabase client integration, and frontend/backend authentication verified.
- **Phase 3:** Student Profiles & Skill Management UI (Pending approval).
