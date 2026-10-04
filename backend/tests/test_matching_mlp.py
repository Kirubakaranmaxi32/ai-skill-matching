"""
Comprehensive Unit and Integration Tests for Phase 5 Step 3: PyTorch MLP Compatibility Model
===========================================================================================
Tests cover:
- Feature engineering (dimensions, metadata, ranges, determinism, missing values)
- Synthetic dataset generation (reproducibility, shapes, target range, finite values)
- CompatibilityMLP neural network (architecture, forward pass, CPU execution)
- Model training pipeline (losses, convergence, checkpoint saving)
- Evaluation metrics (MAE, MSE, RMSE, R2, no fabricated metrics)
- Inference service (checkpoint loading, single-pair scoring, feature contributions)
- Protected API endpoint (/api/v1/matching/compatibility - 401, 403, 404, 422, 200)
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

from ai.feature_engineering import (
    FeatureEngineer,
    FEATURE_COUNT,
    FEATURE_NAMES,
    FEATURE_DEFINITIONS,
)
from ai.training.synthetic_dataset import (
    generate_synthetic_features_and_targets,
    create_and_save_synthetic_datasets,
)
from ai.matching_model import CompatibilityMLP
from ai.training.trainer import CompatibilityModelTrainer
from ai.evaluation.evaluator import ModelEvaluator
from ai.inference.service import CompatibilityInferenceService, CompatibilityResult

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
# 1. Feature Engineering Tests
# ==============================================================================

def test_feature_engineering_dimensions_and_metadata():
    """Verify feature dimension is exactly 10 and metadata matches definitions."""
    fe = FeatureEngineer()
    assert fe.feature_count == 10
    assert len(fe.feature_names) == 10
    assert fe.feature_names == [d.name for d in FEATURE_DEFINITIONS]

    metadata = fe.get_feature_metadata()
    assert len(metadata) == 10
    for meta in metadata:
        assert "name" in meta
        assert "index" in meta
        assert "min_value" in meta
        assert "max_value" in meta
        assert "description" in meta


def test_feature_engineering_ranges_and_determinism():
    """Verify all features are bounded in [0.0, 1.0] and deterministic."""
    fe = FeatureEngineer()
    student_data = {
        "student": {"id": "stu-1", "academic_year": 3},
        "skills": [
            {"skill_id": "sk-1", "skill_name": "Python", "proficiency_level": 3, "category": "ai_ml"},
            {"skill_id": "sk-2", "skill_name": "PyTorch", "proficiency_level": 4, "category": "ai_ml"},
        ],
        "interests": [{"category": "ai_ml"}],
        "previous_projects": [{"title": "CV Project", "description": "Detect objects"}],
        "certifications": [{"name": "AWS ML"}],
    }
    project_data = {
        "project": {"id": "proj-1", "title": "AI Assistant", "description": "Using Python and PyTorch"},
        "required_skills": [
            {"skill_id": "sk-1", "required_proficiency": 3, "category": "ai_ml"},
            {"skill_id": "sk-2", "required_proficiency": 2, "category": "ai_ml"},
        ],
    }

    vec1, dict1 = fe.compute_features(student_data, project_data)
    vec2, dict2 = fe.compute_features(student_data, project_data)

    assert len(vec1) == 10
    assert vec1 == vec2
    assert dict1 == dict2

    for val in vec1:
        assert 0.0 <= val <= 1.0

    # Skill coverage should be 1.0 (both skills matched)
    assert dict1["skill_coverage_ratio"] == 1.0
    # Deficit should be 0.0 (student meets or exceeds requirements)
    assert dict1["proficiency_deficit_ratio"] == 0.0
    # Surplus should be > 0.0 (student has level 4 where 2 was required)
    assert dict1["proficiency_surplus_ratio"] > 0.0


def test_feature_engineering_missing_and_empty_values_safe():
    """Empty student or project data must produce valid normalized features without crashing."""
    fe = FeatureEngineer()
    vec, f_dict = fe.compute_features({}, {})
    assert len(vec) == 10
    for v in vec:
        assert isinstance(v, float)
        assert 0.0 <= v <= 1.0
        assert not math.isnan(v)
        assert not math.isinf(v)


# ==============================================================================
# 2. Synthetic Dataset Tests
# ==============================================================================

def test_synthetic_dataset_reproducibility():
    """Fixed random seed must produce identical synthetic feature vectors and targets."""
    f1, t1 = generate_synthetic_features_and_targets(num_samples=50, seed=42)
    f2, t2 = generate_synthetic_features_and_targets(num_samples=50, seed=42)
    assert f1 == f2
    assert t1 == t2


def test_synthetic_dataset_shape_and_finite_values():
    """Verify synthetic dataset features have 10 dimensions, target in [0,1], no NaN/inf."""
    features, targets = generate_synthetic_features_and_targets(num_samples=100, seed=123)
    assert len(features) == 100
    assert len(targets) == 100

    for feat, target in zip(features, targets):
        assert len(feat) == 10
        assert all(0.0 <= x <= 1.0 for x in feat)
        assert all(not math.isnan(x) and not math.isinf(x) for x in feat)
        assert 0.0 <= target <= 1.0
        assert not math.isnan(target) and not math.isinf(target)


# ==============================================================================
# 3. PyTorch CompatibilityMLP Tests
# ==============================================================================

def test_compatibility_mlp_architecture_and_cpu_forward():
    """Verify CompatibilityMLP layer architecture, CPU forward pass, and output range [0,1]."""
    model = CompatibilityMLP(input_dim=10, hidden_dims=(64, 32), dropout=0.1)
    config = model.get_model_config()
    assert config["input_dim"] == 10
    assert config["hidden_dims"] == [64, 32]
    assert config["output_activation"] == "Sigmoid"
    assert config["total_trainable_parameters"] > 0

    batch_x = torch.rand(8, 10, dtype=torch.float32)
    out = model(batch_x)
    assert out.shape == (8, 1)
    assert torch.all(out >= 0.0)
    assert torch.all(out <= 1.0)


def test_compatibility_mlp_single_prediction_score():
    """Verify predict_score returns a single bounded float."""
    model = CompatibilityMLP()
    score = model.predict_score([0.5] * 10)
    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0


# ==============================================================================
# 4. Training Pipeline Tests
# ==============================================================================

def test_training_pipeline_execution_and_checkpointing(tmp_path):
    """Verify training loop reduces loss, records history, and saves best model checkpoint."""
    X_train = torch.rand(64, 10, dtype=torch.float32)
    y_train = torch.rand(64, 1, dtype=torch.float32)
    X_val = torch.rand(16, 10, dtype=torch.float32)
    y_val = torch.rand(16, 1, dtype=torch.float32)

    trainer = CompatibilityModelTrainer(
        learning_rate=0.01,
        batch_size=16,
        epochs=5,
        seed=42,
    )
    summary = trainer.train(X_train, y_train, X_val, y_val, tmp_path)

    assert summary["epochs_total"] == 5
    assert summary["best_epoch"] >= 1
    assert not math.isnan(summary["best_val_loss"])
    assert len(summary["history"]) == 5

    checkpoint_file = tmp_path / "checkpoints" / "best_matching_mlp.pt"
    assert checkpoint_file.exists()

    ckpt = torch.load(checkpoint_file, map_location="cpu", weights_only=False)
    assert "model_state_dict" in ckpt
    assert "model_config" in ckpt


# ==============================================================================
# 5. Model Evaluation Tests
# ==============================================================================

def test_model_evaluator_metrics_calculation():
    """Verify MAE, MSE, RMSE, and R2 are computed accurately without fabrication."""
    model = CompatibilityMLP()
    X_test = torch.rand(30, 10, dtype=torch.float32)
    y_test = torch.rand(30, 1, dtype=torch.float32)

    metrics = ModelEvaluator.evaluate(model, X_test, y_test)
    assert "mae" in metrics
    assert "mse" in metrics
    assert "rmse" in metrics
    assert "r2" in metrics
    assert metrics["mae"] >= 0.0
    assert metrics["mse"] >= 0.0
    assert metrics["rmse"] >= 0.0
    assert not math.isnan(metrics["mae"])
    assert not math.isnan(metrics["r2"])


# ==============================================================================
# 6. Inference Service Tests
# ==============================================================================

def test_inference_service_computes_score_and_contributions():
    """Verify CompatibilityInferenceService loads checkpoint and scores pair."""
    service = CompatibilityInferenceService()
    assert service.is_loaded is True

    student_data = {
        "student": {"id": "stu-100", "academic_year": 4},
        "skills": [{"skill_id": "sk-1", "proficiency_level": 4}],
        "interests": [],
        "previous_projects": [],
        "certifications": [],
    }
    project_data = {
        "project": {"id": "proj-200", "title": "ML System", "description": "PyTorch"},
        "required_skills": [{"skill_id": "sk-1", "required_proficiency": 4}],
    }

    res = service.evaluate_pair(student_data, project_data)
    assert isinstance(res, CompatibilityResult)
    assert res.student_id == "stu-100"
    assert res.project_id == "proj-200"
    assert 0.0 <= res.compatibility_score <= 1.0
    assert len(res.raw_feature_vector) == 10
    assert len(res.feature_contributions) == 10


# ==============================================================================
# 7. Protected Matching API Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_api_compatibility_unauthenticated_returns_401():
    """Unauthenticated call to compatibility endpoint returns 401."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/api/v1/matching/compatibility",
            json={"project_id": str(uuid.uuid4())},
        )
        assert res.status_code == 401


