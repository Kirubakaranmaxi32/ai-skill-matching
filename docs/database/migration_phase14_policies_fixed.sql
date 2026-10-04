-- ==============================================================================
-- AI Skill Matching: Database Migration (Phase 14 - Row Level Security Policies)
-- File: docs/database/migration_phase14_policies_fixed.sql
-- Title: Progress & Feedback (Direct RLS Policies Creation)
-- Target: PostgreSQL (Supabase Compatible)
-- ==============================================================================
--
-- Objective:
-- Directly create the 11 Row Level Security (RLS) policies for the Phase 14 tables:
--   1. public.project_progress (4 policies)
--   2. public.project_tasks (4 policies)
--   3. public.recommendation_feedback (3 policies)
--
-- Safety Guarantees:
-- 1. ZERO CREATE TABLE statements (tables already exist).
-- 2. ZERO DROP statements (no DROP POLICY, DROP TABLE, etc.).
-- 3. ZERO data mutation statements (no INSERT, UPDATE, DELETE, or TRUNCATE).
-- 4. ZERO schema alterations, triggers, functions, grants, or index definitions.
-- 5. Standard top-level DDL statements directly recognized and executed by PostgreSQL.
-- 6. Safe to execute when policies are currently absent.
-- ==============================================================================

-- ==============================================================================
-- 1. Policies for public.project_progress (4 policies)
-- ==============================================================================

-- Policy 1: SELECT - Allowed to project owner and accepted project members
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

-- Policy 2: INSERT - Allowed to project owner and accepted project members
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

-- Policy 3: UPDATE - Allowed to project owner and accepted project members
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
)
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

-- Policy 4: DELETE - Allowed to project owner and accepted project members
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

-- ==============================================================================
-- 2. Policies for public.project_tasks (4 policies)
-- ==============================================================================

-- Policy 5: SELECT - Allowed to project owner and accepted project members
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

-- Policy 6: INSERT - Allowed to project owner and accepted project members
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

-- Policy 7: UPDATE - Allowed to project owner, accepted project members, or assigned student
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
    OR assigned_to IN (
        SELECT id FROM public.students WHERE user_id = auth.uid()
    )
)
WITH CHECK (
    project_id IN (
        SELECT id FROM public.projects
        WHERE owner_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
    )
    OR project_id IN (
        SELECT project_id FROM public.project_members
        WHERE student_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
    )
    OR assigned_to IN (
        SELECT id FROM public.students WHERE user_id = auth.uid()
    )
);

-- Policy 8: DELETE - Allowed to project owner and accepted project members
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

-- ==============================================================================
-- 3. Policies for public.recommendation_feedback (3 policies)
-- ==============================================================================

-- Policy 9: SELECT - Allowed to project owner and accepted project members
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

-- Policy 10: INSERT - Allowed to feedback author who is project owner or accepted project member
CREATE POLICY "recommendation_feedback_insert_policy" ON public.recommendation_feedback
FOR INSERT TO authenticated
WITH CHECK (
    student_id IN (
        SELECT id FROM public.students WHERE user_id = auth.uid()
    )
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

-- Policy 11: UPDATE - Allowed to feedback author only
CREATE POLICY "recommendation_feedback_update_policy" ON public.recommendation_feedback
FOR UPDATE TO authenticated
USING (
    student_id IN (
        SELECT id FROM public.students WHERE user_id = auth.uid()
    )
)
WITH CHECK (
    student_id IN (
        SELECT id FROM public.students WHERE user_id = auth.uid()
    )
);
