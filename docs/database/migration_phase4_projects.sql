-- ==============================================================================
-- AI Skill Matching: Database Migration (Phase 4)
-- Schema: Projects, Project Skills, & Project Team Members
-- Target: PostgreSQL (Supabase Compatible)
-- ==============================================================================
--
-- Objective:
-- Support Project Creation, Project Feed, and prepare team formation structures.
-- Integrates with existing Phase 3 schema (students, skills) via strict foreign keys.
--
-- Security:
-- Row-Level Security (RLS) is enabled on all tables.
-- Students can only create/update/delete their own projects and project assets.
-- Non-archived projects and their required skills/members are discoverable by authenticated peers.
-- ==============================================================================

-- Ensure required UUID generation functions are available
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Function: Automatic Updated Timestamp Trigger (reused from Phase 3 if present)
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ==============================================================================
-- 1. Projects (Core project specifications)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID NOT NULL REFERENCES public.students(id) ON DELETE CASCADE,
    title VARCHAR(150) NOT NULL,
    description TEXT NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'open',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_projects_title_not_empty CHECK (char_length(trim(title)) > 0),
    CONSTRAINT chk_projects_description_not_empty CHECK (char_length(trim(description)) > 0),
    CONSTRAINT chk_projects_status_valid CHECK (status IN ('open', 'in_progress', 'completed', 'archived'))
);

-- Indexes for performance & query optimization
CREATE INDEX IF NOT EXISTS idx_projects_owner_id ON public.projects(owner_id);
CREATE INDEX IF NOT EXISTS idx_projects_status ON public.projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_created_at ON public.projects(created_at DESC);

-- Automatic updated_at timestamp trigger
DROP TRIGGER IF EXISTS trg_projects_updated_at ON public.projects;
CREATE TRIGGER trg_projects_updated_at
BEFORE UPDATE ON public.projects
FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

-- ==============================================================================
-- 2. Project Skills (Required skills for projects)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.project_skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    skill_id UUID NOT NULL REFERENCES public.skills(id) ON DELETE RESTRICT,
    required_proficiency INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_project_skills_proficiency_range CHECK (required_proficiency BETWEEN 1 AND 4),
    CONSTRAINT uq_project_skills_pair UNIQUE (project_id, skill_id)
);

-- Indexes on foreign keys
CREATE INDEX IF NOT EXISTS idx_project_skills_project_id ON public.project_skills(project_id);
CREATE INDEX IF NOT EXISTS idx_project_skills_skill_id ON public.project_skills(skill_id);

-- ==============================================================================
-- 3. Project Members (Team formation preparation)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.project_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES public.students(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL DEFAULT 'member',
    joined_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_project_members_role_valid CHECK (role IN ('owner', 'member')),
    CONSTRAINT uq_project_members_pair UNIQUE (project_id, student_id)
);

-- Indexes on foreign keys
CREATE INDEX IF NOT EXISTS idx_project_members_project_id ON public.project_members(project_id);
CREATE INDEX IF NOT EXISTS idx_project_members_student_id ON public.project_members(student_id);

-- ==============================================================================
-- 4. Explicit Role Privileges (PostgREST API Grants)
-- ==============================================================================
GRANT SELECT, INSERT, UPDATE, DELETE ON public.projects TO authenticated;
GRANT SELECT ON public.projects TO anon;
GRANT ALL ON public.projects TO service_role;

GRANT SELECT, INSERT, UPDATE, DELETE ON public.project_skills TO authenticated;
GRANT SELECT ON public.project_skills TO anon;
GRANT ALL ON public.project_skills TO service_role;

GRANT SELECT, INSERT, UPDATE, DELETE ON public.project_members TO authenticated;
GRANT SELECT ON public.project_members TO anon;
GRANT ALL ON public.project_members TO service_role;

-- ==============================================================================
-- 5. Row-Level Security (RLS) Enablement
-- ==============================================================================
ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.project_skills ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.project_members ENABLE ROW LEVEL SECURITY;

-- ==============================================================================
-- 6. Row-Level Security Policies
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- A. Projects Policies
-- ------------------------------------------------------------------------------

-- Authenticated users can read non-archived projects in the project feed.
-- Project creators can also view their own archived projects.
DROP POLICY IF EXISTS "Allow authenticated read on non-archived projects" ON public.projects;
CREATE POLICY "Allow authenticated read on non-archived projects"
ON public.projects FOR SELECT
TO authenticated
USING (
    status != 'archived'
    OR owner_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
);

