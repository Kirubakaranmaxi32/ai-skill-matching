-- ==============================================================================
-- AI Skill Matching: Database Schema (Phase 2)
-- PostgreSQL / Supabase Compatible
-- ==============================================================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Departments Table
CREATE TABLE IF NOT EXISTS public.departments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(150) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 2. Students Table (Extends Supabase auth.users)
CREATE TABLE IF NOT EXISTS public.students (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name VARCHAR(150) NOT NULL,
    email VARCHAR(255) NOT NULL,
    department_id UUID REFERENCES public.departments(id) ON DELETE SET NULL,
    year SMALLINT CHECK (year BETWEEN 1 AND 5),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_students_user_id UNIQUE (user_id),
    CONSTRAINT uq_students_email UNIQUE (email)
);

-- 3. Skills Taxonomy Table
CREATE TABLE IF NOT EXISTS public.skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    category VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 4. Student Skills Association Table
CREATE TABLE IF NOT EXISTS public.student_skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES public.students(id) ON DELETE CASCADE,
    skill_id UUID NOT NULL REFERENCES public.skills(id) ON DELETE RESTRICT,
    proficiency_level SMALLINT NOT NULL CHECK (proficiency_level BETWEEN 1 AND 4), -- 1=Beginner, 2=Intermediate, 3=Advanced, 4=Expert
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_student_skill UNIQUE (student_id, skill_id)
);

-- 5. Interests Taxonomy Table
CREATE TABLE IF NOT EXISTS public.interests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 6. Student Interests Association Table
CREATE TABLE IF NOT EXISTS public.student_interests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES public.students(id) ON DELETE CASCADE,
    interest_id UUID NOT NULL REFERENCES public.interests(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_student_interest UNIQUE (student_id, interest_id)
);

-- 7. Student Certifications Table
CREATE TABLE IF NOT EXISTS public.student_certifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES public.students(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    issuer VARCHAR(150) NOT NULL,
    issue_date DATE NOT NULL,
    credential_url VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 8. Student Previous Projects Table
CREATE TABLE IF NOT EXISTS public.student_previous_projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES public.students(id) ON DELETE CASCADE,
    title VARCHAR(150) NOT NULL,
    description TEXT,
    technologies TEXT[],
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_students_user_id ON public.students(user_id);
CREATE INDEX IF NOT EXISTS idx_students_dept ON public.students(department_id);
CREATE INDEX IF NOT EXISTS idx_student_skills_student ON public.student_skills(student_id);
CREATE INDEX IF NOT EXISTS idx_student_skills_skill ON public.student_skills(skill_id);
CREATE INDEX IF NOT EXISTS idx_student_interests_student ON public.student_interests(student_id);

-- ==============================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ==============================================================================

-- Enable RLS on all tables
ALTER TABLE public.departments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.students ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.skills ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.student_skills ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.interests ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.student_interests ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.student_certifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.student_previous_projects ENABLE ROW LEVEL SECURITY;

-- 1. Departments: Everyone can read; only service role / admin can mutate
CREATE POLICY "Allow public read on departments" 
ON public.departments FOR SELECT TO authenticated, anon USING (true);

-- 2. Skills: Everyone can read; only service role / admin can mutate
CREATE POLICY "Allow public read on skills" 
ON public.skills FOR SELECT TO authenticated, anon USING (true);

-- 3. Interests: Everyone can read; only service role / admin can mutate
CREATE POLICY "Allow public read on interests" 
ON public.interests FOR SELECT TO authenticated, anon USING (true);

-- 4. Students: Authenticated students can view profiles, mutate only their own
CREATE POLICY "Students can view all student basic profiles" 
ON public.students FOR SELECT TO authenticated USING (true);

CREATE POLICY "Students can insert their own profile" 
ON public.students FOR INSERT TO authenticated 
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Students can update only their own profile" 
ON public.students FOR UPDATE TO authenticated 
USING (auth.uid() = user_id) 
WITH CHECK (auth.uid() = user_id);

-- 5. Student Skills: Students can view skills, mutate only their own
CREATE POLICY "Authenticated users can view student skills" 
ON public.student_skills FOR SELECT TO authenticated USING (true);

CREATE POLICY "Students can insert their own skills" 
ON public.student_skills FOR INSERT TO authenticated 
WITH CHECK (
    student_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
);

CREATE POLICY "Students can update their own skills" 
ON public.student_skills FOR UPDATE TO authenticated 
USING (
    student_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
);

CREATE POLICY "Students can delete their own skills" 
ON public.student_skills FOR DELETE TO authenticated 
USING (
    student_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
);

-- 6. Student Interests: Students can view and mutate only their own
CREATE POLICY "Authenticated users can view student interests" 
ON public.student_interests FOR SELECT TO authenticated USING (true);

CREATE POLICY "Students can manage their own interests" 
ON public.student_interests FOR ALL TO authenticated 
USING (
    student_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
)
WITH CHECK (
    student_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
);

-- 7. Student Certifications: Read authenticated, mutate owner only
CREATE POLICY "Authenticated users can view student certifications" 
ON public.student_certifications FOR SELECT TO authenticated USING (true);

CREATE POLICY "Students can manage their own certifications" 
ON public.student_certifications FOR ALL TO authenticated 
USING (
    student_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
)
WITH CHECK (
    student_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
);

-- 8. Student Previous Projects: Read authenticated, mutate owner only
CREATE POLICY "Authenticated users can view student previous projects" 
ON public.student_previous_projects FOR SELECT TO authenticated USING (true);

CREATE POLICY "Students can manage their own previous projects" 
ON public.student_previous_projects FOR ALL TO authenticated 
USING (
    student_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
)
WITH CHECK (
    student_id IN (SELECT id FROM public.students WHERE user_id = auth.uid())
);
