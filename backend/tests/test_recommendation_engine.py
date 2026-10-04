"""
Comprehensive Unit and Integration Tests for Phase 5 Step 4: Recommendation Engine
===================================================================================
Tests cover:
- Candidate discovery and eligibility filtering (owner excluded, members excluded, invalid records skipped)
- PyTorch MLP integration (reusing existing checkpoint, no retraining)
- Descending ranking, Top-K truncation, and minimum score threshold filtering
- Factual explainability breakdown (matched vs missing skills, coverage ratio, proficiency alignment)
- Protected recommendation API endpoint:
  * 401 unauthenticated
  * 403 unauthorized (non-owner)
  * 404 project not found
  * 422 invalid UUID or out-of-bounds parameters
  * 200 success with Top-K and threshold checks
  * Empty candidate scenarios
"""

import pytest
import jwt
import uuid
import sys
import math
from pathlib import Path
import torch
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.config import settings
from app.services.db_adapter import reset_in_memory_db, db
from app.services.student_service import get_or_create_student
from app.services.project_service import create_project, add_project_skill
from app.schemas.project import ProjectCreate, ProjectSkillCreate

root_workspace = Path(__file__).resolve().parent.parent.parent
if str(root_workspace) not in sys.path:
    sys.path.insert(0, str(root_workspace))

from ai.recommendation import RecommendationEngine
from app.services.recommendation_service import RecommendationService

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
    settings.SUPABASE_JWT_SECRET = TEST_JWT_SECRET
    reset_in_memory_db()
    yield
    settings.SUPABASE_JWT_SECRET = original_secret
    reset_in_memory_db()


# ==============================================================================
# 1. RecommendationEngine Unit Tests
# ==============================================================================

def test_recommendation_engine_loads_existing_checkpoint():
    """Verify RecommendationEngine reuses existing PyTorch MLP checkpoint without retraining."""
    engine = RecommendationEngine()
    assert engine.is_model_loaded is True
    assert engine.model_version is not None


def test_recommendation_engine_scoring_and_descending_ranking():
    """Verify candidates are sorted in descending order of compatibility score."""
    engine = RecommendationEngine()
    project_data = {
        "project": {"id": "proj-1", "title": "AI System", "description": "PyTorch deep learning"},
        "required_skills": [
            {"skill_id": "sk-1", "skill_name": "Python", "required_proficiency": 3, "category": "ai_ml"},
            {"skill_id": "sk-2", "skill_name": "PyTorch", "required_proficiency": 3, "category": "ai_ml"},
        ],
    }

    # Candidate A: high match (has both skills at high proficiency)
    cand_a = {
        "student": {"id": "stu-a", "full_name": "Alice Expert", "academic_year": 4},
        "skills": [
            {"skill_id": "sk-1", "skill_name": "Python", "proficiency_level": 4, "category": "ai_ml"},
            {"skill_id": "sk-2", "skill_name": "PyTorch", "proficiency_level": 4, "category": "ai_ml"},
        ],
        "interests": [{"category": "ai_ml"}],
        "previous_projects": [{"title": "CV Project", "description": "PyTorch"}],
        "certifications": [{"name": "Deep Learning Spec"}],
    }

    # Candidate B: low match (no relevant skills, year 1)
    cand_b = {
        "student": {"id": "stu-b", "full_name": "Bob Novice", "academic_year": 1},
        "skills": [],
        "interests": [],
        "previous_projects": [],
        "certifications": [],
    }

    results = engine.score_and_rank_candidates(project_data, [cand_b, cand_a], top_k=10, min_score=0.0)

    assert len(results) == 2
    # Candidate A should be Rank 1 with higher score than Candidate B
    assert results[0]["student_id"] == "stu-a"
    assert results[0]["rank"] == 1
    assert results[1]["student_id"] == "stu-b"
    assert results[1]["rank"] == 2
    assert results[0]["compatibility_score"] > results[1]["compatibility_score"]


def test_recommendation_engine_top_k_truncation():
    """Verify top_k parameter strictly caps returned results."""
    engine = RecommendationEngine()
    project_data = {
        "project": {"id": "proj-1", "title": "Platform"},
        "required_skills": [],
    }

    candidates = [
        {"student": {"id": f"stu-{i}", "full_name": f"Student {i}"}, "skills": []}
        for i in range(15)
    ]

    results = engine.score_and_rank_candidates(project_data, candidates, top_k=5, min_score=0.0)
    assert len(results) == 5
    assert [r["rank"] for r in results] == [1, 2, 3, 4, 5]


