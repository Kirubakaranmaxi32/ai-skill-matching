# Production Deployment Architecture & Step-by-Step Guide

**Project Name:** AI Skill Matching  
**Formal Title:** AI-Driven Student Skill Gap Analysis and Project Team Recommendation System Using Deep Learning  
**Tagline:** Find the right skills. Build the right team.  
**Repository:** `Kirubakaranmaxi32/ai-skill-matching`  
**Supabase Project:** `ai-skill-matching` (`https://hranjrkbriebixdrvsbr.supabase.co`)  

---

## 1. Executive Summary & Free Hosting Strategy

### The ML Backend Memory Problem on Free Hosts
The deep learning backend requires:
* **PyTorch CPU** (`torch>=2.2.0`)
* **Sentence Transformers** (`sentence-transformers>=3.0.0` with `all-MiniLM-L6-v2`)
* **Trained PyTorch MLP Checkpoint** (`models/checkpoints/best_matching_mlp.pt`, 10 → 64 → 32 → 1)
* **Scikit-learn, SciPy, NumPy, FastAPI, Uvicorn, Supabase Client**

**Runtime Resident Memory (RSS):** ~550 MB – 720 MB during active inference.  
**Why Render Free Failed:** Render Free enforces a hard **512 MB** memory limit. The Linux kernel OOM-killer terminates the process upon loading PyTorch shared libraries and transformer tensors.

### Recommended 100% Free Production Architecture
To run the **exact, uncompromised PyTorch model** without paying anything and without risking OOM crashes:

1. **Frontend Hosting: Vercel (Hobby Tier — $0/mo)**
   * Hosts React + Vite + TypeScript + Tailwind CSS.
   * Unlimited bandwidth, automatic SSL, SPA routing via `vercel.json` rewrites.
   * Global CDN edge caching.

2. **Backend ML Hosting: Hugging Face Spaces (Docker SDK — $0/mo)**
   * **Hardware:** **2 vCPU, 16 GB RAM, 50 GB Disk** — completely free forever!
   * Zero risk of Out-Of-Memory (OOM) crashes.
   * Full rootless Docker container running FastAPI on port 7860.
   * Free public HTTPS API endpoint: `https://<hf-username>-<space-name>.hf.space`.
   * Secure environment variables/secrets management.

3. **Alternative Instant Backend Hosting: Cloudflare Tunnel (cloudflared)**
   * If instant zero-configuration hosting is preferred during presentations, Cloudflare Tunnel securely routes public web requests directly to the running local FastAPI backend (`localhost:8000`) over HTTPS (`*.trycloudflare.com`) with zero port-forwarding and infinite RAM.

4. **Database, Auth & Storage: Supabase (`ai-skill-matching`)**
   * PostgreSQL database with RLS policies across all 15 phases.
   * Supabase Auth for student registration, sessions, and JWT validation.
   * Supabase Storage for project files and attachments.

---

## 2. Supabase Auth: Resolving the "Email Rate Limit Exceeded" Issue

### Root Cause
By default, Supabase's built-in shared email service enforces a strict rate limit of **3 to 4 emails per hour** to prevent spam abuse. During testing, student registrations quickly trigger `"email rate limit exceeded"`.

### Production Solution: Configure Supabase Auth
In the Supabase Dashboard (`https://supabase.com/dashboard/project/hranjrkbriebixdrvsbr`):

1. **Recommended for Demos & Presentations (Instant Login):**
   * Navigate to **Authentication** → **Providers** → **Email**.
   * Toggle **"Confirm email"** to **OFF** (Disabled).
   * Toggle **"Secure email change"** to **OFF**.
   * Click **Save**.
   * *Outcome:* When students register, their accounts are instantly confirmed and immediately logged in without waiting for an email or hitting the 3/hour email quota.

