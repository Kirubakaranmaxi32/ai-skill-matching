-- ==============================================================================
-- AI Skill Matching: Database Migration (Phase 14 - Remaining Objects)
-- Title: Progress & Feedback (Functions, Indexes, Triggers, Grants, & RLS)
-- Target: PostgreSQL (Supabase Compatible)
-- ==============================================================================
--
-- Objective:
-- Apply remaining database objects for the already-created Phase 14 tables:
--   * public.project_progress
--   * public.project_tasks
--   * public.recommendation_feedback
--
-- Safety Guarantees:
-- 1. ZERO CREATE TABLE statements (tables already exist).
-- 2. ZERO DROP statements (non-destructive).
-- 3. ZERO data mutation statements (no INSERT, UPDATE, DELETE, or TRUNCATE).
-- 4. Does not alter or modify any Phase 1-13 tables.
-- 5. Safe and idempotent using IF NOT EXISTS and conditional existence checks.
-- ==============================================================================

-- ==============================================================================
-- 1. Trigger Functions
-- ==============================================================================

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
-- 2. Query Performance Indexes
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
-- 3. Triggers (Created safely if not already present)
-- ==============================================================================

-- Trigger: Updated timestamp on public.project_progress
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'trg_project_progress_updated_at'
    ) THEN
        CREATE TRIGGER trg_project_progress_updated_at
        BEFORE UPDATE ON public.project_progress
        FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();
    END IF;
END $$;

-- Trigger: Updated timestamp on public.project_tasks
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'trg_project_tasks_updated_at'
    ) THEN
        CREATE TRIGGER trg_project_tasks_updated_at
        BEFORE UPDATE ON public.project_tasks
        FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();
    END IF;
END $$;

-- Trigger: Updated timestamp on public.recommendation_feedback
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'trg_recommendation_feedback_updated_at'
    ) THEN
        CREATE TRIGGER trg_recommendation_feedback_updated_at
        BEFORE UPDATE ON public.recommendation_feedback
        FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();
    END IF;
END $$;

-- Trigger: Task completion timestamp on public.project_tasks
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'trg_project_tasks_completion'
    ) THEN
        CREATE TRIGGER trg_project_tasks_completion
        BEFORE INSERT OR UPDATE ON public.project_tasks
        FOR EACH ROW EXECUTE FUNCTION public.handle_task_completion();
    END IF;
END $$;

-- ==============================================================================
-- 4. Role Privileges (Strictly authenticated and service_role; NO anon grant)
-- ==============================================================================

GRANT SELECT, INSERT, UPDATE, DELETE ON public.project_progress TO authenticated;
GRANT ALL ON public.project_progress TO service_role;

GRANT SELECT, INSERT, UPDATE, DELETE ON public.project_tasks TO authenticated;
GRANT ALL ON public.project_tasks TO service_role;

GRANT SELECT, INSERT, UPDATE, DELETE ON public.recommendation_feedback TO authenticated;
GRANT ALL ON public.recommendation_feedback TO service_role;

-- ==============================================================================
-- 5. Row Level Security (RLS) Enablement
-- ==============================================================================

ALTER TABLE public.project_progress ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.project_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.recommendation_feedback ENABLE ROW LEVEL SECURITY;

-- ==============================================================================
-- 6. Row Level Security Policies (Created safely if not already present)
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- A. Policies for public.project_progress
-- ------------------------------------------------------------------------------

-- SELECT: Allowed to project owner and accepted project members
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public' AND tablename = 'project_progress' AND policyname = 'project_progress_select_policy'
    ) THEN
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
    END IF;
END $$;

-- INSERT: Allowed to project owner and accepted project members
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public' AND tablename = 'project_progress' AND policyname = 'project_progress_insert_policy'
    ) THEN
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
    END IF;
END $$;

-- UPDATE: Allowed to project owner and accepted project members
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public' AND tablename = 'project_progress' AND policyname = 'project_progress_update_policy'
    ) THEN
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
    END IF;
END $$;

-- DELETE: Allowed to project owner and accepted project members
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public' AND tablename = 'project_progress' AND policyname = 'project_progress_delete_policy'
    ) THEN
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
    END IF;
END $$;

-- ------------------------------------------------------------------------------
-- B. Policies for public.project_tasks
-- ------------------------------------------------------------------------------

-- SELECT: Allowed to project owner and accepted project members
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public' AND tablename = 'project_tasks' AND policyname = 'project_tasks_select_policy'
    ) THEN
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
    END IF;
END $$;

-- INSERT: Allowed to project owner and accepted project members
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public' AND tablename = 'project_tasks' AND policyname = 'project_tasks_insert_policy'
    ) THEN
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
    END IF;
END $$;

-- UPDATE: Allowed to project owner, accepted project members, and assigned member
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public' AND tablename = 'project_tasks' AND policyname = 'project_tasks_update_policy'
    ) THEN
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
    END IF;
END $$;

-- DELETE: Allowed to project owner and accepted project members
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public' AND tablename = 'project_tasks' AND policyname = 'project_tasks_delete_policy'
    ) THEN
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
    END IF;
END $$;

-- ------------------------------------------------------------------------------
-- C. Policies for public.recommendation_feedback
-- ------------------------------------------------------------------------------

-- SELECT: Allowed to project owner and accepted project members
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public' AND tablename = 'recommendation_feedback' AND policyname = 'recommendation_feedback_select_policy'
    ) THEN
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
    END IF;
END $$;

-- INSERT: Allowed only to an authenticated student who is an accepted member or owner of the project
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public' AND tablename = 'recommendation_feedback' AND policyname = 'recommendation_feedback_insert_policy'
    ) THEN
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
    END IF;
END $$;

-- UPDATE: Feedback author can update their own feedback
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public' AND tablename = 'recommendation_feedback' AND policyname = 'recommendation_feedback_update_policy'
    ) THEN
        CREATE POLICY "recommendation_feedback_update_policy" ON public.recommendation_feedback
        FOR UPDATE TO authenticated
        USING (
            student_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
        );
    END IF;
END $$;
