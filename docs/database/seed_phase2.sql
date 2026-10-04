-- ==============================================================================
-- AI Skill Matching: Minimal Reference Seed Data (Phase 2)
-- Minimal verified reference taxonomy for departments, skills, and interests.
-- NOTE: Real student profiles, project interactions, and ML synthetic data
-- are strictly excluded here (Synthetic data generation belongs to Phase 7).
-- ==============================================================================

-- 1. Departments Reference
INSERT INTO public.departments (name) VALUES
    ('Computer Science & Engineering'),
    ('Information Technology'),
    ('Electrical & Electronics Engineering'),
    ('Electronics & Communication Engineering'),
    ('Mechanical Engineering'),
    ('Data Science & Artificial Intelligence')
ON CONFLICT (name) DO NOTHING;

-- 2. Core Technical & Non-Technical Skills Reference
INSERT INTO public.skills (name, category) VALUES
    ('Python', 'ai_ml'),
    ('PyTorch', 'ai_ml'),
    ('TensorFlow', 'ai_ml'),
    ('Scikit-Learn', 'ai_ml'),
    ('React', 'frontend'),
    ('TypeScript', 'frontend'),
    ('Tailwind CSS', 'frontend'),
    ('FastAPI', 'backend'),
    ('Node.js', 'backend'),
    ('PostgreSQL', 'backend'),
    ('Docker', 'cloud_devops'),
    ('Git & GitHub', 'cloud_devops'),
    ('UI/UX Design (Figma)', 'design_ui_ux'),
    ('Technical Writing', 'soft_skills'),
    ('Team Leadership', 'soft_skills')
ON CONFLICT (name) DO NOTHING;

-- 3. Core Project Interests Reference
INSERT INTO public.interests (name) VALUES
    ('Artificial Intelligence & Deep Learning'),
    ('Web Development & Cloud Computing'),
    ('Robotics & Autonomous Systems'),
    ('Cybersecurity & Cryptography'),
    ('Data Science & Predictive Analytics'),
    ('Mobile Applications & IoT')
ON CONFLICT (name) DO NOTHING;
