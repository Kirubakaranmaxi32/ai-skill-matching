import pytest
import jwt
import uuid
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings
from app.services.db_adapter import reset_in_memory_db

TEST_JWT_SECRET = "test-secret-key-32-chars-minimum-length!!"


def create_test_jwt(user_id: str, email: str = "student@college.edu") -> str:
    """Generate a valid test Supabase JWT."""
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
    """Setup and teardown test configuration and database state."""
    original_secret = settings.SUPABASE_JWT_SECRET
    settings.SUPABASE_JWT_SECRET = TEST_JWT_SECRET
    reset_in_memory_db()
    yield
    settings.SUPABASE_JWT_SECRET = original_secret
    reset_in_memory_db()


@pytest.mark.asyncio
async def test_unauthenticated_access():
    """All /students/me endpoints must reject unauthenticated requests with 401."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        endpoints = [
            ("GET", "/api/v1/students/me"),
            ("PUT", "/api/v1/students/me"),
            ("GET", "/api/v1/students/me/skills"),
            ("POST", "/api/v1/students/me/skills"),
            ("GET", "/api/v1/students/me/interests"),
            ("POST", "/api/v1/students/me/interests"),
            ("GET", "/api/v1/students/me/certifications"),
            ("POST", "/api/v1/students/me/certifications"),
            ("GET", "/api/v1/students/me/projects"),
            ("POST", "/api/v1/students/me/projects"),
        ]
        for method, endpoint in endpoints:
            if method == "GET":
                res = await client.get(endpoint)
            else:
                res = await client.post(endpoint, json={}) if method == "POST" else await client.put(endpoint, json={})
            assert res.status_code == 401, f"{method} {endpoint} did not return 401"


@pytest.mark.asyncio
async def test_reference_endpoints():
    """Reference endpoints should return lists of departments, skills, and interests."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Departments
        res_dept = await client.get("/api/v1/departments")
        assert res_dept.status_code == 200
        depts = res_dept.json()
        assert isinstance(depts, list)
        assert len(depts) > 0

        # Skills
        res_skills = await client.get("/api/v1/skills")
        assert res_skills.status_code == 200
        skills = res_skills.json()
        assert isinstance(skills, list)
        assert len(skills) > 0

        # Interests
        res_interests = await client.get("/api/v1/interests")
        assert res_interests.status_code == 200
        interests = res_interests.json()
        assert isinstance(interests, list)
        assert len(interests) > 0


@pytest.mark.asyncio
async def test_profile_retrieval_and_lazy_creation():
    """An authenticated student can retrieve their profile (lazily created if not exists)."""
    user_id = str(uuid.uuid4())
    token = create_test_jwt(user_id, "kiruba@college.edu")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {"Authorization": f"Bearer {token}"}
        res = await client.get("/api/v1/students/me", headers=headers)
        assert res.status_code == 200
        profile = res.json()
        assert profile["user_id"] == user_id
        assert "full_name" in profile
        assert profile["academic_year"] == 1


@pytest.mark.asyncio
async def test_profile_update():
    """An authenticated student can update their profile information."""
    user_id = str(uuid.uuid4())
    token = create_test_jwt(user_id, "student@college.edu")
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get departments to pick a valid department_id
        depts_res = await client.get("/api/v1/departments")
        dept_id = depts_res.json()[0]["id"]

        update_payload = {
            "full_name": "Kirubakaran S",
            "department_id": dept_id,
            "academic_year": 3,
        }
        put_res = await client.put("/api/v1/students/me", json=update_payload, headers=headers)
        assert put_res.status_code == 200
        updated = put_res.json()
        assert updated["full_name"] == "Kirubakaran S"
        assert updated["academic_year"] == 3
        assert updated["department_id"] == dept_id


@pytest.mark.asyncio
async def test_skills_crud():
    """Student can add, retrieve, and delete skills."""
    user_id = str(uuid.uuid4())
    token = create_test_jwt(user_id)
    headers = {"Authorization": f"Bearer {token}"}
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Get skills taxonomy to pick a valid skill
        skills_res = await client.get("/api/v1/skills")
        skill_id = skills_res.json()[0]["id"]

        # 2. Add skill (201 Created)
        create_payload = {"skill_id": skill_id, "proficiency": 3}
        post_res = await client.post("/api/v1/students/me/skills", json=create_payload, headers=headers)
        assert post_res.status_code == 201
        added_skill = post_res.json()
        assert added_skill["skill_id"] == skill_id
        assert added_skill["proficiency"] == 3

        # 3. List skills
        list_res = await client.get("/api/v1/students/me/skills", headers=headers)
        assert list_res.status_code == 200
        my_skills = list_res.json()
        assert len(my_skills) == 1
        assert my_skills[0]["skill_id"] == skill_id

        # 4. Delete skill (200 OK)
        del_res = await client.delete(f"/api/v1/students/me/skills/{skill_id}", headers=headers)
        assert del_res.status_code == 200

        # 5. Verify deletion
        list_after = await client.get("/api/v1/students/me/skills", headers=headers)
        assert len(list_after.json()) == 0


