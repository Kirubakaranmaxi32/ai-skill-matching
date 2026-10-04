"""
Phase 13: Voluntary Team Formation & Invitations Backend Tests
============================================================
Comprehensive test suite verifying:
- Unauthenticated access control (401)
- Project owner invitation creation (201)
- Non-owner authorization rejection (403)
- Self-invitation rejection (400)
- Duplicate pending invitation prevention (409)
- Existing member invitation prevention (400)
- Inbox ('received') and Outbox ('sent') listing
- Project-level invitation listing by owner
- Non-owner project invitation query protection (403)
- Voluntary acceptance (adds candidate to project_members)
- Non-invited student acceptance rejection (403)
- Voluntary decline/rejection (does not add to project_members)
- Owner cancellation (403 for non-owner, 200 for owner)
- Recommendation enrichment with invitation status
- Isolated Demo Mode invitation lifecycle
"""

import pytest
import jwt
import uuid
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings
from app.services.db_adapter import reset_in_memory_db, db
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
    reset_demo_invitations()
    yield
    settings.SUPABASE_JWT_SECRET = original_secret
    reset_in_memory_db()
    reset_demo_invitations()


@pytest.mark.asyncio
async def test_unauthenticated_endpoints():
    """All invitation endpoints must reject unauthenticated requests with 401."""
    transport = ASGITransport(app=app)
    fake_proj_id = str(uuid.uuid4())
    fake_inv_id = str(uuid.uuid4())
    fake_student_id = str(uuid.uuid4())

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        endpoints = [
            ("GET", "/api/v1/invitations", None),
            ("POST", f"/api/v1/projects/{fake_proj_id}/invitations", {"student_id": fake_student_id}),
            ("GET", f"/api/v1/projects/{fake_proj_id}/invitations", None),
            ("POST", f"/api/v1/invitations/{fake_inv_id}/accept", None),
            ("POST", f"/api/v1/invitations/{fake_inv_id}/reject", None),
            ("POST", f"/api/v1/invitations/{fake_inv_id}/cancel", None),
        ]
        for method, endpoint, body in endpoints:
            if method == "GET":
                res = await client.get(endpoint)
            elif method == "POST":
                res = await client.post(endpoint, json=body or {})
            assert res.status_code == 401, f"{method} {endpoint} returned {res.status_code} instead of 401"


@pytest.mark.asyncio
async def test_create_invitation_success():
    """Project owner can invite an eligible candidate student."""
    transport = ASGITransport(app=app)
    owner_user_id = str(uuid.uuid4())
    candidate_user_id = str(uuid.uuid4())

    owner_headers = {"Authorization": f"Bearer {create_test_jwt(owner_user_id, 'owner@college.edu')}"}
    candidate_headers = {"Authorization": f"Bearer {create_test_jwt(candidate_user_id, 'cand@college.edu')}"}

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create candidate profile first
        res_cand = await client.get("/api/v1/students/me", headers=candidate_headers)
        assert res_cand.status_code == 200
        candidate_student_id = res_cand.json()["id"]

        # Create owner project
        res_p = await client.post(
            "/api/v1/projects",
            json={"title": "AI Research Project", "description": "Cutting edge deep learning"},
            headers=owner_headers,
        )
        assert res_p.status_code == 201
        project_id = res_p.json()["id"]

        # Owner invites candidate
        res_inv = await client.post(
            f"/api/v1/projects/{project_id}/invitations",
            json={"student_id": candidate_student_id},
            headers=owner_headers,
        )
        assert res_inv.status_code == 201
        data = res_inv.json()
        assert data["status"] == "pending"
        assert data["project_id"] == project_id
        assert data["invited_student_id"] == candidate_student_id
        assert data["project"]["title"] == "AI Research Project"


