-- ==============================================================================
-- AI Skill Matching: Database Migration (Phase 14)
-- Title: Progress & Feedback
-- Schema: Project Progress, Project Tasks & Recommendation Feedback
-- Target: PostgreSQL (Supabase Compatible)
-- ==============================================================================

-- Ensure UUID generation extension is available
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Function: Automatic Updated Timestamp Trigger
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function: Automatic Task completed_at handling
CREATE OR REPLACE FUNCTION public.handle_task_completion()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        IF NEW.status = 'completed' AND NEW.completed_at IS NULL THEN
            NEW.completed_at = CURRENT_TIMESTAMP;
        ELSIF NEW.status <> 'completed' THEN
            NEW.completed_at = NULL;
        END IF;
    ELSIF TG_OP = 'UPDATE' THEN
        IF NEW.status = 'completed' AND (OLD.status IS NULL OR OLD.status <> 'completed') THEN
            IF NEW.completed_at IS NULL THEN
                NEW.completed_at = CURRENT_TIMESTAMP;
            END IF;
        ELSIF NEW.status <> 'completed' THEN
            NEW.completed_at = NULL;
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ==============================================================================
-- 1. Table: public.project_progress
-- Tracks overall project progress percentage, status, and summary.
-- Enforces only one progress record per project: UNIQUE(project_id).
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.project_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    progress_percentage INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(30) NOT NULL DEFAULT 'not_started',
    summary TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_progress_percentage_range CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
    CONSTRAINT chk_progress_status_valid CHECK (status IN ('not_started', 'in_progress', 'completed', 'blocked')),
    CONSTRAINT uq_project_progress_project_id UNIQUE (project_id)
);

-- ==============================================================================
-- 2. Table: public.project_tasks
-- Tracks individual project tasks, priorities, due dates, and member assignments.
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.project_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    assigned_to UUID REFERENCES public.students(id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(30) NOT NULL DEFAULT 'todo',
    priority VARCHAR(30) NOT NULL DEFAULT 'medium',
    due_date DATE,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_tasks_status_valid CHECK (status IN ('todo', 'in_progress', 'completed', 'blocked')),
    CONSTRAINT chk_tasks_priority_valid CHECK (priority IN ('low', 'medium', 'high')),
    CONSTRAINT chk_tasks_title_not_empty CHECK (char_length(trim(title)) > 0)
);

-- ==============================================================================
-- 3. Table: public.recommendation_feedback
-- Tracks post-recommendation / collaboration feedback from accepted project members.
-- Prevents duplicate feedback from the same student for the same project: UNIQUE(project_id, student_id).
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.recommendation_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES public.students(id) ON DELETE CASCADE,
    recommendation_id UUID NULL,
    rating INTEGER,
    feedback_text TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_feedback_rating_range CHECK (rating IS NULL OR (rating >= 1 AND rating <= 5)),
    CONSTRAINT uq_student_project_feedback UNIQUE (project_id, student_id)
);