@pytest.mark.asyncio
async def test_interests_crud():
    """Student can add, list, and delete project interests."""
    user_id = str(uuid.uuid4())
    token = create_test_jwt(user_id)
    headers = {"Authorization": f"Bearer {token}"}
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Pick interest
        interests_res = await client.get("/api/v1/interests")
        interest_id = interests_res.json()[0]["id"]

        # Add interest
        post_res = await client.post(
            "/api/v1/students/me/interests",
            json={"interest_id": interest_id},
            headers=headers
        )
        assert post_res.status_code == 201

        # List interests
        list_res = await client.get("/api/v1/students/me/interests", headers=headers)
        assert len(list_res.json()) == 1

        # Delete interest
        del_res = await client.delete(f"/api/v1/students/me/interests/{interest_id}", headers=headers)
        assert del_res.status_code == 200


@pytest.mark.asyncio
async def test_certifications_crud():
    """Student can add, retrieve, and delete certifications."""
    user_id = str(uuid.uuid4())
    token = create_test_jwt(user_id)
    headers = {"Authorization": f"Bearer {token}"}
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        cert_payload = {
            "name": "AWS Certified Cloud Practitioner",
            "issuing_organization": "Amazon Web Services",
            "issue_date": "2026-05-15",
            "credential_url": "https://aws.amazon.com/verify/12345",
        }
        post_res = await client.post("/api/v1/students/me/certifications", json=cert_payload, headers=headers)
        assert post_res.status_code == 201
        cert_data = post_res.json()
        cert_id = cert_data["id"]

        # List
        list_res = await client.get("/api/v1/students/me/certifications", headers=headers)
        assert len(list_res.json()) == 1

        # Delete
        del_res = await client.delete(f"/api/v1/students/me/certifications/{cert_id}", headers=headers)
        assert del_res.status_code == 200


@pytest.mark.asyncio
async def test_previous_projects_crud():
    """Student can add, list, and delete previous projects."""
    user_id = str(uuid.uuid4())
    token = create_test_jwt(user_id)
    headers = {"Authorization": f"Bearer {token}"}
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        proj_payload = {
            "title": "Autonomous Drone Path Planner",
            "description": "Implemented A* path search with ROS2 and OpenCV.",
            "technologies": ["Python", "OpenCV", "ROS2"],
            "project_url": "https://github.com/student/drone-planner",
        }
        post_res = await client.post("/api/v1/students/me/projects", json=proj_payload, headers=headers)
        assert post_res.status_code == 201
        proj_data = post_res.json()
        proj_id = proj_data["id"]

        # List
        list_res = await client.get("/api/v1/students/me/projects", headers=headers)
        assert len(list_res.json()) == 1

        # Delete
        del_res = await client.delete(f"/api/v1/students/me/projects/{proj_id}", headers=headers)
        assert del_res.status_code == 200


@pytest.mark.asyncio
async def test_ownership_protection():
    """User B cannot delete User A's certifications or projects (returns 403 or 404)."""
    user_a = str(uuid.uuid4())
    user_b = str(uuid.uuid4())
    token_a = create_test_jwt(user_a, "user_a@college.edu")
    token_b = create_test_jwt(user_b, "user_b@college.edu")
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # User A creates a certification
        cert_payload = {
            "name": "Machine Learning Specialization",
            "issuing_organization": "DeepLearning.AI",
            "issue_date": "2026-03-01",
        }
        res_a = await client.post("/api/v1/students/me/certifications", json=cert_payload, headers=headers_a)
        cert_id = res_a.json()["id"]

        # User B attempts to delete User A's certification
        del_b_res = await client.delete(f"/api/v1/students/me/certifications/{cert_id}", headers=headers_b)
        assert del_b_res.status_code in [403, 404]

        # Verify User A's certification is still intact
        list_a = await client.get("/api/v1/students/me/certifications", headers=headers_a)
        assert len(list_a.json()) == 1