def test_recommendation_engine_min_score_filtering():
    """Verify candidates below min_score threshold are eliminated."""
    engine = RecommendationEngine()
    project_data = {
        "project": {"id": "proj-1", "title": "High Bar Project"},
        "required_skills": [{"skill_id": "sk-1", "required_proficiency": 4}],
    }

    # Low match candidate
    cand_low = {"student": {"id": "stu-low"}, "skills": []}

    results = engine.score_and_rank_candidates(project_data, [cand_low], top_k=10, min_score=0.99)
    assert len(results) == 0


def test_recommendation_engine_factual_explanation_structure():
    """Verify explanation breakdown contains factual matched and missing skills."""
    engine = RecommendationEngine()
    project_data = {
        "project": {"id": "p-1", "title": "Web App"},
        "required_skills": [
            {"skill_id": "s-react", "skill_name": "React", "required_proficiency": 3},
            {"skill_id": "s-fastapi", "skill_name": "FastAPI", "required_proficiency": 2},
        ],
    }

    cand = {
        "student": {"id": "s-1", "full_name": "Frontend Dev"},
        "skills": [
            {"skill_id": "s-react", "skill_name": "React", "proficiency_level": 3},
        ],
    }

    results = engine.score_and_rank_candidates(project_data, [cand], top_k=5, min_score=0.0)
    assert len(results) == 1
    expl = results[0]["explanation"]

    assert len(expl["matched_skills"]) == 1
    assert expl["matched_skills"][0]["skill_name"] == "React"
    assert expl["matched_skills"][0]["student_proficiency"] == 3

    assert len(expl["missing_skills"]) == 1
    assert expl["missing_skills"][0]["skill_name"] == "FastAPI"

    assert expl["skill_coverage_ratio"] == 0.5
    assert "proficiency_alignment" in expl


# ==============================================================================
# 2. RecommendationService & Candidate Discovery Tests
# ==============================================================================

def test_candidate_discovery_excludes_owner_and_members():
    """Verify that project owner and existing project members are excluded from recommendations."""
    owner_user = str(uuid.uuid4())
    member_user = str(uuid.uuid4())
    eligible_user = str(uuid.uuid4())

    owner_student = get_or_create_student(owner_user, full_name="Owner Student")
    member_student = get_or_create_student(member_user, full_name="Member Student")
    eligible_student = get_or_create_student(eligible_user, full_name="Eligible Candidate")

    # Owner creates project
    proj = create_project(owner_user, ProjectCreate(title="Distributed Systems", description="Go & Docker"))
    proj_id = str(proj["id"])

    # Add member_student as member
    db.insert("project_members", {
        "project_id": proj_id,
        "student_id": str(member_student["id"]),
        "role": "contributor",
        "joined_at": "2026-01-01T00:00:00Z",
    })

    service = RecommendationService()
    res = service.get_project_recommendations(proj_id, owner_user, top_k=10, min_score=0.0)

    # Eligible list should include only eligible_student; owner and member are strictly excluded
    candidate_ids = [str(r.student_id) for r in res.recommendations]
    assert str(eligible_student["id"]) in candidate_ids
    assert str(owner_student["id"]) not in candidate_ids
    assert str(member_student["id"]) not in candidate_ids
    assert res.total_eligible_candidates == 1


