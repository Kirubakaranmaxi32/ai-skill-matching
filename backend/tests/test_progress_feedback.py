"""
Phase 14: Project Progress & Collaboration Feedback Backend Tests
================================================================
Comprehensive test suite verifying:
- Unauthenticated access control (401)
- Non-member access control (403)
- Task management (creation, assignment, status transition, completion timestamp, deletion)
- Milestone & progress checkpoints (creation, update, overview percentage calculation)
- Collaboration feedback submission & aggregate metrics (average rating, skills alignment)
- Duplicate feedback prevention (409 Conflict)
- Isolated Demo Mode execution with zero database mutation
"""

import pytest
import jwt
import uuid
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings
from app.services.db_adapter import reset_in_memory_db, db
from app.services.progress_service import reset_demo_progress_and_tasks
from app.services.feedback_service import reset_demo_feedback
from app.services.invitation_service import reset_demo_invitations

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
    reset_demo_progress_and_tasks()
    reset_demo_feedback()
    reset_demo_invitations()
    yield
    settings.SUPABASE_JWT_SECRET = original_secret
    reset_in_memory_db()
    reset_demo_progress_and_tasks()
    reset_demo_feedback()
    reset_demo_invitations()


@pytest.mark.asyncio
async def test_unauthenticated_progress_and_feedback():
    """All progress, task, and feedback endpoints require authentication (401)."""
    transport = ASGITransport(app=app)
    fake_proj_id = str(uuid.uuid4())
    fake_task_id = str(uuid.uuid4())
    fake_prog_id = str(uuid.uuid4())

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        endpoints = [
            ("GET", f"/api/v1/projects/{fake_proj_id}/progress", None),
            ("POST", f"/api/v1/projects/{fake_proj_id}/progress", {"title": "Milestone", "progress_percentage": 50}),
            ("PATCH", f"/api/v1/projects/{fake_proj_id}/progress/{fake_prog_id}", {"title": "Update"}),
            ("DELETE", f"/api/v1/projects/{fake_proj_id}/progress/{fake_prog_id}", None),
            ("GET", f"/api/v1/projects/{fake_proj_id}/tasks", None),
            ("POST", f"/api/v1/projects/{fake_proj_id}/tasks", {"title": "Task 1"}),
            ("PATCH", f"/api/v1/projects/{fake_proj_id}/tasks/{fake_task_id}", {"title": "Task Update"}),
            ("DELETE", f"/api/v1/projects/{fake_proj_id}/tasks/{fake_task_id}", None),
            ("GET", f"/api/v1/projects/{fake_proj_id}/feedback", None),
            ("POST", f"/api/v1/projects/{fake_proj_id}/feedback", {"rating": 5}),
        ]
        for method, endpoint, body in endpoints:
            if method == "GET":
                res = await client.get(endpoint)
            elif method == "POST":
                res = await client.post(endpoint, json=body or {})
            elif method == "PATCH":
                res = await client.patch(endpoint, json=body or {})
            elif method == "DELETE":
                res = await client.delete(endpoint)
            assert res.status_code == 401, f"{method} {endpoint} returned {res.status_code} instead of 401"


@pytest.mark.asyncio
async def test_non_member_forbidden():
    """Students who are not project owners or accepted team members are forbidden (403)."""
    transport = ASGITransport(app=app)
    owner_user_id = str(uuid.uuid4())
    outsider_user_id = str(uuid.uuid4())

    owner_headers = {"Authorization": f"Bearer {create_test_jwt(owner_user_id, 'owner@college.edu')}"}
    outsider_headers = {"Authorization": f"Bearer {create_test_jwt(outsider_user_id, 'outsider@college.edu')}"}

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create owner project
        res_p = await client.post(
            "/api/v1/projects",
            json={"title": "Team AI", "description": "AI research"},
            headers=owner_headers,
        )
        assert res_p.status_code == 201
        project_id = res_p.json()["id"]

        # Outsider tries to access progress overview
        res = await client.get(f"/api/v1/projects/{project_id}/progress", headers=outsider_headers)
        assert res.status_code == 403

        # Outsider tries to access tasks
        res = await client.get(f"/api/v1/projects/{project_id}/tasks", headers=outsider_headers)
        assert res.status_code == 403

        # Outsider tries to create task
        res = await client.post(
            f"/api/v1/projects/{project_id}/tasks",
            json={"title": "Unauthorized Task"},
            headers=outsider_headers,
        )
        assert res.status_code == 403

        # Outsider tries to submit feedback
        res = await client.post(
            f"/api/v1/projects/{project_id}/feedback",
            json={"rating": 5, "feedback_text": "Great"},
            headers=outsider_headers,
        )
        assert res.status_code == 403


