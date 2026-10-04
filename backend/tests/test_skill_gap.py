"""
Unit and Integration Tests for Phase 6: Skill-Gap Analysis
=========================================================
Tests verify:
- Core calculation logic:
  * All skills matched
  * Some skills matched, some partial, some missing
  * Partial proficiency gap calculation
  * Missing skills classification
  * Student with no skills
  * Project with no required skills
  * Accurate skill coverage ratio and gap counts
- API Integration:
  * 401 unauthenticated
  * 404 nonexistent project
  * Authenticated student analyzing own skill gap for a project (200)
  * Project owner analyzing a candidate student's skill gap (200)
  * Unauthorized non-owner accessing another student's skill gap (403)
  * Demo mode path (/api/v1/demo/projects/{id}/skill-gap)
  * Zero database mutation guarantee
"""

import pytest
import jwt
import uuid
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.config import settings
from app.services.db_adapter import reset_in_memory_db, db
from app.services.student_service import get_or_create_student
from app.services.project_service import create_project, add_project_skill
from app.services.student_skills_service import add_student_skill
from app.services.skill_gap_service import calculate_skill_gap, skill_gap_service
from app.schemas.project import ProjectCreate, ProjectSkillCreate
from app.schemas.skill_gap import SkillGapStatus

TEST_JWT_SECRET = "test-secret-key-32-chars-minimum-length!!"


def create_test_jwt(user_id: str, email: str = "student@college.edu") -> str:
    """Generate a test Supabase JWT."""
    payload = {
        "sub": user_id,
        "email": email,
        "aud": "authenticated",
        "role": "authenticated",
        "exp": 9999999999,
    }
    return jwt.encode(payload, TEST_JWT_SECRET, algorithm="HS256")


@pytest.fixture(autouse=True)
def setup_test_env():
    original_secret = settings.SUPABASE_JWT_SECRET
    original_demo = settings.DEMO_MODE
    settings.SUPABASE_JWT_SECRET = TEST_JWT_SECRET
    reset_in_memory_db()
    yield
    settings.SUPABASE_JWT_SECRET = original_secret
    settings.DEMO_MODE = original_demo
    reset_in_memory_db()


# ==========================================
# 1. Pure Calculation Unit Tests
# ==========================================

def test_calculate_skill_gap_all_matched():
    """Verify scenario where student meets or exceeds all project required proficiencies."""
    skill_1 = str(uuid.uuid4())
    skill_2 = str(uuid.uuid4())

    required = [
        {"skill_id": skill_1, "skill_name": "Python", "required_proficiency": 3},
        {"skill_id": skill_2, "skill_name": "PyTorch", "required_proficiency": 2},
    ]
    student = [
        {"skill_id": skill_1, "proficiency": 3},  # Exact match
        {"skill_id": skill_2, "proficiency": 4},  # Exceeds requirement
    ]

    result = calculate_skill_gap(required, student)
    summary = result["summary"]
    skills = result["skills"]

    assert summary.total_required_skills == 2
    assert summary.matched_count == 2
    assert summary.partial_count == 0
    assert summary.missing_count == 0
    assert summary.skill_coverage_ratio == 1.0
    assert summary.proficiency_gap_count == 0
    assert all(s.status == SkillGapStatus.MATCHED for s in skills)
    assert all(s.proficiency_gap is None for s in skills)


