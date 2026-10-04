import pytest
import jwt
import uuid
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings
from app.services.db_adapter import reset_in_memory_db, db

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
async def test_unauthenticated_endpoints():
    """All /projects endpoints must reject unauthenticated requests with 401."""
    transport = ASGITransport(app=app)
    fake_id = str(uuid.uuid4())
    fake_skill = str(uuid.uuid4())

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        endpoints = [
            ("POST", "/api/v1/projects", {"title": "Test", "description": "Desc"}),
            ("GET", "/api/v1/projects/me", None),
            ("GET", f"/api/v1/projects/{fake_id}", None),
            ("PUT", f"/api/v1/projects/{fake_id}", {"title": "Updated"}),
            ("POST", f"/api/v1/projects/{fake_id}/archive", None),
            ("POST", f"/api/v1/projects/{fake_id}/skills", {"skill_id": fake_skill, "required_proficiency": 2}),
            ("GET", f"/api/v1/projects/{fake_id}/skills", None),
            ("DELETE", f"/api/v1/projects/{fake_id}/skills/{fake_skill}", None),
        ]
        for method, endpoint, body in endpoints:
            if method == "GET":
                res = await client.get(endpoint)
            elif method == "POST":
                res = await client.post(endpoint, json=body or {})
            elif method == "PUT":
                res = await client.put(endpoint, json=body or {})
            elif method == "DELETE":
                res = await client.delete(endpoint)
            assert res.status_code == 401, f"{method} {endpoint} returned {res.status_code} instead of 401"


@pytest.mark.asyncio
async def test_project_creation_and_membership():
    """Authenticated user creates a project; ownership and membership are automatically assigned."""
    user_id = str(uuid.uuid4())
    token = create_test_jwt(user_id, "creator@college.edu")
    headers = {"Authorization": f"Bearer {token}"}
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create project
        create_payload = {
            "title": "Autonomous Drone Path Planner",
            "description": "Building an autonomous quadcopter path planner using ROS2 and A*.",
            "status": "open",
        }
        res = await client.post("/api/v1/projects", json=create_payload, headers=headers)
        assert res.status_code == 201
        data = res.json()
        assert data["title"] == create_payload["title"]
        assert data["description"] == create_payload["description"]
        assert data["status"] == "open"
        assert "id" in data
        assert "owner_id" in data

        project_id = data["id"]
        owner_id = data["owner_id"]

        # Verify owner membership was created
        members = db.select_by_field("project_members", "project_id", project_id)
        assert len(members) == 1
        assert members[0]["student_id"] == owner_id
        assert members[0]["role"] == "owner"


@pytest.mark.asyncio
async def test_get_my_projects():
    """Student can retrieve all projects they own, ordered newest first."""
    user_id = str(uuid.uuid4())
    token = create_test_jwt(user_id)
    headers = {"Authorization": f"Bearer {token}"}
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create project 1
        await client.post(
            "/api/v1/projects",
            json={"title": "Project Alpha", "description": "First project"},
            headers=headers,
        )
        # Create project 2
        await client.post(
            "/api/v1/projects",
            json={"title": "Project Beta", "description": "Second project"},
            headers=headers,
        )

        # List my projects
        res = await client.get("/api/v1/projects/me", headers=headers)
        assert res.status_code == 200
        my_projs = res.json()
        assert len(my_projs) == 2
        # Verify title exists
        titles = [p["title"] for p in my_projs]
        assert "Project Alpha" in titles
        assert "Project Beta" in titles


@pytest.mark.asyncio
async def test_get_project_by_id():
    """Retrieve detailed project with owner info, required skills, and members."""
    user_id = str(uuid.uuid4())
    token = create_test_jwt(user_id, "lead@college.edu")
    headers = {"Authorization": f"Bearer {token}"}
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create project
        create_res = await client.post(
            "/api/v1/projects",
            json={"title": "Deep Learning Classifier", "description": "Image segmentation with PyTorch"},
            headers=headers,
        )
        proj_id = create_res.json()["id"]

        # Add a skill to project
        skills_res = await client.get("/api/v1/skills")
        skill_id = skills_res.json()[0]["id"]
        await client.post(
            f"/api/v1/projects/{proj_id}/skills",
            json={"skill_id": skill_id, "required_proficiency": 3},
            headers=headers,
        )

        # Get project by ID
        detail_res = await client.get(f"/api/v1/projects/{proj_id}", headers=headers)
        assert detail_res.status_code == 200
        detail = detail_res.json()
        assert detail["id"] == proj_id
        assert detail["owner"] is not None
        assert detail["owner"]["user_id"] == user_id
        assert len(detail["required_skills"]) == 1
        assert detail["required_skills"][0]["skill_id"] == skill_id
        assert len(detail["members"]) == 1
        assert detail["members"][0]["role"] == "owner"


@pytest.mark.asyncio
async def test_update_own_project_and_ownership_protection():
    """Owner can update their project; another user receives 403 Forbidden."""
    user_a = str(uuid.uuid4())
    user_b = str(uuid.uuid4())
    token_a = create_test_jwt(user_a)
    token_b = create_test_jwt(user_b)
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # User A creates project
        create_res = await client.post(
            "/api/v1/projects",
            json={"title": "Original Title", "description": "Original Description"},
            headers=headers_a,
        )
        proj_id = create_res.json()["id"]

        # User B attempts to update User A's project -> 403 Forbidden
        update_b = await client.put(
            f"/api/v1/projects/{proj_id}",
            json={"title": "Hacked Title"},
            headers=headers_b,
        )
        assert update_b.status_code == 403

        # User A updates their project -> 200 OK
        update_a = await client.put(
            f"/api/v1/projects/{proj_id}",
            json={"title": "Updated Title", "status": "in_progress"},
            headers=headers_a,
        )
        assert update_a.status_code == 200
        assert update_a.json()["title"] == "Updated Title"
        assert update_a.json()["status"] == "in_progress"


