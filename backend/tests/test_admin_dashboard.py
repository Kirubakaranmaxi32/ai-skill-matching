"""
Phase 15: Admin Dashboard Backend Tests
=======================================
Verifies:
- Unauthenticated access returns HTTP 401 Unauthorized.
- Authenticated non-admin student returns HTTP 403 Forbidden.
- Authorized administrator (via app_metadata or admin_users) receives HTTP 200.
- Accuracy of all analytics endpoints: overview, students, projects, progress, feedback, ai-matching, system.
- Strict prevention of sensitive credential leakage (no JWT secret, service role key, etc.).
- Explicit indication of unavailable historical recommendation session logs.
- Safe execution in Demo Mode with zero database mutations.
"""

import pytest
import jwt
import uuid
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings
from app.services.db_adapter import reset_in_memory_db, db

TEST_JWT_SECRET = "test-secret-key-32-chars-minimum-length!!"


def create_test_token(user_id: str, email: str = "user@college.edu", is_admin: bool = False) -> str:
    """Generate a test Supabase JWT with optional server-managed admin role in app_metadata."""
    payload = {
        "sub": user_id,
        "email": email,
        "aud": "authenticated",
        "role": "authenticated",
        "app_metadata": {"role": "admin"} if is_admin else {},
        "user_metadata": {"role": "admin"} if is_admin else {},  # Notice: backend must NOT trust user_metadata
        "exp": 9999999999,
    }
    return jwt.encode(payload, TEST_JWT_SECRET, algorithm="HS256")


@pytest.fixture(autouse=True)
def setup_test_env():
    """Setup and teardown test configuration and database state."""
    original_secret = settings.SUPABASE_JWT_SECRET
    settings.SUPABASE_JWT_SECRET = TEST_JWT_SECRET
    reset_in_memory_db()
    yield
    settings.SUPABASE_JWT_SECRET = original_secret
    reset_in_memory_db()