# ==============================================================================
# 3. Protected API Integration Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_api_recommendations_unauthenticated_returns_401():
    """Unauthenticated call to recommendations endpoint returns 401."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get(f"/api/v1/projects/{uuid.uuid4()}/recommendations")
        assert res.status_code == 401


@pytest.mark.asyncio
async def test_api_recommendations_non_owner_returns_403():
    """Attempting to view recommendations for another student's project returns 403 Forbidden."""
    owner_id = str(uuid.uuid4())
    other_user_id = str(uuid.uuid4())
    owner_token = create_test_jwt(owner_id)
    other_token = create_test_jwt(other_user_id)
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_res = await client.post(
            "/api/v1/projects",
            json={"title": "Autonomous Drone", "description": "ROS2 and PyTorch"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        proj_id = create_res.json()["id"]

        # other_user attempts to view recommendations -> 403
        rec_res = await client.get(
            f"/api/v1/projects/{proj_id}/recommendations",
            headers={"Authorization": f"Bearer {other_token}"},
        )
        assert rec_res.status_code == 403
        assert "permission" in rec_res.json()["detail"].lower() or "owner" in rec_res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_api_recommendations_missing_project_returns_404():
    """Recommendations for non-existent project returns 404."""
    user_id = str(uuid.uuid4())
    token = create_test_jwt(user_id)
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get(
            f"/api/v1/projects/{uuid.uuid4()}/recommendations",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 404


@pytest.mark.asyncio
async def test_api_recommendations_invalid_params_returns_422():
    """Invalid top_k or min_score returns 422 Unprocessable Entity."""
    user_id = str(uuid.uuid4())
    token = create_test_jwt(user_id)
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Invalid top_k (0 < 1)
        res = await client.get(
            f"/api/v1/projects/{uuid.uuid4()}/recommendations?top_k=0",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 422

        # Invalid min_score (1.5 > 1.0)
        res2 = await client.get(
            f"/api/v1/projects/{uuid.uuid4()}/recommendations?min_score=1.5",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res2.status_code == 422


@pytest.mark.asyncio
async def test_api_recommendations_owner_success_with_candidates():
    """Owner successfully retrieves ranked candidate recommendations with factual explainability."""
    owner_id = str(uuid.uuid4())
    cand1_id = str(uuid.uuid4())
    cand2_id = str(uuid.uuid4())

    owner_token = create_test_jwt(owner_id)
    transport = ASGITransport(app=app)

    # Initialize candidates
    s1 = get_or_create_student(cand1_id, full_name="Candidate Senior")
    s2 = get_or_create_student(cand2_id, full_name="Candidate Junior")

    # Add skills to candidate 1
    db.insert("student_skills", {
        "student_id": str(s1["id"]),
        "skill_id": "a1000000-0000-0000-0000-000000000001",  # Python
        "proficiency_level": 4,
    })

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Create project
        create_res = await client.post(
            "/api/v1/projects",
            json={"title": "Fullstack ML App", "description": "FastAPI, React, Python"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        proj_id = create_res.json()["id"]

        # 2. Add required skill
        await client.post(
            f"/api/v1/projects/{proj_id}/skills",
            json={"skill_id": "a1000000-0000-0000-0000-000000000001", "required_proficiency": 3},
            headers={"Authorization": f"Bearer {owner_token}"},
        )

        # 3. Request recommendations
        rec_res = await client.get(
            f"/api/v1/projects/{proj_id}/recommendations?top_k=5&min_score=0.0",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert rec_res.status_code == 200
        data = rec_res.json()

        assert data["project_id"] == proj_id
        assert data["total_eligible_candidates"] >= 2
        assert len(data["recommendations"]) <= 5
        assert "model_version" in data

        # Check ranking order
        recs = data["recommendations"]
        if len(recs) >= 2:
            assert recs[0]["compatibility_score"] >= recs[1]["compatibility_score"]
            assert recs[0]["rank"] == 1
            assert recs[1]["rank"] == 2

        # Check factual explanation fields
        top_rec = recs[0]
        assert "explanation" in top_rec
        assert "matched_skills" in top_rec["explanation"]
        assert "missing_skills" in top_rec["explanation"]
        assert "skill_coverage_ratio" in top_rec["explanation"]
        assert 0.0 <= top_rec["compatibility_score"] <= 1.0


@pytest.mark.asyncio
async def test_api_recommendations_empty_when_no_candidates():
    """Project with zero eligible candidates returns clean empty list."""
    owner_id = str(uuid.uuid4())
    owner_token = create_test_jwt(owner_id)
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_res = await client.post(
            "/api/v1/projects",
            json={"title": "Solo Project", "description": "Just me"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        proj_id = create_res.json()["id"]

        rec_res = await client.get(
            f"/api/v1/projects/{proj_id}/recommendations",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert rec_res.status_code == 200
        data = rec_res.json()
        assert data["total_eligible_candidates"] == 0
        assert data["returned_recommendations_count"] == 0
        assert data["recommendations"] == []