@pytest.mark.asyncio
async def test_tasks_and_progress_lifecycle():
    """Verify full task creation, assignment to member, completion, and progress overview calculation."""
    transport = ASGITransport(app=app)
    owner_user_id = str(uuid.uuid4())
    member_user_id = str(uuid.uuid4())

    owner_headers = {"Authorization": f"Bearer {create_test_jwt(owner_user_id, 'owner@college.edu')}"}
    member_headers = {"Authorization": f"Bearer {create_test_jwt(member_user_id, 'member@college.edu')}"}

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Setup member profile
        res_mem = await client.get("/api/v1/students/me", headers=member_headers)
        assert res_mem.status_code == 200
        member_student_id = res_mem.json()["id"]

        # 2. Setup project
        res_p = await client.post(
            "/api/v1/projects",
            json={"title": "Vision System", "description": "Autonomous vision"},
            headers=owner_headers,
        )
        assert res_p.status_code == 201
        project_id = res_p.json()["id"]

        # 3. Add member via voluntary invitation acceptance
        res_inv = await client.post(
            f"/api/v1/projects/{project_id}/invitations",
            json={"student_id": member_student_id},
            headers=owner_headers,
        )
        assert res_inv.status_code == 201
        inv_id = res_inv.json()["id"]

        res_acc = await client.post(f"/api/v1/invitations/{inv_id}/accept", headers=member_headers)
        assert res_acc.status_code == 200

        # 4. Owner creates task 1 assigned to member
        res_t1 = await client.post(
            f"/api/v1/projects/{project_id}/tasks",
            json={
                "title": "Train CNN Model",
                "description": "Train on custom dataset",
                "priority": "high",
                "assigned_student_id": member_student_id,
            },
            headers=owner_headers,
        )
        assert res_t1.status_code == 201
        task1 = res_t1.json()
        assert task1["status"] == "todo"
        assert task1["priority"] == "high"
        assert task1["assigned_student_id"] == member_student_id

        # 5. Member creates task 2
        res_t2 = await client.post(
            f"/api/v1/projects/{project_id}/tasks",
            json={"title": "Evaluate Metrics", "priority": "medium"},
            headers=member_headers,
        )
        assert res_t2.status_code == 201
        task2 = res_t2.json()

        # 6. Check initial overview (0% progress, 2 total tasks)
        res_ov = await client.get(f"/api/v1/projects/{project_id}/progress", headers=owner_headers)
        assert res_ov.status_code == 200
        ov = res_ov.json()
        assert ov["total_tasks"] == 2
        assert ov["completed_tasks"] == 0
        assert ov["overall_progress_percentage"] == 0

        # 7. Member updates task 1 to completed
        res_up = await client.patch(
            f"/api/v1/projects/{project_id}/tasks/{task1['id']}",
            json={"status": "completed"},
            headers=member_headers,
        )
        assert res_up.status_code == 200
        updated_t1 = res_up.json()
        assert updated_t1["status"] == "completed"
        assert updated_t1["completed_at"] is not None

        # 8. Check updated overview (1 of 2 completed => 50% overall progress)
        res_ov2 = await client.get(f"/api/v1/projects/{project_id}/progress", headers=member_headers)
        assert res_ov2.status_code == 200
        ov2 = res_ov2.json()
        assert ov2["total_tasks"] == 2
        assert ov2["completed_tasks"] == 1
        assert ov2["overall_progress_percentage"] == 50

        # 9. Create milestone progress checkpoint
        res_prog = await client.post(
            f"/api/v1/projects/{project_id}/progress",
            json={
                "title": "Alpha Release Completed",
                "description": "Core features operational",
                "progress_percentage": 50,
                "status": "on_track",
            },
            headers=owner_headers,
        )
        assert res_prog.status_code == 201
        prog_checkpoint = res_prog.json()
        assert prog_checkpoint["title"] == "Alpha Release Completed"

        # 10. Update progress checkpoint
        res_p_up = await client.patch(
            f"/api/v1/projects/{project_id}/progress/{prog_checkpoint['id']}",
            json={"progress_percentage": 60},
            headers=owner_headers,
        )
        assert res_p_up.status_code == 200
        assert res_p_up.json()["progress_percentage"] == 60

        # 11. Delete task 2 by creator
        res_del = await client.delete(
            f"/api/v1/projects/{project_id}/tasks/{task2['id']}",
            headers=member_headers,
        )
        assert res_del.status_code == 200

        # 12. Delete progress checkpoint by owner
        res_del_p = await client.delete(
            f"/api/v1/projects/{project_id}/progress/{prog_checkpoint['id']}",
            headers=owner_headers,
        )
        assert res_del_p.status_code == 200