-- Authenticated users can insert a project strictly owned by their own student profile
DROP POLICY IF EXISTS "Allow individual student project insert" ON public.projects;
CREATE POLICY "Allow individual student project insert"
ON public.projects FOR INSERT
TO authenticated
WITH CHECK (
    owner_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
);

-- Project owners can update their own project details
DROP POLICY IF EXISTS "Allow owner project update" ON public.projects;
CREATE POLICY "Allow owner project update"
ON public.projects FOR UPDATE
TO authenticated
USING (
    owner_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
)
WITH CHECK (
    owner_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
);

-- Project owners can delete (or archive) their own projects
DROP POLICY IF EXISTS "Allow owner project delete" ON public.projects;
CREATE POLICY "Allow owner project delete"
ON public.projects FOR DELETE
TO authenticated
USING (
    owner_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
);

-- ------------------------------------------------------------------------------
-- B. Project Skills Policies
-- ------------------------------------------------------------------------------

-- Authenticated users can view required skills for readable projects
DROP POLICY IF EXISTS "Allow authenticated read on project_skills" ON public.project_skills;
CREATE POLICY "Allow authenticated read on project_skills"
ON public.project_skills FOR SELECT
TO authenticated
USING (
    project_id IN (
        SELECT id FROM public.projects
        WHERE status != 'archived'
           OR owner_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
    )
);

-- Project owner can add required skills to their project
DROP POLICY IF EXISTS "Allow owner project_skills insert" ON public.project_skills;
CREATE POLICY "Allow owner project_skills insert"
ON public.project_skills FOR INSERT
TO authenticated
WITH CHECK (
    project_id IN (
        SELECT id FROM public.projects
        WHERE owner_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
    )
);

-- Project owner can update required skills for their project
DROP POLICY IF EXISTS "Allow owner project_skills update" ON public.project_skills;
CREATE POLICY "Allow owner project_skills update"
ON public.project_skills FOR UPDATE
TO authenticated
USING (
    project_id IN (
        SELECT id FROM public.projects
        WHERE owner_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
    )
)
WITH CHECK (
    project_id IN (
        SELECT id FROM public.projects
        WHERE owner_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
    )
);

-- Project owner can delete required skills from their project
DROP POLICY IF EXISTS "Allow owner project_skills delete" ON public.project_skills;
CREATE POLICY "Allow owner project_skills delete"
ON public.project_skills FOR DELETE
TO authenticated
USING (
    project_id IN (
        SELECT id FROM public.projects
        WHERE owner_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
    )
);

-- ------------------------------------------------------------------------------
-- C. Project Members Policies
-- ------------------------------------------------------------------------------

-- Authenticated users can view member rosters of readable projects
DROP POLICY IF EXISTS "Allow authenticated read on project_members" ON public.project_members;
CREATE POLICY "Allow authenticated read on project_members"
ON public.project_members FOR SELECT
TO authenticated
USING (
    project_id IN (
        SELECT id FROM public.projects
        WHERE status != 'archived'
           OR owner_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
    )
);

-- Project owner controls member additions (team formation prep)
DROP POLICY IF EXISTS "Allow owner project_members insert" ON public.project_members;
CREATE POLICY "Allow owner project_members insert"
ON public.project_members FOR INSERT
TO authenticated
WITH CHECK (
    project_id IN (
        SELECT id FROM public.projects
        WHERE owner_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
    )
);

-- Project owner controls member updates
DROP POLICY IF EXISTS "Allow owner project_members update" ON public.project_members;
CREATE POLICY "Allow owner project_members update"
ON public.project_members FOR UPDATE
TO authenticated
USING (
    project_id IN (
        SELECT id FROM public.projects
        WHERE owner_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
    )
)
WITH CHECK (
    project_id IN (
        SELECT id FROM public.projects
        WHERE owner_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
    )
);

-- Project owner controls member removals
DROP POLICY IF EXISTS "Allow owner project_members delete" ON public.project_members;
CREATE POLICY "Allow owner project_members delete"
ON public.project_members FOR DELETE
TO authenticated
USING (
    project_id IN (
        SELECT id FROM public.projects
        WHERE owner_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
    )
);