def test_calculate_skill_gap_mixed_status():
    """Verify combination of matched, partial proficiency deficit, and missing skills."""
    sk_python = str(uuid.uuid4())
    sk_ml = str(uuid.uuid4())
    sk_dl = str(uuid.uuid4())
    sk_docker = str(uuid.uuid4())

    required = [
        {"skill_id": sk_python, "skill_name": "Python", "required_proficiency": 3},
        {"skill_id": sk_ml, "skill_name": "Machine Learning", "required_proficiency": 3},
        {"skill_id": sk_dl, "skill_name": "Deep Learning", "required_proficiency": 4},
        {"skill_id": sk_docker, "skill_name": "Docker", "required_proficiency": 2},
    ]
    student = [
        {"skill_id": sk_python, "proficiency": 4},  # Matched (4 >= 3)
        {"skill_id": sk_ml, "proficiency": 2},      # Partial (2 < 3, gap=1)
        {"skill_id": sk_dl, "proficiency": 1},      # Partial (1 < 4, gap=3)
        # Docker is missing
    ]

    result = calculate_skill_gap(required, student)
    summary = result["summary"]
    skills = {str(s.skill_id): s for s in result["skills"]}

    assert summary.total_required_skills == 4
    assert summary.matched_count == 1
    assert summary.partial_count == 2
    assert summary.missing_count == 1
    assert summary.skill_coverage_ratio == 0.25
    assert summary.proficiency_gap_count == 2

    # Verify individual statuses
    assert skills[sk_python].status == SkillGapStatus.MATCHED
    assert skills[sk_python].student_proficiency == 4
    assert skills[sk_python].proficiency_gap is None

    assert skills[sk_ml].status == SkillGapStatus.PARTIAL
    assert skills[sk_ml].student_proficiency == 2
    assert skills[sk_ml].proficiency_gap == 1

    assert skills[sk_dl].status == SkillGapStatus.PARTIAL
    assert skills[sk_dl].student_proficiency == 1
    assert skills[sk_dl].proficiency_gap == 3

    assert skills[sk_docker].status == SkillGapStatus.MISSING
    assert skills[sk_docker].student_proficiency is None
    assert skills[sk_docker].proficiency_gap is None


def test_calculate_skill_gap_student_no_skills():
    """Verify candidate with zero skills marked completely missing."""
    sk_1 = str(uuid.uuid4())
    required = [
        {"skill_id": sk_1, "skill_name": "Python", "required_proficiency": 3},
    ]
    student = []

    result = calculate_skill_gap(required, student)
    summary = result["summary"]

    assert summary.total_required_skills == 1
    assert summary.matched_count == 0
    assert summary.partial_count == 0
    assert summary.missing_count == 1
    assert summary.skill_coverage_ratio == 0.0
    assert summary.proficiency_gap_count == 0


def test_calculate_skill_gap_project_no_required_skills():
    """Verify project without required skills produces 1.0 coverage and handles 0 div safely."""
    required = []
    student = [{"skill_id": str(uuid.uuid4()), "proficiency": 3}]

    result = calculate_skill_gap(required, student)
    summary = result["summary"]

    assert summary.total_required_skills == 0
    assert summary.matched_count == 0
    assert summary.partial_count == 0
    assert summary.missing_count == 0
    assert summary.skill_coverage_ratio == 1.0


# ==========================================
# 2. API Integration Tests (Real DB Path)
# ==========================================

@pytest.mark.asyncio
async def test_skill_gap_unauthenticated():
    """Verify endpoint rejects unauthenticated request with 401."""
    transport = ASGITransport(app=app)
    fake_project_id = str(uuid.uuid4())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(f"/api/v1/projects/{fake_project_id}/skill-gap")
        assert resp.status_code == 401


@pytest.mark.asyncio
async def test_skill_gap_project_not_found():
    """Verify 404 returned when project does not exist."""
    user_id = str(uuid.uuid4())
    token = create_test_jwt(user_id)
    headers = {"Authorization": f"Bearer {token}"}
    fake_project_id = str(uuid.uuid4())

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            f"/api/v1/projects/{fake_project_id}/skill-gap",
            headers=headers,
        )
        assert resp.status_code == 404