2. **If Email Verification is Required in Production (Custom SMTP):**
   * Navigate to **Project Settings** → **Authentication** → **SMTP Settings**.
   * Toggle **"Enable Custom SMTP"** to **ON**.
   * Provide SMTP credentials from a free email provider:
     * **Resend** (3,000 free emails/mo): Host `smtp.resend.com`, Port `465`, User `resend`, Password `<API_KEY>`.
     * **SendGrid** (100 free emails/day): Host `smtp.sendgrid.net`, Port `587`, User `apikey`, Password `<API_KEY>`.
     * **Gmail SMTP**: Host `smtp.gmail.com`, Port `587`, User `<email>`, Password `<Google App Password>`.
   * *Outcome:* Supabase bypasses its internal 3-email limit and sends via your dedicated provider.

3. **URL Configuration:**
   * Navigate to **Authentication** → **URL Configuration**.
   * Set **Site URL** to your production frontend URL (e.g., `https://ai-skill-matching.vercel.app`).
   * Add redirect URLs:
     * `https://ai-skill-matching.vercel.app/**`
     * `http://localhost:5173/**`

---

## 3. Required Environment Variables

### Backend Secrets & Variables (Server-Side Only)
*Never commit these or expose them to the frontend:*

| Variable Name | Example / Production Value | Purpose |
|---|---|---|
| `ENVIRONMENT` | `production` | Enables production mode |
| `DEBUG` | `False` | Disables verbose debug stack traces |
| `SECRET_KEY` | *(64-char random hex string)* | Cryptographic session & token security |
| `FRONTEND_URL` | `https://ai-skill-matching.vercel.app` | Primary frontend web address |
| `BACKEND_URL` | `https://<hf-user>-ai-skill-matching.hf.space` | Public backend API address |
| `ALLOWED_ORIGINS` | `https://ai-skill-matching.vercel.app,http://localhost:5173` | Allowed CORS origins (regex also matches `*.vercel.app`) |
| `SUPABASE_URL` | `https://hranjrkbriebixdrvsbr.supabase.co` | Supabase project API endpoint |
| `SUPABASE_ANON_KEY` | *(Supabase public anon key)* | Client-level database operations |
| `SUPABASE_SERVICE_ROLE_KEY` | *(Supabase private service_role key)* | Server-side elevated database operations & admin queries |
| `SUPABASE_JWT_SECRET` | *(Supabase JWT secret from API settings)* | Cryptographic JWT signature verification |
| `SENTENCE_TRANSFORMER_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Pretrained NLP representation model |
| `DEMO_MODE` | `False` | Enforces production Supabase data mode |

### Frontend Variables (Built into Bundle at Deploy Time)
*Public variables only:*

| Variable Name | Value | Purpose |
|---|---|---|
| `VITE_API_BASE_URL` | `https://<hf-user>-ai-skill-matching.hf.space/api/v1` | Production backend API v1 route |
| `VITE_BACKEND_URL` | `https://<hf-user>-ai-skill-matching.hf.space` | Production backend root URL (for `/health`) |
| `VITE_APP_NAME` | `AI Skill Matching` | Application branding |
| `VITE_APP_TAGLINE` | `Find the right skills. Build the right team.` | Application branding tagline |
| `VITE_SUPABASE_URL` | `https://hranjrkbriebixdrvsbr.supabase.co` | Public Supabase project endpoint |
| `VITE_SUPABASE_ANON_KEY` | *(Supabase public anon key)* | Public anon client key |

---

## 4. Step-by-Step Deployment Guide

### Phase A: Deploy Backend to Hugging Face Spaces (16 GB Free RAM)