-- ==============================================================================
-- 4. Query Performance Indexes
-- ==============================================================================
-- Indexes for public.project_progress
CREATE INDEX IF NOT EXISTS idx_project_progress_project_id ON public.project_progress(project_id);
CREATE INDEX IF NOT EXISTS idx_project_progress_created_at ON public.project_progress(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_project_progress_status ON public.project_progress(status);

-- Indexes for public.project_tasks
CREATE INDEX IF NOT EXISTS idx_project_tasks_project_id ON public.project_tasks(project_id);
CREATE INDEX IF NOT EXISTS idx_project_tasks_assigned_to ON public.project_tasks(assigned_to);
CREATE INDEX IF NOT EXISTS idx_project_tasks_status ON public.project_tasks(status);
CREATE INDEX IF NOT EXISTS idx_project_tasks_created_at ON public.project_tasks(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_project_tasks_due_date ON public.project_tasks(due_date);

-- Indexes for public.recommendation_feedback
CREATE INDEX IF NOT EXISTS idx_recommendation_feedback_project_id ON public.recommendation_feedback(project_id);
CREATE INDEX IF NOT EXISTS idx_recommendation_feedback_student_id ON public.recommendation_feedback(student_id);
CREATE INDEX IF NOT EXISTS idx_recommendation_feedback_created_at ON public.recommendation_feedback(created_at DESC);

-- ==============================================================================
-- 5. Triggers
-- ==============================================================================
-- Triggers for updated_at
DROP TRIGGER IF EXISTS trg_project_progress_updated_at ON public.project_progress;
CREATE TRIGGER trg_project_progress_updated_at
BEFORE UPDATE ON public.project_progress
FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

DROP TRIGGER IF EXISTS trg_project_tasks_updated_at ON public.project_tasks;
CREATE TRIGGER trg_project_tasks_updated_at
BEFORE UPDATE ON public.project_tasks
FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

DROP TRIGGER IF EXISTS trg_recommendation_feedback_updated_at ON public.recommendation_feedback;
CREATE TRIGGER trg_recommendation_feedback_updated_at
BEFORE UPDATE ON public.recommendation_feedback
FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

-- Trigger for project_tasks completed_at handling
DROP TRIGGER IF EXISTS trg_project_tasks_completion ON public.project_tasks;
CREATE TRIGGER trg_project_tasks_completion
BEFORE INSERT OR UPDATE ON public.project_tasks
FOR EACH ROW EXECUTE FUNCTION public.handle_task_completion();

-- ==============================================================================
-- 6. Role Privileges (Strictly authenticated and service_role; NO anon grant)
-- ==============================================================================
GRANT SELECT, INSERT, UPDATE, DELETE ON public.project_progress TO authenticated;
GRANT ALL ON public.project_progress TO service_role;

GRANT SELECT, INSERT, UPDATE, DELETE ON public.project_tasks TO authenticated;
GRANT ALL ON public.project_tasks TO service_role;

GRANT SELECT, INSERT, UPDATE, DELETE ON public.recommendation_feedback TO authenticated;
GRANT ALL ON public.recommendation_feedback TO service_role;

-- ==============================================================================
-- 7. Row Level Security (RLS)
-- ==============================================================================
ALTER TABLE public.project_progress ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.project_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.recommendation_feedback ENABLE ROW LEVEL SECURITY;

-- ------------------------------------------------------------------------------
-- A. Policies for public.project_progress
-- ------------------------------------------------------------------------------

-- SELECT: Allowed only to the project owner and accepted project members
DROP POLICY IF EXISTS "project_progress_select_policy" ON public.project_progress;
CREATE POLICY "project_progress_select_policy" ON public.project_progress
FOR SELECT TO authenticated
USING (
    project_id IN (
        SELECT id FROM public.projects
        WHERE owner_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
    )
    OR project_id IN (
        SELECT project_id FROM public.project_members
        WHERE student_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
    )
);

-- INSERT: Allowed only to the project owner and accepted project members
DROP POLICY IF EXISTS "project_progress_insert_policy" ON public.project_progress;
CREATE POLICY "project_progress_insert_policy" ON public.project_progress
FOR INSERT TO authenticated
WITH CHECK (
    project_id IN (
        SELECT id FROM public.projects
        WHERE owner_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
    )
    OR project_id IN (
        SELECT project_id FROM public.project_members
        WHERE student_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
    )
);

-- UPDATE: Allowed only to the project owner and accepted project members
DROP POLICY IF EXISTS "project_progress_update_policy" ON public.project_progress;
CREATE POLICY "project_progress_update_policy" ON public.project_progress
FOR UPDATE TO authenticated
USING (
    project_id IN (
        SELECT id FROM public.projects
        WHERE owner_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
    )
    OR project_id IN (
        SELECT project_id FROM public.project_members
        WHERE student_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
    )
);

-- DELETE: Allowed only to the project owner and accepted project members
DROP POLICY IF EXISTS "project_progress_delete_policy" ON public.project_progress;
CREATE POLICY "project_progress_delete_policy" ON public.project_progress
FOR DELETE TO authenticated
USING (
    project_id IN (
        SELECT id FROM public.projects
        WHERE owner_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
    )
    OR project_id IN (
        SELECT project_id FROM public.project_members
        WHERE student_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
    )
);

-- ------------------------------------------------------------------------------
-- B. Policies for public.project_tasks
-- ------------------------------------------------------------------------------

-- SELECT: Allowed only to the project owner and accepted project members
DROP POLICY IF EXISTS "project_tasks_select_policy" ON public.project_tasks;
CREATE POLICY "project_tasks_select_policy" ON public.project_tasks
FOR SELECT TO authenticated
USING (
    project_id IN (
        SELECT id FROM public.projects
        WHERE owner_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
    )
    OR project_id IN (
        SELECT project_id FROM public.project_members
        WHERE student_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
    )
);

-- INSERT: Allowed only to the project owner and accepted project members
DROP POLICY IF EXISTS "project_tasks_insert_policy" ON public.project_tasks;
CREATE POLICY "project_tasks_insert_policy" ON public.project_tasks
FOR INSERT TO authenticated
WITH CHECK (
    project_id IN (
        SELECT id FROM public.projects
        WHERE owner_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
    )
    OR project_id IN (
        SELECT project_id FROM public.project_members
        WHERE student_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
    )
);

-- UPDATE: Allowed only to the project owner and accepted project members (including assigned member)
DROP POLICY IF EXISTS "project_tasks_update_policy" ON public.project_tasks;
CREATE POLICY "project_tasks_update_policy" ON public.project_tasks
FOR UPDATE TO authenticated
USING (
    project_id IN (
        SELECT id FROM public.projects
        WHERE owner_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
    )
    OR project_id IN (
        SELECT project_id FROM public.project_members
        WHERE student_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
    )
    OR assigned_to IN (SELECT id FROM public.students WHERE user_id = auth.uid())
);

-- DELETE: Allowed only to the project owner and accepted project members
DROP POLICY IF EXISTS "project_tasks_delete_policy" ON public.project_tasks;
CREATE POLICY "project_tasks_delete_policy" ON public.project_tasks
FOR DELETE TO authenticated
USING (
    project_id IN (
        SELECT id FROM public.projects
        WHERE owner_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
    )
    OR project_id IN (
        SELECT project_id FROM public.project_members
        WHERE student_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
    )
);

-- ------------------------------------------------------------------------------
-- C. Policies for public.recommendation_feedback
-- ------------------------------------------------------------------------------

-- SELECT: Allowed only to the project owner and accepted project members
DROP POLICY IF EXISTS "recommendation_feedback_select_policy" ON public.recommendation_feedback;
CREATE POLICY "recommendation_feedback_select_policy" ON public.recommendation_feedback
FOR SELECT TO authenticated
USING (
    project_id IN (
        SELECT id FROM public.projects
        WHERE owner_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
    )
    OR project_id IN (
        SELECT project_id FROM public.project_members
        WHERE student_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
    )
);

-- INSERT: Allowed only to an authenticated student who is an accepted member of the project
DROP POLICY IF EXISTS "recommendation_feedback_insert_policy" ON public.recommendation_feedback;
CREATE POLICY "recommendation_feedback_insert_policy" ON public.recommendation_feedback
FOR INSERT TO authenticated
WITH CHECK (
    student_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
    AND (
        project_id IN (
            SELECT id FROM public.projects
            WHERE owner_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
        )
        OR project_id IN (
            SELECT project_id FROM public.project_members
            WHERE student_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
        )
    )
);

-- UPDATE: Feedback author can update their own feedback
DROP POLICY IF EXISTS "recommendation_feedback_update_policy" ON public.recommendation_feedback;
CREATE POLICY "recommendation_feedback_update_policy" ON public.recommendation_feedback
FOR UPDATE TO authenticated
USING (
    student_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
);