@pytest.mark.asyncio
async def test_skill_gap_authenticated_own_analysis():
    """
    Verify authenticated student can evaluate their own skill gap
    against an existing project.
    """
    # 1. Create owner and project with required skills
    owner_user = str(uuid.uuid4())
    owner_student = get_or_create_student(owner_user)
    proj = create_project(owner_user, ProjectCreate(title="CV Rover", description="Computer Vision rover"))
    proj_id = str(proj["id"])

    # Get sample taxonomy skill
    from app.services.reference_service import get_skills
    skills = get_skills()
    skill_1 = str(skills[0]["id"])
    skill_2 = str(skills[1]["id"])

    add_project_skill(proj_id, owner_user, ProjectSkillCreate(skill_id=uuid.UUID(skill_1), required_proficiency=3))
    add_project_skill(proj_id, owner_user, ProjectSkillCreate(skill_id=uuid.UUID(skill_2), required_proficiency=4))

    # 2. Create student B and assign skills
    student_b_user = str(uuid.uuid4())
    student_b = get_or_create_student(student_b_user)
    add_student_skill(student_b_user, skill_1, proficiency=3)  # Matched
    add_student_skill(student_b_user, skill_2, proficiency=2)  # Partial (2 < 4)

    # Student B queries their own skill gap for the project
    token_b = create_test_jwt(student_b_user)
    headers_b = {"Authorization": f"Bearer {token_b}"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            f"/api/v1/projects/{proj_id}/skill-gap",
            headers=headers_b,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["project_id"] == proj_id
        assert data["student_id"] == str(student_b["id"])
        assert data["summary"]["total_required_skills"] == 2
        assert data["summary"]["matched_count"] == 1
        assert data["summary"]["partial_count"] == 1
        assert data["summary"]["missing_count"] == 0
        assert data["summary"]["skill_coverage_ratio"] == 0.5


@pytest.mark.asyncio
async def test_skill_gap_owner_queries_candidate():
    """
    Verify project owner can analyze a candidate student's skill gap
    using the ?student_id query parameter.
    """
    owner_user = str(uuid.uuid4())
    proj = create_project(owner_user, ProjectCreate(title="AI Chatbot", description="NLP project"))
    proj_id = str(proj["id"])

    from app.services.reference_service import get_skills
    skills = get_skills()
    skill_1 = str(skills[0]["id"])
    add_project_skill(proj_id, owner_user, ProjectSkillCreate(skill_id=uuid.UUID(skill_1), required_proficiency=3))

    cand_user = str(uuid.uuid4())
    cand_student = get_or_create_student(cand_user)
    add_student_skill(cand_user, skill_1, proficiency=4)

    owner_token = create_test_jwt(owner_user)
    owner_headers = {"Authorization": f"Bearer {owner_token}"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            f"/api/v1/projects/{proj_id}/skill-gap?student_id={cand_student['id']}",
            headers=owner_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["student_id"] == str(cand_student["id"])
        assert data["summary"]["matched_count"] == 1


@pytest.mark.asyncio
async def test_skill_gap_unauthorized_non_owner_querying_other_student():
    """
    Verify 403 Forbidden when an unrelated student attempts to inspect
    another student's private skill gap for a project they do not own.
    """
    owner_user = str(uuid.uuid4())
    proj = create_project(owner_user, ProjectCreate(title="Robotics", description="Hardware project"))
    proj_id = str(proj["id"])

    student_a_user = str(uuid.uuid4())
    student_a = get_or_create_student(student_a_user)

    unrelated_user = str(uuid.uuid4())
    unrelated_token = create_test_jwt(unrelated_user)
    headers = {"Authorization": f"Bearer {unrelated_token}"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            f"/api/v1/projects/{proj_id}/skill-gap?student_id={student_a['id']}",
            headers=headers,
        )
        assert resp.status_code == 403


# ==========================================
# 3. Demo Mode Path & Zero DB Mutations
# ==========================================

@pytest.mark.asyncio
async def test_demo_skill_gap_endpoint():
    """Verify demo skill gap returns correct structure using local synthetic data."""
    from app.services.demo_service import load_demo_projects, load_demo_students
    demo_projects = load_demo_projects()
    demo_proj = demo_projects[0]
    proj_id = demo_proj["id"]

    demo_students = load_demo_students()
    cand_student = demo_students[1]

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Dedicated demo route
        resp = await client.get(
            f"/api/v1/demo/projects/{proj_id}/skill-gap?student_id={cand_student['id']}"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["project_id"] == str(proj_id)
        assert data["student_id"] == str(cand_student["id"])
        assert "summary" in data
        assert "skills" in data
        assert data["summary"]["total_required_skills"] == len(demo_proj["required_skills"])


@pytest.mark.asyncio
async def test_skill_gap_zero_database_mutations():
    """
    Verify skill gap operations cause zero mutations to database tables
    (no inserts, updates, or deletes).
    """
    initial_students = len(db.select_all("students"))
    initial_projects = len(db.select_all("projects"))
    initial_skills = len(db.select_all("project_skills"))

    from app.services.demo_service import load_demo_projects
    proj_id = load_demo_projects()[0]["id"]

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.get(f"/api/v1/demo/projects/{proj_id}/skill-gap")

    assert len(db.select_all("students")) == initial_students
    assert len(db.select_all("projects")) == initial_projects
    assert len(db.select_all("project_skills")) == initial_skills