@pytest.mark.asyncio
async def test_archive_project():
    """Owner can archive their project; non-owners cannot access archived project."""
    user_a = str(uuid.uuid4())
    user_b = str(uuid.uuid4())
    token_a = create_test_jwt(user_a)
    token_b = create_test_jwt(user_b)
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # User A creates project
        create_res = await client.post(
            "/api/v1/projects",
            json={"title": "Active Project", "description": "Active Description"},
            headers=headers_a,
        )
        proj_id = create_res.json()["id"]

        # User B attempts to archive User A's project -> 403
        arch_b = await client.post(f"/api/v1/projects/{proj_id}/archive", headers=headers_b)
        assert arch_b.status_code == 403

        # User A archives own project -> 200
        arch_a = await client.post(f"/api/v1/projects/{proj_id}/archive", headers=headers_a)
        assert arch_a.status_code == 200
        assert arch_a.json()["status"] == "archived"

        # User A can still retrieve their own archived project
        get_a = await client.get(f"/api/v1/projects/{proj_id}", headers=headers_a)
        assert get_a.status_code == 200

        # User B cannot view User A's archived project -> 404
        get_b = await client.get(f"/api/v1/projects/{proj_id}", headers=headers_b)
        assert get_b.status_code == 404


@pytest.mark.asyncio
async def test_project_skills_lifecycle():
    """Owner can add, view, and delete required skills; duplicates rejected with 409."""
    user_id = str(uuid.uuid4())
    token = create_test_jwt(user_id)
    headers = {"Authorization": f"Bearer {token}"}
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Create project
        create_res = await client.post(
            "/api/v1/projects",
            json={"title": "Cloud Platform", "description": "Deploying Kubernetes cluster"},
            headers=headers,
        )
        proj_id = create_res.json()["id"]

        # 2. Get available taxonomy skills
        skills_res = await client.get("/api/v1/skills")
        skill_id = skills_res.json()[0]["id"]

        # 3. Add skill (201 Created)
        add_skill_res = await client.post(
            f"/api/v1/projects/{proj_id}/skills",
            json={"skill_id": skill_id, "required_proficiency": 3},
            headers=headers,
        )
        assert add_skill_res.status_code == 201
        skill_data = add_skill_res.json()
        assert skill_data["skill_id"] == skill_id
        assert skill_data["required_proficiency"] == 3
        assert "skill_name" in skill_data

        # 4. Duplicate skill -> 409 Conflict
        dup_res = await client.post(
            f"/api/v1/projects/{proj_id}/skills",
            json={"skill_id": skill_id, "required_proficiency": 2},
            headers=headers,
        )
        assert dup_res.status_code == 409

        # 5. List project skills
        list_skills_res = await client.get(f"/api/v1/projects/{proj_id}/skills", headers=headers)
        assert list_skills_res.status_code == 200
        assert len(list_skills_res.json()) == 1

        # 6. Delete project skill
        del_res = await client.delete(f"/api/v1/projects/{proj_id}/skills/{skill_id}", headers=headers)
        assert del_res.status_code == 200

        # 7. Verify deletion
        list_after = await client.get(f"/api/v1/projects/{proj_id}/skills", headers=headers)
        assert len(list_after.json()) == 0


@pytest.mark.asyncio
async def test_validation_and_not_found_handling():
    """Verify input validation (empty fields, proficiency range, invalid status) and 404s."""
    user_id = str(uuid.uuid4())
    token = create_test_jwt(user_id)
    headers = {"Authorization": f"Bearer {token}"}
    transport = ASGITransport(app=app)
    fake_proj_id = str(uuid.uuid4())

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Empty title -> 422
        res1 = await client.post(
            "/api/v1/projects",
            json={"title": "   ", "description": "Valid description"},
            headers=headers,
        )
        assert res1.status_code == 422

        # Empty description -> 422
        res2 = await client.post(
            "/api/v1/projects",
            json={"title": "Valid title", "description": "  \n "},
            headers=headers,
        )
        assert res2.status_code == 422

        # Invalid status -> 422
        res3 = await client.post(
            "/api/v1/projects",
            json={"title": "Valid title", "description": "Valid desc", "status": "unknown_status"},
            headers=headers,
        )
        assert res3.status_code == 422

        # Nonexistent project -> 404
        res4 = await client.get(f"/api/v1/projects/{fake_proj_id}", headers=headers)
        assert res4.status_code == 404

        # Create valid project to test skill proficiency bounds
        proj_res = await client.post(
            "/api/v1/projects",
            json={"title": "Boundary Test", "description": "Testing boundary cases"},
            headers=headers,
        )
        proj_id = proj_res.json()["id"]
        skill_id = str(uuid.uuid4())

        # Proficiency > 4 -> 422
        res5 = await client.post(
            f"/api/v1/projects/{proj_id}/skills",
            json={"skill_id": skill_id, "required_proficiency": 5},
            headers=headers,
        )
        assert res5.status_code == 422

        # Proficiency < 1 -> 422
        res6 = await client.post(
            f"/api/v1/projects/{proj_id}/skills",
            json={"skill_id": skill_id, "required_proficiency": 0},
            headers=headers,
        )
        assert res6.status_code == 422