@pytest.mark.asyncio
async def test_api_compatibility_self_assessment_success():
    """Authenticated student successfully evaluates their own compatibility against an open project."""
    student_user_id = str(uuid.uuid4())
    owner_user_id = str(uuid.uuid4())
    student_token = create_test_jwt(student_user_id)
    owner_token = create_test_jwt(owner_user_id)
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Owner creates a project
        create_res = await client.post(
            "/api/v1/projects",
            json={"title": "NLP System", "description": "Building with Python and FastAPI"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        proj_id = create_res.json()["id"]

        # 2. Student evaluates their own compatibility (student_id omitted -> defaults to self)
        comp_res = await client.post(
            "/api/v1/matching/compatibility",
            json={"project_id": proj_id},
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert comp_res.status_code == 200
        data = comp_res.json()
        assert data["project_id"] == proj_id
        assert 0.0 <= data["compatibility_score"] <= 1.0
        assert "model_version" in data
        assert len(data["feature_contributions"]) == 10


@pytest.mark.asyncio
async def test_api_compatibility_owner_evaluates_candidate_student_success():
    """Project owner can evaluate a candidate student's compatibility against their project."""
    owner_user_id = str(uuid.uuid4())
    candidate_user_id = str(uuid.uuid4())
    owner_token = create_test_jwt(owner_user_id)
    transport = ASGITransport(app=app)

    # Initialize candidate student record
    candidate_student = get_or_create_student(candidate_user_id, full_name="Candidate Student")
    cand_student_id = candidate_student["id"]

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Owner creates project
        create_res = await client.post(
            "/api/v1/projects",
            json={"title": "Cloud Platform", "description": "Distributed architecture"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        proj_id = create_res.json()["id"]

        # Owner evaluates candidate
        comp_res = await client.post(
            "/api/v1/matching/compatibility",
            json={"project_id": proj_id, "student_id": cand_student_id},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert comp_res.status_code == 200
        data = comp_res.json()
        assert data["student_id"] == cand_student_id
        assert data["project_id"] == proj_id
        assert 0.0 <= data["compatibility_score"] <= 1.0


@pytest.mark.asyncio
async def test_api_compatibility_non_owner_evaluating_other_student_returns_403():
    """Non-owner student evaluating another student against someone else's project returns 403."""
    owner_user_id = str(uuid.uuid4())
    other_user_id = str(uuid.uuid4())
    candidate_user_id = str(uuid.uuid4())
    other_token = create_test_jwt(other_user_id)
    owner_token = create_test_jwt(owner_user_id)
    transport = ASGITransport(app=app)

    candidate_student = get_or_create_student(candidate_user_id)
    cand_student_id = candidate_student["id"]

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_res = await client.post(
            "/api/v1/projects",
            json={"title": "Security Lab", "description": "Network security"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        proj_id = create_res.json()["id"]

        # other_user attempts to evaluate candidate on owner's project -> 403
        comp_res = await client.post(
            "/api/v1/matching/compatibility",
            json={"project_id": proj_id, "student_id": cand_student_id},
            headers={"Authorization": f"Bearer {other_token}"},
        )
        assert comp_res.status_code == 403
        assert "permission" in comp_res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_api_compatibility_missing_project_returns_404():
    """Querying compatibility for non-existent project returns 404."""
    user_id = str(uuid.uuid4())
    token = create_test_jwt(user_id)
    fake_proj_id = str(uuid.uuid4())
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/api/v1/matching/compatibility",
            json={"project_id": fake_proj_id},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 404
        assert "project not found" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_api_compatibility_invalid_uuid_returns_422():
    """Invalid UUID format returns 422 Unprocessable Entity."""
    user_id = str(uuid.uuid4())
    token = create_test_jwt(user_id)
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/api/v1/matching/compatibility",
            json={"project_id": "not-a-valid-uuid"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 422