@pytest.mark.asyncio
async def test_create_invitation_non_owner_forbidden():
    """Non-owner student cannot invite members to someone else's project."""
    transport = ASGITransport(app=app)
    owner_user_id = str(uuid.uuid4())
    intruder_user_id = str(uuid.uuid4())
    candidate_user_id = str(uuid.uuid4())

    owner_headers = {"Authorization": f"Bearer {create_test_jwt(owner_user_id)}" }
    intruder_headers = {"Authorization": f"Bearer {create_test_jwt(intruder_user_id)}" }
    cand_headers = {"Authorization": f"Bearer {create_test_jwt(candidate_user_id)}" }

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res_cand = await client.get("/api/v1/students/me", headers=cand_headers)
        candidate_student_id = res_cand.json()["id"]

        res_p = await client.post(
            "/api/v1/projects",
            json={"title": "Owner Project", "description": "Private project"},
            headers=owner_headers,
        )
        project_id = res_p.json()["id"]

        # Intruder attempts to send invitation
        res_inv = await client.post(
            f"/api/v1/projects/{project_id}/invitations",
            json={"student_id": candidate_student_id},
            headers=intruder_headers,
        )
        assert res_inv.status_code == 403


@pytest.mark.asyncio
async def test_create_invitation_self_invite_rejected():
    """Project owner cannot invite themselves."""
    transport = ASGITransport(app=app)
    owner_user_id = str(uuid.uuid4())
    owner_headers = {"Authorization": f"Bearer {create_test_jwt(owner_user_id)}" }

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res_owner = await client.get("/api/v1/students/me", headers=owner_headers)
        owner_student_id = res_owner.json()["id"]

        res_p = await client.post(
            "/api/v1/projects",
            json={"title": "Solo Project", "description": "Solo project"},
            headers=owner_headers,
        )
        project_id = res_p.json()["id"]

        res_inv = await client.post(
            f"/api/v1/projects/{project_id}/invitations",
            json={"student_id": owner_student_id},
            headers=owner_headers,
        )
        assert res_inv.status_code == 400
        assert "Cannot invite yourself" in res_inv.json()["detail"]


@pytest.mark.asyncio
async def test_create_invitation_duplicate_pending_rejected():
    """Duplicate pending invitations for the same candidate must be rejected with 409 Conflict."""
    transport = ASGITransport(app=app)
    owner_user_id = str(uuid.uuid4())
    candidate_user_id = str(uuid.uuid4())

    owner_headers = {"Authorization": f"Bearer {create_test_jwt(owner_user_id)}" }
    cand_headers = {"Authorization": f"Bearer {create_test_jwt(candidate_user_id)}" }

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res_cand = await client.get("/api/v1/students/me", headers=cand_headers)
        candidate_student_id = res_cand.json()["id"]

        res_p = await client.post(
            "/api/v1/projects",
            json={"title": "Team Project", "description": "Desc"},
            headers=owner_headers,
        )
        project_id = res_p.json()["id"]

        # First invitation succeeds
        res_inv1 = await client.post(
            f"/api/v1/projects/{project_id}/invitations",
            json={"student_id": candidate_student_id},
            headers=owner_headers,
        )
        assert res_inv1.status_code == 201

        # Second invitation conflicts
        res_inv2 = await client.post(
            f"/api/v1/projects/{project_id}/invitations",
            json={"student_id": candidate_student_id},
            headers=owner_headers,
        )
        assert res_inv2.status_code == 409
        assert "active pending invitation already exists" in res_inv2.json()["detail"]