@pytest.mark.asyncio
async def test_feedback_submission_and_summary():
    """Verify collaboration feedback submission, single-submission constraint, and summary metrics."""
    transport = ASGITransport(app=app)
    owner_user_id = str(uuid.uuid4())
    member_user_id = str(uuid.uuid4())

    owner_headers = {"Authorization": f"Bearer {create_test_jwt(owner_user_id, 'owner@college.edu')}"}
    member_headers = {"Authorization": f"Bearer {create_test_jwt(member_user_id, 'member@college.edu')}"}

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create member profile & project
        res_mem = await client.get("/api/v1/students/me", headers=member_headers)
        member_student_id = res_mem.json()["id"]

        res_p = await client.post(
            "/api/v1/projects",
            json={"title": "NLP Tool", "description": "Text analytics"},
            headers=owner_headers,
        )
        project_id = res_p.json()["id"]

        # Accept invitation
        res_inv = await client.post(
            f"/api/v1/projects/{project_id}/invitations",
            json={"student_id": member_student_id},
            headers=owner_headers,
        )
        inv_id = res_inv.json()["id"]
        await client.post(f"/api/v1/invitations/{inv_id}/accept", headers=member_headers)

        # 1. Initial feedback summary (empty)
        res_fb_init = await client.get(f"/api/v1/projects/{project_id}/feedback", headers=owner_headers)
        assert res_fb_init.status_code == 200
        fb_init = res_fb_init.json()
        assert fb_init["total_feedback_count"] == 0
        assert fb_init["average_rating"] == 0.0

        # 2. Member submits feedback
        res_fb1 = await client.post(
            f"/api/v1/projects/{project_id}/feedback",
            json={
                "rating": 5,
                "feedback_text": "Excellent team collaboration and skill alignment.",
                "collaboration_quality": "exceptional",
                "skills_aligned": True,
            },
            headers=member_headers,
        )
        assert res_fb1.status_code == 201
        data1 = res_fb1.json()
        assert data1["rating"] == 5
        assert data1["skills_aligned"] is True

        # 3. Duplicate feedback attempt by member returns 409 Conflict
        res_dup = await client.post(
            f"/api/v1/projects/{project_id}/feedback",
            json={"rating": 4, "feedback_text": "Duplicate attempt"},
            headers=member_headers,
        )
        assert res_dup.status_code == 409

        # 4. Owner submits feedback
        res_fb2 = await client.post(
            f"/api/v1/projects/{project_id}/feedback",
            json={
                "rating": 4,
                "feedback_text": "Very productive workflow and task execution.",
                "collaboration_quality": "good",
                "skills_aligned": True,
            },
            headers=owner_headers,
        )
        assert res_fb2.status_code == 201

        # 5. Check aggregate summary
        res_sum = await client.get(f"/api/v1/projects/{project_id}/feedback", headers=member_headers)
        assert res_sum.status_code == 200
        summary = res_sum.json()
        assert summary["total_feedback_count"] == 2
        assert summary["average_rating"] == 4.5
        assert summary["skills_aligned_percentage"] == 100.0
        assert len(summary["feedback_list"]) == 2


@pytest.mark.asyncio
async def test_demo_mode_progress_and_feedback():
    """Verify demo mode progress and feedback without modifying Supabase database."""
    transport = ASGITransport(app=app)
    demo_proj_id = "00000000-de00-0000-0000-000000000001"

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Unauthenticated demo progress overview
        res_demo_prog = await client.get(f"/api/v1/demo/projects/{demo_proj_id}/progress")
        assert res_demo_prog.status_code == 200
        ov = res_demo_prog.json()
        assert ov["total_tasks"] >= 3
        assert len(ov["updates"]) >= 1

        # 2. Unauthenticated demo tasks list
        res_demo_tasks = await client.get(f"/api/v1/demo/projects/{demo_proj_id}/tasks")
        assert res_demo_tasks.status_code == 200
        tasks = res_demo_tasks.json()
        assert len(tasks) >= 3

        # 3. Create demo task
        res_add_task = await client.post(
            f"/api/v1/demo/projects/{demo_proj_id}/tasks",
            json={"title": "Demo Autonomous Drone Test", "priority": "high"},
        )
        assert res_add_task.status_code == 201
        new_task = res_add_task.json()
        assert new_task["title"] == "Demo Autonomous Drone Test"

        # 4. Update demo task
        res_up_task = await client.patch(
            f"/api/v1/demo/projects/{demo_proj_id}/tasks/{new_task['id']}",
            json={"status": "completed"},
        )
        assert res_up_task.status_code == 200
        assert res_up_task.json()["status"] == "completed"

        # 5. Delete demo task
        res_del_task = await client.delete(
            f"/api/v1/demo/projects/{demo_proj_id}/tasks/{new_task['id']}"
        )
        assert res_del_task.status_code == 200

        # 6. Demo feedback summary
        res_demo_fb = await client.get(f"/api/v1/demo/projects/{demo_proj_id}/feedback")
        assert res_demo_fb.status_code == 200
        fb_sum = res_demo_fb.json()
        assert fb_sum["total_feedback_count"] >= 1
        assert fb_sum["average_rating"] >= 4.0

        # 7. Submit demo feedback
        res_add_fb = await client.post(
            f"/api/v1/demo/projects/{demo_proj_id}/feedback",
            json={"rating": 5, "feedback_text": "Great demo collaboration", "skills_aligned": True},
        )
        assert res_add_fb.status_code == 201

        # Confirm zero records were written to in-memory db table project_tasks or recommendation_feedback
        assert len(db.select_by_field("project_tasks", "project_id", demo_proj_id)) == 0
        assert len(db.select_by_field("recommendation_feedback", "project_id", demo_proj_id)) == 0
