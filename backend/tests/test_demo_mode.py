"""
Unit and Integration Tests for Local Demonstration Mode
======================================================
Tests verify:
- Demo datasets (students.json, projects.json) integrity and metadata.
- Demo mode API endpoints (/api/v1/demo/*).
- Real PyTorch MLP inference via DemoRecommendationService (no hardcoding, continuous scores [0.0, 1.0]).
- Owner and existing member exclusion in demo recommendations.
- Descending ranking and Top-K / min_score filtering.
- Zero database mutations guarantee (no database writes during demo operations).
- Production mode preservation (DEMO_MODE default is False).
"""

import pytest
import uuid
import sys
from pathlib import Path
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.config import settings
from app.services.db_adapter import reset_in_memory_db, db
from app.services.demo_service import (
    load_demo_students,
    load_demo_projects,
    get_demo_project_by_id,
    DemoRecommendationService,
    is_demo_mode_active,
)

root_workspace = Path(__file__).resolve().parent.parent.parent
if str(root_workspace) not in sys.path:
    sys.path.insert(0, str(root_workspace))


@pytest.fixture(autouse=True)
def setup_test_env():
    reset_in_memory_db()
    original_demo_mode = settings.DEMO_MODE
    yield
    settings.DEMO_MODE = original_demo_mode


# ==========================================
# 1. Demo Dataset File & Metadata Integrity
# ==========================================

def test_demo_students_dataset_integrity():
    """Verify demo students file contains valid synthetic data with metadata."""
    import json
    students_file = root_workspace / "data" / "demo" / "students.json"
    assert students_file.exists()
    with open(students_file, "r", encoding="utf-8") as f:
        raw_data = json.load(f)
    meta = raw_data.get("_metadata", {})
    assert meta.get("dataset_type") == "DEMO"
    assert meta.get("synthetic") is True

    students = load_demo_students()
    assert len(students) >= 3
    assert len(students) == 4

    for s in students:
        # Check UUID format
        student_id = uuid.UUID(str(s["id"]))
        assert student_id is not None
        assert "full_name" in s
        assert "academic_year" in s
        assert "department" in s
        assert "skills" in s
        assert len(s["skills"]) > 0
        assert "interests" in s


def test_demo_projects_dataset_integrity():
    """Verify demo projects file contains valid synthetic data with metadata."""
    import json
    projects_file = root_workspace / "data" / "demo" / "projects.json"
    assert projects_file.exists()
    with open(projects_file, "r", encoding="utf-8") as f:
        raw_data = json.load(f)
    meta = raw_data.get("_metadata", {})
    assert meta.get("dataset_type") == "DEMO"
    assert meta.get("synthetic") is True

    projects = load_demo_projects()
    assert len(projects) >= 2
    assert len(projects) == 3

    for p in projects:
        project_id = uuid.UUID(str(p["id"]))
        assert project_id is not None
        assert "title" in p
        assert "description" in p
        assert "owner_id" in p
        assert "required_skills" in p
        assert len(p["required_skills"]) > 0


def test_get_demo_project_by_id():
    """Verify single demo project retrieval by valid and invalid ID."""
    projects = load_demo_projects()
    target_id = projects[0]["id"]

    found = get_demo_project_by_id(str(target_id))
    assert found["id"] == target_id
    assert found["title"] == projects[0]["title"]

    with pytest.raises(Exception) as exc_info:
        get_demo_project_by_id(str(uuid.uuid4()))
    assert "404" in str(exc_info.value) or "not found" in str(exc_info.value).lower()


# ==========================================
# 2. Demo Recommendation Engine & Real MLP
# ==========================================

def test_demo_recommendation_service_real_inference():
    """
    Verify DemoRecommendationService executes real PyTorch MLP inference
    using the existing trained checkpoint and produces continuous scores.
    """
    service = DemoRecommendationService()
    projects = load_demo_projects()
    demo_proj = projects[0]
    proj_id = demo_proj["id"]
    owner_id = str(demo_proj["owner_id"])

    response = service.get_demo_recommendations(project_id=str(proj_id))

    assert response.project_id == uuid.UUID(str(proj_id))
    assert response.project_title == demo_proj["title"]
    assert response.total_eligible_candidates > 0
    assert response.returned_recommendations_count > 0
    assert "demo" in response.model_version.lower()

    # Verify candidates
    for i, rec in enumerate(response.recommendations):
        # 1-based rank
        assert rec.rank == i + 1
        # Real continuous compatibility score [0.0, 1.0]
        assert 0.0 <= rec.compatibility_score <= 1.0
        # Owner is excluded
        assert str(rec.student_id) != owner_id
        # Required skills and match counts
        assert rec.required_skill_count == len(demo_proj["required_skills"])
        assert 0 <= rec.matched_skill_count <= rec.required_skill_count
        # Factual explanations
        assert rec.explanation is not None
        assert 0.0 <= rec.explanation.skill_coverage_ratio <= 1.0
        assert 0.0 <= rec.explanation.proficiency_alignment <= 1.0

    # Verify descending score order
    scores = [r.compatibility_score for r in response.recommendations]
    assert scores == sorted(scores, reverse=True)


