-- ==============================================================================
-- AI Skill Matching: Database Migration (Phase 13)
-- Schema: Project Team Invitations & Voluntary Team Formation
-- Target: PostgreSQL (Supabase Compatible)
-- ==============================================================================
--
-- Objective:
-- Implement matching and voluntary team formation.
-- Provides structured, status-constrained invitations for project owners to invite
-- recommended candidate students, and for invited students to accept or reject.
--
-- Security:
-- Row-Level Security (RLS) is enabled.
-- Authenticated users can only see their own received or sent invitations.
-- Anonymous access is strictly prohibited (no SELECT/INSERT/UPDATE/DELETE for anon).
-- Only project owners can send invitations for projects they own.
-- Only invited candidates can accept or reject invitations addressed to them.
-- Only project owners can cancel pending invitations for their projects.
-- State transitions and column immutability are strictly enforced via RLS and trigger.
-- ==============================================================================

-- 1. Invitations Table
CREATE TABLE IF NOT EXISTS public.invitations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    inviter_id UUID NOT NULL REFERENCES public.students(id) ON DELETE CASCADE,
    invited_student_id UUID NOT NULL REFERENCES public.students(id) ON DELETE CASCADE,
    status VARCHAR(30) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    responded_at TIMESTAMPTZ,
    CONSTRAINT chk_invitations_status_valid CHECK (status IN ('pending', 'accepted', 'rejected', 'cancelled')),
    CONSTRAINT chk_invitations_not_self CHECK (inviter_id <> invited_student_id)
);

-- 2. Partial Unique Index: Prevent duplicate active pending invitations
CREATE UNIQUE INDEX IF NOT EXISTS uq_active_pending_invitation
ON public.invitations (project_id, invited_student_id)
WHERE status = 'pending';

-- 3. Query Indexes
CREATE INDEX IF NOT EXISTS idx_invitations_project_id ON public.invitations(project_id);
CREATE INDEX IF NOT EXISTS idx_invitations_inviter_id ON public.invitations(inviter_id);
CREATE INDEX IF NOT EXISTS idx_invitations_invited_student_id ON public.invitations(invited_student_id);
CREATE INDEX IF NOT EXISTS idx_invitations_status ON public.invitations(status);
CREATE INDEX IF NOT EXISTS idx_invitations_created_at ON public.invitations(created_at DESC);

-- 4. Triggers
-- A. Update safety & immutability trigger
CREATE OR REPLACE FUNCTION public.handle_invitation_update_safety()
RETURNS TRIGGER AS $$
BEGIN
    -- Prevent modification of immutable columns
    IF NEW.id <> OLD.id THEN
        RAISE EXCEPTION 'Cannot modify invitation id';
    END IF;
    IF NEW.project_id <> OLD.project_id THEN
        RAISE EXCEPTION 'Cannot modify invitation project_id';
    END IF;
    IF NEW.inviter_id <> OLD.inviter_id THEN
        RAISE EXCEPTION 'Cannot modify invitation inviter_id';
    END IF;
    IF NEW.invited_student_id <> OLD.invited_student_id THEN
        RAISE EXCEPTION 'Cannot modify invitation invited_student_id';
    END IF;
    IF NEW.created_at <> OLD.created_at THEN
        RAISE EXCEPTION 'Cannot modify invitation created_at';
    END IF;

    -- Only pending invitations can be transitioned
    IF OLD.status <> 'pending' THEN
        RAISE EXCEPTION 'Cannot update an invitation that is already in status %', OLD.status;
    END IF;

    -- Automatically record responded_at timestamp if not explicitly supplied
    IF NEW.status IN ('accepted', 'rejected', 'cancelled') AND NEW.responded_at IS NULL THEN
        NEW.responded_at = CURRENT_TIMESTAMP;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_invitations_safety ON public.invitations;
CREATE TRIGGER trg_invitations_safety
BEFORE UPDATE ON public.invitations
FOR EACH ROW EXECUTE FUNCTION public.handle_invitation_update_safety();

-- B. Automatic updated_at trigger
DROP TRIGGER IF EXISTS trg_invitations_updated_at ON public.invitations;
CREATE TRIGGER trg_invitations_updated_at
BEFORE UPDATE ON public.invitations
FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

-- 5. Privileges (Strictly authenticated and service_role; NO anon grant)
GRANT SELECT, INSERT, UPDATE, DELETE ON public.invitations TO authenticated;
GRANT ALL ON public.invitations TO service_role;

-- 6. Row-Level Security (RLS)
ALTER TABLE public.invitations ENABLE ROW LEVEL SECURITY;

-- Policy: Select (invited student or project owner/inviter can view; anon cannot)
DROP POLICY IF EXISTS "invitations_select_policy" ON public.invitations;
CREATE POLICY "invitations_select_policy" ON public.invitations
FOR SELECT TO authenticated
USING (
    invited_student_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
    OR inviter_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
);

-- Policy: Insert (project owners only for their own projects)
DROP POLICY IF EXISTS "invitations_insert_policy" ON public.invitations;
CREATE POLICY "invitations_insert_policy" ON public.invitations
FOR INSERT TO authenticated
WITH CHECK (
    inviter_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
    AND project_id IN (
        SELECT id FROM public.projects
        WHERE owner_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
    )
);

-- Policy: Update - Invited Student Response (Voluntary Accept or Decline)
-- Only invited student can respond; allowed transitions: pending -> accepted OR pending -> rejected
DROP POLICY IF EXISTS "invitations_candidate_response_policy" ON public.invitations;
DROP POLICY IF EXISTS "invitations_update_policy" ON public.invitations;
CREATE POLICY "invitations_candidate_response_policy" ON public.invitations
FOR UPDATE TO authenticated
USING (
    invited_student_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
    AND status = 'pending'
)
WITH CHECK (
    invited_student_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
    AND status IN ('accepted', 'rejected')
);

-- Policy: Update - Project Owner Cancellation
-- Only project owner can cancel; allowed transition: pending -> cancelled
DROP POLICY IF EXISTS "invitations_owner_cancel_policy" ON public.invitations;
CREATE POLICY "invitations_owner_cancel_policy" ON public.invitations
FOR UPDATE TO authenticated
USING (
    inviter_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
    AND project_id IN (
        SELECT id FROM public.projects
        WHERE owner_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
    )
    AND status = 'pending'
)
WITH CHECK (
    inviter_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
    AND project_id IN (
        SELECT id FROM public.projects
        WHERE owner_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
    )
    AND status = 'cancelled'
);
