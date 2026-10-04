-- ==============================================================================
-- AI Skill Matching: Database Migration (Phase 3)
-- Schema: Student Profiles, Departments, Skills, Interests, & Portfolio
-- Target: PostgreSQL (Supabase Compatible)
-- ==============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Function: Automatic Updated Timestamp Trigger
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ==============================================================================
-- 1. Departments (Academic Disciplines)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.departments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(150) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ==============================================================================
-- 2. Students (Profile linked to Supabase Auth)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.students (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name VARCHAR(150) NOT NULL,
    department_id UUID REFERENCES public.departments(id) ON DELETE SET NULL,
    academic_year SMALLINT CHECK (academic_year BETWEEN 1 AND 5),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_students_user_id UNIQUE (user_id)
);

CREATE TRIGGER trg_students_updated_at
BEFORE UPDATE ON public.students
FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

-- ==============================================================================
-- 3. Skills (Master Taxonomy)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    category VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ==============================================================================
-- 4. Student Skills (Proficiency ratings 1-4)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.student_skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES public.students(id) ON DELETE CASCADE,
    skill_id UUID NOT NULL REFERENCES public.skills(id) ON DELETE RESTRICT,
    proficiency SMALLINT NOT NULL CHECK (proficiency BETWEEN 1 AND 4),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_student_skills_pair UNIQUE (student_id, skill_id)
);

CREATE TRIGGER trg_student_skills_updated_at
BEFORE UPDATE ON public.student_skills
FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

-- ==============================================================================
-- 5. Interests (Project and Domain Interest Areas)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.interests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ==============================================================================
-- 6. Student Interests (Association)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.student_interests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES public.students(id) ON DELETE CASCADE,
    interest_id UUID NOT NULL REFERENCES public.interests(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_student_interests_pair UNIQUE (student_id, interest_id)
);

-- ==============================================================================
-- 7. Certifications (Student Achievements & Accreditations)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.certifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES public.students(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    issuing_organization VARCHAR(150) NOT NULL,
    issue_date DATE NOT NULL,
    credential_url VARCHAR(500),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ==============================================================================
-- 8. Previous Projects (Student Project Portfolio)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.previous_projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES public.students(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    technologies TEXT[],
    project_url VARCHAR(500),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ==============================================================================
-- Performance & Lookup Indexes
-- ==============================================================================
CREATE INDEX IF NOT EXISTS idx_students_user_id ON public.students(user_id);
CREATE INDEX IF NOT EXISTS idx_students_department_id ON public.students(department_id);
CREATE INDEX IF NOT EXISTS idx_student_skills_student_id ON public.student_skills(student_id);
CREATE INDEX IF NOT EXISTS idx_student_skills_skill_id ON public.student_skills(skill_id);
CREATE INDEX IF NOT EXISTS idx_student_interests_student_id ON public.student_interests(student_id);
CREATE INDEX IF NOT EXISTS idx_student_interests_interest_id ON public.student_interests(interest_id);
CREATE INDEX IF NOT EXISTS idx_certifications_student_id ON public.certifications(student_id);
CREATE INDEX IF NOT EXISTS idx_previous_projects_student_id ON public.previous_projects(student_id);

-- ==============================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ==============================================================================

-- Enable RLS on all 8 tables
ALTER TABLE public.departments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.students ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.skills ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.student_skills ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.interests ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.student_interests ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.certifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.previous_projects ENABLE ROW LEVEL SECURITY;

-- 1. Departments: Readable by authenticated and anonymous users
CREATE POLICY "Allow read access to departments"
ON public.departments FOR SELECT
TO authenticated, anon
USING (true);

-- 2. Skills: Readable by authenticated and anonymous users
CREATE POLICY "Allow read access to skills"
ON public.skills FOR SELECT
TO authenticated, anon
USING (true);

-- 3. Interests: Readable by authenticated and anonymous users
CREATE POLICY "Allow read access to interests"
ON public.interests FOR SELECT
TO authenticated, anon
USING (true);

-- 4. Students:
-- Authenticated users can view student profiles (needed for student discovery and team matching)
CREATE POLICY "Allow authenticated read on students"
ON public.students FOR SELECT
TO authenticated
USING (true);

-- Students can insert only their own profile linked to their authenticated user_id
CREATE POLICY "Allow individual student insert"
ON public.students FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = user_id);

-- Students can update only their own profile
CREATE POLICY "Allow individual student update"
ON public.students FOR UPDATE
TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

-- Students can delete only their own profile
CREATE POLICY "Allow individual student delete"
ON public.students FOR DELETE
TO authenticated
USING (auth.uid() = user_id);

-- 5. Student Skills:
-- Authenticated users can view student skills
CREATE POLICY "Allow authenticated read on student_skills"
ON public.student_skills FOR SELECT
TO authenticated
USING (true);

-- Students can insert their own skills
CREATE POLICY "Allow individual student skill insert"
ON public.student_skills FOR INSERT
TO authenticated
WITH CHECK (
    student_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
);

-- Students can update their own skills
CREATE POLICY "Allow individual student skill update"
ON public.student_skills FOR UPDATE
TO authenticated
USING (
    student_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
)
WITH CHECK (
    student_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
);

-- Students can delete their own skills
CREATE POLICY "Allow individual student skill delete"
ON public.student_skills FOR DELETE
TO authenticated
USING (
    student_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
);

-- 6. Student Interests:
-- Authenticated users can view student interests
CREATE POLICY "Allow authenticated read on student_interests"
ON public.student_interests FOR SELECT
TO authenticated
USING (true);

-- Students can manage (ALL) their own interests
CREATE POLICY "Allow individual student interest insert"
ON public.student_interests FOR INSERT
TO authenticated
WITH CHECK (
    student_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
);

CREATE POLICY "Allow individual student interest update"
ON public.student_interests FOR UPDATE
TO authenticated
USING (
    student_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
)
WITH CHECK (
    student_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
);

CREATE POLICY "Allow individual student interest delete"
ON public.student_interests FOR DELETE
TO authenticated
USING (
    student_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
);

-- 7. Certifications:
-- Authenticated users can view student certifications
CREATE POLICY "Allow authenticated read on certifications"
ON public.certifications FOR SELECT
TO authenticated
USING (true);

-- Students can manage their own certifications
CREATE POLICY "Allow individual student certification insert"
ON public.certifications FOR INSERT
TO authenticated
WITH CHECK (
    student_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
);

CREATE POLICY "Allow individual student certification update"
ON public.certifications FOR UPDATE
TO authenticated
USING (
    student_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
)
WITH CHECK (
    student_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
);

CREATE POLICY "Allow individual student certification delete"
ON public.certifications FOR DELETE
TO authenticated
USING (
    student_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
);

-- 8. Previous Projects:
-- Authenticated users can view previous projects
CREATE POLICY "Allow authenticated read on previous_projects"
ON public.previous_projects FOR SELECT
TO authenticated
USING (true);

-- Students can manage their own previous projects
CREATE POLICY "Allow individual student project insert"
ON public.previous_projects FOR INSERT
TO authenticated
WITH CHECK (
    student_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
);

CREATE POLICY "Allow individual student project update"
ON public.previous_projects FOR UPDATE
TO authenticated
USING (
    student_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
)
WITH CHECK (
    student_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
);

CREATE POLICY "Allow individual student project delete"
ON public.previous_projects FOR DELETE
TO authenticated
USING (
    student_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
);