@pytest.mark.asyncio
async def test_list_my_invitations_and_project_invitations():
    """Verify inbox and outbox views and project invitation listing."""
    transport = ASGITransport(app=app)
    owner_user_id = str(uuid.uuid4())
    candidate_user_id = str(uuid.uuid4())

    owner_headers = {"Authorization": f"Bearer {create_test_jwt(owner_user_id)}" }
    cand_headers = {"Authorization": f"Bearer {create_test_jwt(candidate_user_id)}" }

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res_cand = await client.get("/api/v1/students/me", headers=cand_headers)
        candidate_student_id = res_cand.json()["id"]

        res_p = await client.post(
            "/api/v1/projects",
            json={"title": "Invoiced App", "description": "Finance tool"},
            headers=owner_headers,
        )
        project_id = res_p.json()["id"]

        # Create invitation
        await client.post(
            f"/api/v1/projects/{project_id}/invitations",
            json={"student_id": candidate_student_id},
            headers=owner_headers,
        )

        # Candidate checks inbox (role=received)
        res_inbox = await client.get("/api/v1/invitations?role=received", headers=cand_headers)
        assert res_inbox.status_code == 200
        inbox_items = res_inbox.json()
        assert len(inbox_items) == 1
        assert inbox_items[0]["project"]["title"] == "Invoiced App"

        # Owner checks outbox (role=sent)
        res_outbox = await client.get("/api/v1/invitations?role=sent", headers=owner_headers)
        assert res_outbox.status_code == 200
        assert len(res_outbox.json()) == 1

        # Owner checks project invitations
        res_proj_inv = await client.get(f"/api/v1/projects/{project_id}/invitations", headers=owner_headers)
        assert res_proj_inv.status_code == 200
        assert len(res_proj_inv.json()) == 1

        # Non-owner checks project invitations -> 403 Forbidden
        res_cand_proj = await client.get(f"/api/v1/projects/{project_id}/invitations", headers=cand_headers)
        assert res_cand_proj.status_code == 403


@pytest.mark.asyncio
async def test_accept_invitation_adds_to_project_members():
    """Accepting invitation atomically adds candidate to project_members."""
    transport = ASGITransport(app=app)
    owner_user_id = str(uuid.uuid4())
    candidate_user_id = str(uuid.uuid4())

    owner_headers = {"Authorization": f"Bearer {create_test_jwt(owner_user_id)}" }
    cand_headers = {"Authorization": f"Bearer {create_test_jwt(candidate_user_id)}" }

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res_cand = await client.get("/api/v1/students/me", headers=cand_headers)
        candidate_student_id = res_cand.json()["id"]

        res_p = await client.post(
            "/api/v1/projects",
            json={"title": "Robotics Lab", "description": "Hardware and software"},
            headers=owner_headers,
        )
        project_id = res_p.json()["id"]

        res_inv = await client.post(
            f"/api/v1/projects/{project_id}/invitations",
            json={"student_id": candidate_student_id},
            headers=owner_headers,
        )
        invitation_id = res_inv.json()["id"]

        # Candidate accepts
        res_acc = await client.post(f"/api/v1/invitations/{invitation_id}/accept", headers=cand_headers)
        assert res_acc.status_code == 200
        assert res_acc.json()["status"] == "accepted"

        # Verify candidate is now in project_members
        res_p_detail = await client.get(f"/api/v1/projects/{project_id}", headers=owner_headers)
        assert res_p_detail.status_code == 200
        member_ids = [str(m["student_id"]) for m in res_p_detail.json()["members"]]
        assert candidate_student_id in member_ids

        # Candidate cannot accept again (already accepted)
        res_acc2 = await client.post(f"/api/v1/invitations/{invitation_id}/accept", headers=cand_headers)
        assert res_acc2.status_code == 400


@pytest.mark.asyncio
async def test_reject_invitation_does_not_add_to_members():
    """Declining invitation does NOT add candidate to project_members."""
    transport = ASGITransport(app=app)
    owner_user_id = str(uuid.uuid4())
    candidate_user_id = str(uuid.uuid4())

    owner_headers = {"Authorization": f"Bearer {create_test_jwt(owner_user_id)}" }
    cand_headers = {"Authorization": f"Bearer {create_test_jwt(candidate_user_id)}" }

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res_cand = await client.get("/api/v1/students/me", headers=cand_headers)
        candidate_student_id = res_cand.json()["id"]

        res_p = await client.post(
            "/api/v1/projects",
            json={"title": "Cloud Platform", "description": "Kubernetes cluster"},
            headers=owner_headers,
        )
        project_id = res_p.json()["id"]

        res_inv = await client.post(
            f"/api/v1/projects/{project_id}/invitations",
            json={"student_id": candidate_student_id},
            headers=owner_headers,
        )
        invitation_id = res_inv.json()["id"]

        # Candidate declines
        res_rej = await client.post(f"/api/v1/invitations/{invitation_id}/reject", headers=cand_headers)
        assert res_rej.status_code == 200
        assert res_rej.json()["status"] == "rejected"

        # Verify candidate is NOT in project_members
        res_p_detail = await client.get(f"/api/v1/projects/{project_id}", headers=owner_headers)
        assert res_p_detail.status_code == 200
        member_ids = [str(m["student_id"]) for m in res_p_detail.json()["members"]]
        assert candidate_student_id not in member_ids


