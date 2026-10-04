-- ==============================================================================
-- AI Skill Matching: Database Migration (Phase 15 - Admin Role)
-- File: docs/database/migration_phase15_admin.sql
-- Title: Admin Users Table & Authorization Security
-- Target: PostgreSQL (Supabase Compatible)
-- ==============================================================================
--
-- Objective:
-- Establish a secure, dedicated admin_users table for Phase 15 Admin Dashboard.
-- Prevents standard authenticated students from escalating privileges.
-- Strictly preserves Phase 1-14 tables, triggers, constraints, and RLS policies.
--
-- Security Guarantees:
-- 1. References auth.users(id) with CASCADE delete.
-- 2. UNIQUE(user_id) ensures one-to-one user admin mapping.
-- 3. RLS enabled: Authenticated users can ONLY SELECT their own record (to check if they are admin).
-- 4. ZERO INSERT/UPDATE/DELETE policies for authenticated users.
--    Normal users CANNOT insert themselves or update their role.
-- 5. Only service_role can INSERT, UPDATE, or DELETE admin records.
-- 6. Zero fake or seed data inserted.
-- ==============================================================================

-- 1. Admin Users Table
CREATE TABLE IF NOT EXISTS public.admin_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    role VARCHAR(30) NOT NULL DEFAULT 'admin',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_admin_users_user_id UNIQUE (user_id),
    CONSTRAINT chk_admin_users_role CHECK (role IN ('admin', 'super_admin'))
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_admin_users_user_id ON public.admin_users(user_id);
CREATE INDEX IF NOT EXISTS idx_admin_users_email ON public.admin_users(email);

-- Automatic updated_at trigger (using existing handle_updated_at function)
DROP TRIGGER IF EXISTS trg_admin_users_updated_at ON public.admin_users;
CREATE TRIGGER trg_admin_users_updated_at
BEFORE UPDATE ON public.admin_users
FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

-- 2. Row Level Security (RLS)
ALTER TABLE public.admin_users ENABLE ROW LEVEL SECURITY;

-- Policy: Authenticated users can only read their own admin entry to verify their admin status
DROP POLICY IF EXISTS "admin_users_select_own_policy" ON public.admin_users;
CREATE POLICY "admin_users_select_own_policy" ON public.admin_users
FOR SELECT TO authenticated
USING (user_id = auth.uid());

-- 3. Role Privileges
-- authenticated can only SELECT (constrained by RLS above; cannot write)
GRANT SELECT ON public.admin_users TO authenticated;
-- service_role has ALL administrative privileges
GRANT ALL ON public.admin_users TO service_role;
