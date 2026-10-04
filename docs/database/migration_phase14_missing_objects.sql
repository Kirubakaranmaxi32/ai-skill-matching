-- ==============================================================================
-- AI Skill Matching: Database Migration (Phase 14 - Missing Objects)
-- File: docs/database/migration_phase14_missing_objects.sql
-- Title: Progress & Feedback (Functions, Indexes, Triggers & Grants)
-- Target: PostgreSQL (Supabase Compatible)
-- ==============================================================================
--
-- Objective:
-- Apply the remaining database objects for the Phase 14 tables:
--   * public.project_progress
--   * public.project_tasks
--   * public.recommendation_feedback
--
-- Objects Created:
-- 1. Trigger Functions (2):
--    - public.handle_updated_at()
--    - public.handle_task_completion()
-- 2. Indexes (11 query performance indexes):
--    - 3 on public.project_progress
--    - 5 on public.project_tasks
--    - 3 on public.recommendation_feedback
-- 3. Triggers (4 triggers with DROP TRIGGER IF EXISTS):
--    - trg_project_progress_updated_at on public.project_progress
--    - trg_project_tasks_updated_at on public.project_tasks
--    - trg_recommendation_feedback_updated_at on public.recommendation_feedback
--    - trg_project_tasks_completion on public.project_tasks
-- 4. Role Grants (6 statements):
--    - authenticated: SELECT, INSERT, UPDATE, DELETE on all 3 tables
--    - service_role: ALL on all 3 tables
--    - (Strictly NO grant to anon)
--
-- Safety Guarantees:
-- - ZERO CREATE TABLE / DROP TABLE statements (tables already exist).
-- - ZERO CREATE POLICY / DROP POLICY statements (RLS policies already exist).
-- - ZERO data mutation statements (no INSERT, UPDATE, DELETE, or TRUNCATE).
-- - ZERO modifications to Phase 1-13 tables.
-- - Safe and re-runnable (IF NOT EXISTS, CREATE OR REPLACE, DROP TRIGGER IF EXISTS).
-- ==============================================================================

-- ==============================================================================
-- 1. Trigger Functions
-- ==============================================================================

-- Function 1: Automatic updated_at timestamp handler
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function 2: Automatic task completed_at timestamp handler
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
-- 2. Query Performance Indexes (11 Indexes)
-- ==============================================================================

-- Indexes for public.project_progress (3 indexes)
CREATE INDEX IF NOT EXISTS idx_project_progress_project_id ON public.project_progress(project_id);
CREATE INDEX IF NOT EXISTS idx_project_progress_created_at ON public.project_progress(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_project_progress_status ON public.project_progress(status);

-- Indexes for public.project_tasks (5 indexes)
CREATE INDEX IF NOT EXISTS idx_project_tasks_project_id ON public.project_tasks(project_id);
CREATE INDEX IF NOT EXISTS idx_project_tasks_assigned_to ON public.project_tasks(assigned_to);
CREATE INDEX IF NOT EXISTS idx_project_tasks_status ON public.project_tasks(status);
CREATE INDEX IF NOT EXISTS idx_project_tasks_created_at ON public.project_tasks(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_project_tasks_due_date ON public.project_tasks(due_date);

-- Indexes for public.recommendation_feedback (3 indexes)
CREATE INDEX IF NOT EXISTS idx_recommendation_feedback_project_id ON public.recommendation_feedback(project_id);
CREATE INDEX IF NOT EXISTS idx_recommendation_feedback_student_id ON public.recommendation_feedback(student_id);
CREATE INDEX IF NOT EXISTS idx_recommendation_feedback_created_at ON public.recommendation_feedback(created_at DESC);

-- ==============================================================================
-- 3. Triggers (4 Triggers)
-- ==============================================================================

-- Trigger 1: Updated timestamp on public.project_progress
DROP TRIGGER IF EXISTS trg_project_progress_updated_at ON public.project_progress;
CREATE TRIGGER trg_project_progress_updated_at
BEFORE UPDATE ON public.project_progress
FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

-- Trigger 2: Updated timestamp on public.project_tasks
DROP TRIGGER IF EXISTS trg_project_tasks_updated_at ON public.project_tasks;
CREATE TRIGGER trg_project_tasks_updated_at
BEFORE UPDATE ON public.project_tasks
FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

-- Trigger 3: Updated timestamp on public.recommendation_feedback
DROP TRIGGER IF EXISTS trg_recommendation_feedback_updated_at ON public.recommendation_feedback;
CREATE TRIGGER trg_recommendation_feedback_updated_at
BEFORE UPDATE ON public.recommendation_feedback
FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

-- Trigger 4: Task completion timestamp on public.project_tasks
DROP TRIGGER IF EXISTS trg_project_tasks_completion ON public.project_tasks;
CREATE TRIGGER trg_project_tasks_completion
BEFORE INSERT OR UPDATE ON public.project_tasks
FOR EACH ROW EXECUTE FUNCTION public.handle_task_completion();

-- ==============================================================================
-- 4. Role Grants (Strictly authenticated and service_role; NO anon grant)
-- ==============================================================================

-- Grants for public.project_progress
GRANT SELECT, INSERT, UPDATE, DELETE ON public.project_progress TO authenticated;
GRANT ALL ON public.project_progress TO service_role;

-- Grants for public.project_tasks
GRANT SELECT, INSERT, UPDATE, DELETE ON public.project_tasks TO authenticated;
GRANT ALL ON public.project_tasks TO service_role;

-- Grants for public.recommendation_feedback
GRANT SELECT, INSERT, UPDATE, DELETE ON public.recommendation_feedback TO authenticated;
GRANT ALL ON public.recommendation_feedback TO service_role;