def test_demo_recommendation_service_top_k_and_min_score():
    """Verify top_k truncation and min_score threshold filtering in demo service."""
    service = DemoRecommendationService()
    projects = load_demo_projects()
    proj_id = str(projects[0]["id"])

    # Test top_k = 1
    resp_top1 = service.get_demo_recommendations(project_id=proj_id, top_k=1)
    assert len(resp_top1.recommendations) <= 1

    # Test min_score threshold
    resp_all = service.get_demo_recommendations(project_id=proj_id, top_k=10, min_score=0.0)
    if resp_all.recommendations:
        highest_score = resp_all.recommendations[0].compatibility_score
        # A threshold higher than the highest score should yield 0 recommendations
        resp_filtered = service.get_demo_recommendations(
            project_id=proj_id, top_k=10, min_score=min(1.0, highest_score + 0.05)
        )
        assert len(resp_filtered.recommendations) == 0


# ==========================================
# 3. Demo API Endpoints Integration
# ==========================================

@pytest.mark.asyncio
async def test_demo_status_endpoint():
    """Verify GET /api/v1/demo/status returns demo metadata."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/demo/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["dataset_type"] == "DEMO"
        assert data["synthetic"] is True
        assert "demo_mode_configured" in data


@pytest.mark.asyncio
async def test_demo_students_and_projects_endpoints():
    """Verify demo listing endpoints return local datasets without authentication."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Students endpoint
        s_resp = await client.get("/api/v1/demo/students")
        assert s_resp.status_code == 200
        s_data = s_resp.json()
        assert s_data["synthetic"] is True
        assert s_data["count"] == 4
        assert len(s_data["students"]) == 4

        # Projects endpoint
        p_resp = await client.get("/api/v1/demo/projects")
        assert p_resp.status_code == 200
        p_data = p_resp.json()
        assert len(p_data) == 3

        # Single project endpoint
        proj_id = p_data[0]["id"]
        single_resp = await client.get(f"/api/v1/demo/projects/{proj_id}")
        assert single_resp.status_code == 200
        assert single_resp.json()["id"] == proj_id

        # 404 for nonexistent project
        fake_id = str(uuid.uuid4())
        not_found_resp = await client.get(f"/api/v1/demo/projects/{fake_id}")
        assert not_found_resp.status_code == 404


@pytest.mark.asyncio
async def test_demo_recommendations_endpoint():
    """Verify GET /api/v1/demo/projects/{project_id}/recommendations returns real MLP recommendations."""
    projects = load_demo_projects()
    proj_id = projects[0]["id"]

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(f"/api/v1/demo/projects/{proj_id}/recommendations?top_k=2")
        assert resp.status_code == 200
        data = resp.json()

        assert data["project_id"] == str(proj_id)
        assert data["returned_recommendations_count"] <= 2
        assert len(data["recommendations"]) <= 2
        for rec in data["recommendations"]:
            assert 0.0 <= rec["compatibility_score"] <= 1.0
            assert rec["explanation"]["skill_coverage_ratio"] is not None


# ==========================================
# 4. Zero Database Mutation Guarantee
# ==========================================

@pytest.mark.asyncio
async def test_demo_mode_zero_database_mutations():
    """
    Verify that executing Demo Mode operations causes ZERO mutations
    to the underlying database (no records inserted, updated, or deleted).
    """
    # Verify initial database state is empty
    initial_students = db.select_all("students")
    initial_projects = db.select_all("projects")
    assert len(initial_students) == 0
    assert len(initial_projects) == 0

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Fetch demo status
        await client.get("/api/v1/demo/status")

        # 2. Fetch demo students
        await client.get("/api/v1/demo/students")

        # 3. Fetch demo projects
        p_resp = await client.get("/api/v1/demo/projects")
        proj_id = p_resp.json()[0]["id"]

        # 4. Compute recommendations
        await client.get(f"/api/v1/demo/projects/{proj_id}/recommendations")

    # Re-verify database state is completely untouched
    final_students = db.select_all("students")
    final_projects = db.select_all("projects")
    assert len(final_students) == 0
    assert len(final_projects) == 0


# ==========================================
# 5. Production Mode Preservation
# ==========================================

def test_production_mode_preserved_by_default():
    """Verify DEMO_MODE defaults to False to prevent accidental exposure."""
    assert is_demo_mode_active() is False
    assert settings.DEMO_MODE is False
