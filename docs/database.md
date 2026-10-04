# Database & Authentication Architecture (Phase 2)

**Project Name:** AI Skill Matching  
**Component:** PostgreSQL / Supabase Database Foundation & Supabase Auth Integration

---

## 1. Supabase Setup Guide

The application uses **Supabase** for managed PostgreSQL hosting and user authentication.

### Local Development / Cloud Setup Steps:
1. Log in to [Supabase Console](https://supabase.com).
2. Create a new project: `ai-skill-matching`.
3. In **Project Settings $\rightarrow$ API**, retrieve:
   - **Project URL:** e.g., `https://<project-ref>.supabase.co`
   - **Anon Public API Key:** `eyJhbGciOi...`
   - **Service Role Secret Key:** `eyJhbGciOi...` (backend only, never expose to frontend)
   - **JWT Secret:** (under API $\rightarrow$ JWT Settings)
4. In the **SQL Editor**, execute the migration script:
   - Run `docs/database/schema_phase2.sql` to initialize all tables and Row-Level Security (RLS) policies.
   - Run `docs/database/seed_phase2.sql` to populate canonical department and skill taxonomy reference records.
5. In **Authentication $\rightarrow$ URL Configuration**, ensure Site URL is configured to:
   - `http://localhost:5173` (Frontend development server)

---

## 2. Environment Variables Specification

### Frontend (`frontend/.env`)
```ini
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_BACKEND_URL=http://localhost:8000
VITE_APP_NAME="AI Skill Matching"
VITE_APP_TAGLINE="Find the right skills. Build the right team."

# Supabase Auth Integration
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-supabase-anon-key
```

### Backend (`backend/.env`)
```ini
ENVIRONMENT=development
DEBUG=true
API_V1_STR=/api/v1
SECRET_KEY=change-me-to-a-secure-secret-key-in-production
FRONTEND_URL=http://localhost:5173
BACKEND_URL=http://localhost:8000
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key
SUPABASE_JWT_SECRET=your-supabase-jwt-secret
```

> [!CAUTION]
> The `SUPABASE_SERVICE_ROLE_KEY` bypasses Row-Level Security and must **never** be exposed in the frontend or committed to source control.

---

## 3. Database Tables (3NF Schema)

| Table | Primary Key | Description | Relationships / Foreign Keys |
| :--- | :--- | :--- | :--- |
| `departments` | `id UUID` | Academic departments | Referenced by `students.department_id` |
| `students` | `id UUID` | Student profile records | Extends `auth.users(id)` via `user_id` |
| `skills` | `id UUID` | Standard skill taxonomy | Referenced by `student_skills.skill_id` |
| `student_skills` | `id UUID` | Student proficiency ratings | Composite unique on `(student_id, skill_id)` |
| `interests` | `id UUID` | Project interest categories | Referenced by `student_interests.interest_id` |
| `student_interests` | `id UUID` | Student interest mappings | Composite unique on `(student_id, interest_id)` |
| `student_certifications` | `id UUID` | Verified achievements | `student_id REFERENCES students(id)` |
| `student_previous_projects`| `id UUID` | Portfolio items | `student_id REFERENCES students(id)` |

---

## 4. Authentication Flow

```
1. Student registers on Frontend (/register)
       ↓
2. Supabase Auth generates user record in auth.users
       ↓
3. Application initializes student profile in public.students (user_id = auth.uid())
       ↓
4. User logs in (/login) with email and password
       ↓
5. Supabase returns JWT access token + refresh token
       ↓
6. Frontend AuthContext caches session and provides user claims
       ↓
7. Authenticated requests pass Authorization: Bearer <token>
       ↓
8. FastAPI dependency (app.core.auth.get_current_user) verifies cryptographic signature
       ↓
9. PostgreSQL evaluates Row-Level Security (auth.uid() = user_id)
```

---

## 5. Row-Level Security (RLS) Strategy

Row-Level Security is strictly enabled on all tables:
- **Reference Tables (`departments`, `skills`, `interests`):** Public read-only access for all authenticated and anonymous clients; mutations restricted to administrators.
- **Identity Table (`students`):** Authenticated students can view basic profile information across peers, but can only mutate (`INSERT`, `UPDATE`) records matching their own `auth.uid()`.
- **Private Data (`student_skills`, `student_certifications`, `student_previous_projects`):** Students can view and mutate only their own related records via `student_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())`.
- **Public Isolation:** Unauthenticated users have zero access to student profile details.

---

## 6. Security Considerations

- **Password Storage:** Managed exclusively by Supabase Auth using Argon2 / bcrypt. Plaintext passwords never reach application storage or application logs.
- **Token Verification:** Backend cryptographically validates JWT tokens against the Supabase secret key or live auth client. Arbitrary user ID headers from the client are completely rejected.
- **State Injection Defense:** Frontend client guards (`ProtectedRoute`) prevent unauthorized view rendering, while backend dependencies enforce HTTP 401 Unauthorized for unauthenticated API requests.