1. Create a free account at [huggingface.co](https://huggingface.co).
2. Go to [huggingface.co/new-space](https://huggingface.co/new-space).
3. Fill in:
   * **Space name:** `ai-skill-matching-backend`
   * **License:** `mit`
   * **Space SDK:** Select **Docker** (Blank)
   * **Space Hardware:** Select **CPU basic • 2 vCPU • 16 GB RAM • Free**
   * **Visibility:** **Public**
4. In the Space dashboard, navigate to **Settings** → **Variables and secrets**.
5. Add the **Secrets** (New secret):
   * `SUPABASE_SERVICE_ROLE_KEY` = `<your-service-role-key>`
   * `SUPABASE_JWT_SECRET` = `<your-jwt-secret>`
   * `SECRET_KEY` = `<secure-random-string>`
6. Add the **Variables** (New variable):
   * `ENVIRONMENT` = `production`
   * `DEBUG` = `False`
   * `DEMO_MODE` = `False`
   * `SUPABASE_URL` = `https://hranjrkbriebixdrvsbr.supabase.co`
   * `SUPABASE_ANON_KEY` = `<your-anon-key>`
   * `PORT` = `7860`
7. Push the repository to your Hugging Face Space:
   ```bash
   git remote add space https://huggingface.co/spaces/<your-hf-username>/ai-skill-matching-backend
   git push space main
   ```
8. Hugging Face builds the Docker container and starts Uvicorn. Once the Space displays "Running", your backend is live at:
   `https://<your-hf-username>-ai-skill-matching-backend.hf.space`
9. Test by opening in browser:
   `https://<your-hf-username>-ai-skill-matching-backend.hf.space/health`
   Expected response: `{"status":"healthy","service":"ai-skill-matching-backend"}`

### Phase B: Deploy Frontend to Vercel

1. Create a free account at [vercel.com](https://vercel.com) and log in with GitHub.
2. Click **Add New...** → **Project**.
3. Import your GitHub repository: `Kirubakaranmaxi32/ai-skill-matching`.
4. Configure Build and Project Settings:
   * **Framework Preset:** `Vite`
   * **Root Directory:** Edit and select `frontend` (or leave root if relying on root `vercel.json`).
   * **Build Command:** `npm run build`
   * **Output Directory:** `dist`
5. Expand **Environment Variables** and add:
   * `VITE_API_BASE_URL` = `https://<your-hf-username>-ai-skill-matching-backend.hf.space/api/v1`
   * `VITE_BACKEND_URL` = `https://<your-hf-username>-ai-skill-matching-backend.hf.space`
   * `VITE_APP_NAME` = `AI Skill Matching`
   * `VITE_APP_TAGLINE` = `Find the right skills. Build the right team.`
   * `VITE_SUPABASE_URL` = `https://hranjrkbriebixdrvsbr.supabase.co`
   * `VITE_SUPABASE_ANON_KEY` = `<your-supabase-anon-key>`
6. Click **Deploy**.
7. In ~60 seconds, Vercel gives you your production URL:
   `https://ai-skill-matching.vercel.app` (or similar custom subdomain).

### Phase C: Finalize CORS in Hugging Face Backend

1. In Hugging Face Space Settings → **Variables and secrets**:
   * Update variable `ALLOWED_ORIGINS` = `https://ai-skill-matching.vercel.app,http://localhost:5173`
   * Update variable `FRONTEND_URL` = `https://ai-skill-matching.vercel.app`
2. Space automatically reloads with the updated origin.

---

## 5. End-to-End Verification Checklist

| Step | Flow Stage | Verification Method |
|---|---|---|
| 1 | **Home Page** | Open `https://<frontend-url>.vercel.app/`. Header shows "AI Skill Matching" and "AI Matching". No broken styles or console errors. |
| 2 | **Registration** | Register a new student account. Instant login occurs without "email rate limit exceeded" error. |
| 3 | **Login & Sessions** | Log in with registered credentials. Session token persists in local storage. |
| 4 | **Student Profile** | Navigate to `/profile`. Department, academic year, and bio can be saved to Supabase. |
| 5 | **Skills Management** | Add skills with proficiency 1–5. Records persist in `student_skills`. |
| 6 | **Project Creation** | Create a project with title, description, and required skills. |
| 7 | **AI Project Analysis** | Click "Analyze Project". Sentence Transformer extracts skill embeddings. |
| 8 | **Skill-Gap Analysis** | View missing skills and team coverage. |
| 9 | **PyTorch Compatibility** | Run recommendations. The `best_matching_mlp.pt` PyTorch model generates compatibility scores clamped to `[0.0, 1.0]`. |
| 10 | **Invitations & Teams** | Send invitation to candidate. Accept invitation; verify member joined project. |
| 11 | **Progress & Feedback** | Update task status, log progress, submit collaboration feedback. |
| 12 | **Admin Dashboard** | Open `/admin` with authorized administrator account. Statistics render accurately. |