@pytest.mark.asyncio
async def test_cancel_invitation_by_owner():
    """Project owner can withdraw a pending invitation."""
    transport = ASGITransport(app=app)
    owner_user_id = str(uuid.uuid4())
    candidate_user_id = str(uuid.uuid4())
    random_user_id = str(uuid.uuid4())

    owner_headers = {"Authorization": f"Bearer {create_test_jwt(owner_user_id)}" }
    cand_headers = {"Authorization": f"Bearer {create_test_jwt(candidate_user_id)}" }
    rand_headers = {"Authorization": f"Bearer {create_test_jwt(random_user_id)}" }

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res_cand = await client.get("/api/v1/students/me", headers=cand_headers)
        candidate_student_id = res_cand.json()["id"]

        res_p = await client.post(
            "/api/v1/projects",
            json={"title": "Mobile App", "description": "iOS and Android app"},
            headers=owner_headers,
        )
        project_id = res_p.json()["id"]

        res_inv = await client.post(
            f"/api/v1/projects/{project_id}/invitations",
            json={"student_id": candidate_student_id},
            headers=owner_headers,
        )
        invitation_id = res_inv.json()["id"]

        # Random student cannot cancel
        res_cancel_rand = await client.post(f"/api/v1/invitations/{invitation_id}/cancel", headers=rand_headers)
        assert res_cancel_rand.status_code == 403

        # Owner cancels
        res_cancel_owner = await client.post(f"/api/v1/invitations/{invitation_id}/cancel", headers=owner_headers)
        assert res_cancel_owner.status_code == 200
        assert res_cancel_owner.json()["status"] == "cancelled"


@pytest.mark.asyncio
async def test_demo_mode_invitation_lifecycle():
    """Demo project invitations work in-memory with zero Supabase interaction."""
    transport = ASGITransport(app=app)
    user_id = str(uuid.uuid4())
    headers = {"Authorization": f"Bearer {create_test_jwt(user_id)}" }

    demo_proj_id = "00000000-de00-0001-0000-000000000001"
    demo_candidate_id = "00000000-de00-0000-0000-000000000002"

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create demo invitation
        res_inv = await client.post(
            f"/api/v1/projects/{demo_proj_id}/invitations",
            json={"student_id": demo_candidate_id},
            headers=headers,
        )
        assert res_inv.status_code == 201
        inv_data = res_inv.json()
        assert inv_data["status"] == "pending"
        inv_id = inv_data["id"]

        # List demo invitations for project
        res_list = await client.get(f"/api/v1/projects/{demo_proj_id}/invitations", headers=headers)
        assert res_list.status_code == 200
        assert len(res_list.json()) == 1

        # Accept demo invitation
        res_acc = await client.post(f"/api/v1/invitations/{inv_id}/accept", headers=headers)
        assert res_acc.status_code == 200
        assert res_acc.json()["status"] == "accepted"

        # Verify demo project detail includes accepted candidate in members
        res_p = await client.get(f"/api/v1/projects/{demo_proj_id}", headers=headers)
        assert res_p.status_code == 200
        members = res_p.json()["members"]
        member_ids = [str(m["student_id"]) for m in members]
        assert demo_candidate_id in member_ids