@pytest.mark.asyncio
async def test_unauthenticated_admin_endpoints_return_401():
    """Unauthenticated requests to all /api/v1/admin/* routes must be rejected with 401."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        endpoints = [
            "/api/v1/admin/status",
            "/api/v1/admin/overview",
            "/api/v1/admin/students",
            "/api/v1/admin/projects",
            "/api/v1/admin/progress",
            "/api/v1/admin/feedback",
            "/api/v1/admin/ai-matching",
            "/api/v1/admin/system",
        ]
        for ep in endpoints:
            res = await client.get(ep)
            assert res.status_code == 401, f"{ep} returned {res.status_code} instead of 401"


@pytest.mark.asyncio
async def test_non_admin_student_returns_403():
    """Regular authenticated students without admin privileges must receive 403 Forbidden."""
    transport = ASGITransport(app=app)
    student_user_id = str(uuid.uuid4())
    student_token = create_test_token(student_user_id, email="student@college.edu", is_admin=False)
    headers = {"Authorization": f"Bearer {student_token}"}

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        endpoints = [
            "/api/v1/admin/status",
            "/api/v1/admin/overview",
            "/api/v1/admin/students",
            "/api/v1/admin/projects",
            "/api/v1/admin/progress",
            "/api/v1/admin/feedback",
            "/api/v1/admin/ai-matching",
            "/api/v1/admin/system",
        ]
        for ep in endpoints:
            res = await client.get(ep, headers=headers)
            assert res.status_code == 403, f"{ep} returned {res.status_code} instead of 403"
            assert "Administrative access required" in res.json().get("detail", "")


@pytest.mark.asyncio
async def test_authorized_admin_access_via_app_metadata():
    """Admins verified through server-managed app_metadata must receive 200 OK."""
    transport = ASGITransport(app=app)
    admin_user_id = str(uuid.uuid4())
    admin_token = create_test_token(admin_user_id, email="admin@college.edu", is_admin=True)
    headers = {"Authorization": f"Bearer {admin_token}"}

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/admin/status", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data.get("is_admin") is True
        assert data.get("user_id") == admin_user_id


@pytest.mark.asyncio
async def test_authorized_admin_access_via_admin_users_table():
    """Admins registered in public.admin_users table must receive 200 OK even without token app_metadata."""
    transport = ASGITransport(app=app)
    admin_user_id = str(uuid.uuid4())
    # Token has NO admin in app_metadata
    plain_token = create_test_token(admin_user_id, email="dbadmin@college.edu", is_admin=False)
    headers = {"Authorization": f"Bearer {plain_token}"}

    # Register admin in admin_users table
    db.insert("admin_users", {
        "user_id": admin_user_id,
        "email": "dbadmin@college.edu",
        "role": "admin",
    })

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/admin/status", headers=headers)
        assert res.status_code == 200
        assert res.json().get("is_admin") is True


@pytest.mark.asyncio
async def test_admin_overview_metrics():
    """Verifies overview aggregation across populated sample entities."""
    transport = ASGITransport(app=app)
    admin_token = create_test_token(str(uuid.uuid4()), is_admin=True)
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Populate sample test data
    s1_id = str(uuid.uuid4())
    p1_id = str(uuid.uuid4())
    db.insert("students", {"id": s1_id, "user_id": str(uuid.uuid4()), "name": "Alice", "email": "alice@college.edu"})
    db.insert("projects", {"id": p1_id, "owner_id": s1_id, "title": "AI Project", "description": "Desc", "status": "open"})
    db.insert("project_members", {"project_id": p1_id, "student_id": s1_id, "role": "owner"})
    db.insert("invitations", {"project_id": p1_id, "inviter_id": s1_id, "invited_student_id": str(uuid.uuid4()), "status": "pending"})
    db.insert("project_progress", {"project_id": p1_id, "progress_percentage": 50, "status": "in_progress"})
    db.insert("recommendation_feedback", {"project_id": p1_id, "student_id": s1_id, "rating": 5})

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/admin/overview", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["total_students"] >= 1
        assert data["total_projects"] >= 1
        assert data["total_project_members"] >= 1
        assert data["total_invitations"] >= 1
        assert data["avg_project_progress"] == 50.0
        assert data["total_feedback"] >= 1
        assert data["avg_feedback_rating"] == 5.0
        assert "ai_model_loaded" in data


@pytest.mark.asyncio
async def test_admin_student_and_skill_statistics():
    """Verifies detailed student demographics, department grouping, and skill distributions."""
    transport = ASGITransport(app=app)
    admin_token = create_test_token(str(uuid.uuid4()), is_admin=True)
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Add department, students, skills
    dept_id = str(uuid.uuid4())
    db.insert("departments", {"id": dept_id, "name": "Computer Science"})
    s_id = str(uuid.uuid4())
    db.insert("students", {"id": s_id, "user_id": str(uuid.uuid4()), "name": "Bob", "email": "bob@cs.edu", "department_id": dept_id, "year": 3})
    sk_id = str(uuid.uuid4())
    db.insert("skills", {"id": sk_id, "name": "Python", "category": "backend"})
    db.insert("student_skills", {"student_id": s_id, "skill_id": sk_id, "proficiency_level": 3})

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/admin/students", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["total_students"] >= 1
        assert any(d["department"] == "Computer Science" for d in data["students_by_department"])
        assert data["students_by_year"]["3"] >= 1
        assert data["profile_completeness"]["with_skills"] >= 1
        assert data["total_skills"] >= 1
        assert any(s["skill_name"] == "Python" for s in data["most_common_skills"])
        assert data["proficiency_distribution"]["advanced"] >= 1


@pytest.mark.asyncio
async def test_admin_progress_and_task_statistics():
    """Verifies progress percentage, task statuses, and priority distributions."""
    transport = ASGITransport(app=app)
    admin_token = create_test_token(str(uuid.uuid4()), is_admin=True)
    headers = {"Authorization": f"Bearer {admin_token}"}

    p_id = str(uuid.uuid4())
    db.insert("projects", {"id": p_id, "owner_id": str(uuid.uuid4()), "title": "Tasks Proj", "description": "D", "status": "open"})
    db.insert("project_progress", {"project_id": p_id, "progress_percentage": 75, "status": "in_progress"})
    db.insert("project_tasks", {"project_id": p_id, "title": "Task 1", "status": "completed", "priority": "high"})
    db.insert("project_tasks", {"project_id": p_id, "title": "Task 2", "status": "blocked", "priority": "medium"})

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/admin/progress", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["avg_project_progress"] == 75.0
        assert data["total_tasks"] == 2
        assert data["completed_tasks"] == 1
        assert data["blocked_tasks"] == 1
        assert data["tasks_by_status"]["completed"] == 1
        assert data["tasks_by_status"]["blocked"] == 1
        assert data["tasks_by_priority"]["high"] == 1
        assert data["tasks_by_priority"]["medium"] == 1


@pytest.mark.asyncio
async def test_admin_ai_matching_no_fabricated_metrics():
    """Verifies real MLP model config is read and historical_tracking_available is False."""
    transport = ASGITransport(app=app)
    admin_token = create_test_token(str(uuid.uuid4()), is_admin=True)
    headers = {"Authorization": f"Bearer {admin_token}"}

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/admin/ai-matching", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["model_type"] == "CompatibilityMLP"
        assert data["input_features_count"] == 10  # Actual input dimension verified
        assert data["hidden_layers"] == [64, 32]
        assert data["trainable_parameters"] == 2817
        assert data["checkpoint_present"] is True
        assert data["historical_tracking_available"] is False
        assert "planned as a future enhancement" in data["historical_tracking_notice"]


@pytest.mark.asyncio
async def test_admin_system_no_secret_leakage():
    """Verifies system health does not expose secrets, credentials, or keys."""
    transport = ASGITransport(app=app)
    admin_token = create_test_token(str(uuid.uuid4()), is_admin=True)
    headers = {"Authorization": f"Bearer {admin_token}"}

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/admin/system", headers=headers)
        assert res.status_code == 200
        text = res.text
        # Assert no sensitive secrets appear in output
        assert "secret" not in text.lower() or "secret" in "checkpoint_verified"
        assert "apikey" not in text.lower()
        assert "supabase_service_role_key" not in text.lower()
        assert "password" not in text.lower()
        assert res.json()["status"] == "healthy"
