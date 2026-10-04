"""
Unit and Integration Tests for Phase 5 Step 1: AI Project Analysis Architecture
==============================================================================
Tests cover:
- Text preprocessing (cleaning, markdown stripping, technical syntax preservation)
- Empty and trivial text handling
- Configuration loading
- Sentence Transformer embedding provider interface and graceful fallback
- Taxonomy skill extraction and normalization
- Project analysis service orchestration
- Protected API endpoint validation (401 unauthenticated, 403 non-owner, 404 missing)
- Structured ProjectAnalysisResult schema fidelity
"""

import pytest
import jwt
import uuid
import sys
from pathlib import Path
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.config import settings
from app.services.db_adapter import reset_in_memory_db, db
from app.services.project_analysis.preprocessor import TextPreprocessor
from app.services.project_analysis.service import ProjectAnalysisService
from app.schemas.project_analysis import ProjectAnalysisResult, ExtractedSkill
from app.services.project_service import create_project
from app.schemas.project import ProjectCreate

root_workspace = Path(__file__).resolve().parent.parent.parent
if str(root_workspace) not in sys.path:
    sys.path.insert(0, str(root_workspace))

from ai.embeddings import SentenceTransformerEmbeddingProvider
from ai.skill_extraction import TaxonomyMatchSkillExtractor, CandidateSkill

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
# 1. Text Preprocessing Tests
# ==============================================================================

def test_preprocessing_normalizes_whitespace_and_markdown():
    """Verify markdown headers, bold, italics, bullets, and excessive spaces are cleaned."""
    raw = """
    # Smart Autonomous Drone Swarm
    
    * Developed an autonomous **quadcopter** swarm platform.
    * Uses [ROS2 Documentation](https://docs.ros.org) for communications.
    * Implemented with _Python_ and `FastAPI`.
    """
    cleaned = TextPreprocessor.clean(raw)
    assert "#" not in cleaned
    assert "*" not in cleaned
    assert "_" not in cleaned
    assert "`" not in cleaned
    assert "https://docs.ros.org" not in cleaned
    assert "ROS2 Documentation" in cleaned
    assert "quadcopter" in cleaned
    assert "Python" in cleaned
    assert "FastAPI" in cleaned
    assert "  " not in cleaned  # No double spaces


def test_preprocessing_preserves_technical_tokens():
    """Verify programming language symbols and technical abbreviations are retained."""
    raw = "Building microservices in C++, C#, .NET 8, Node.js, and React.js with AI/ML & CI/CD."
    cleaned = TextPreprocessor.clean(raw)
    assert "C++" in cleaned
    assert "C#" in cleaned
    assert ".NET" in cleaned
    assert "Node.js" in cleaned
    assert "React.js" in cleaned
    assert "AI/ML" in cleaned
    assert "CI/CD" in cleaned


def test_empty_and_trivial_text_handling():
    """Verify empty, None, and whitespace strings are safely identified as trivial."""
    assert TextPreprocessor.clean("") == ""
    assert TextPreprocessor.clean(None) == ""
    assert TextPreprocessor.clean("   \t\n  ") == ""
    assert TextPreprocessor.is_empty_or_trivial("") is True
    assert TextPreprocessor.is_empty_or_trivial(None) is True
    assert TextPreprocessor.is_empty_or_trivial("   ") is True
    assert TextPreprocessor.is_empty_or_trivial("Tiny", min_length=10) is True
    assert TextPreprocessor.is_empty_or_trivial("Valid length description string", min_length=10) is False


# ==============================================================================
# 2. Configuration & Embedding Service Tests
# ==============================================================================

def test_sentence_transformer_configuration_loaded():
    """Verify central configuration defines the default Sentence Transformer model."""
    assert hasattr(settings, "SENTENCE_TRANSFORMER_MODEL")
    assert settings.SENTENCE_TRANSFORMER_MODEL == "sentence-transformers/all-MiniLM-L6-v2"


def test_embedding_provider_interface_and_unavailable_handling():
    """
    Verify embedding provider provides the expected interface and reports
    model availability without fabricating fake embeddings.
    """
    provider = SentenceTransformerEmbeddingProvider(model_name=settings.SENTENCE_TRANSFORMER_MODEL)
    assert provider.model_name == "sentence-transformers/all-MiniLM-L6-v2"
    assert provider.embedding_dimension == 384
    # When sentence-transformers is not installed in the environment:
    # it must report is_available=False, return None on embed_text, and not crash
    if not provider.is_available:
        assert provider.embed_text("Any text") is None
        assert "not installed" in provider.status_message or "not loaded" in provider.status_message


# ==============================================================================
# 3. Skill Extraction Architecture Tests
# ==============================================================================

def test_taxonomy_skill_extractor_exact_and_alias():
    """Verify skill extraction identifies taxonomy skills and aliases without hallucinating."""
    extractor = TaxonomyMatchSkillExtractor()
    mock_taxonomy = [
        {"id": "skill-1", "name": "Python", "category": "ai_ml"},
        {"id": "skill-2", "name": "PyTorch", "category": "ai_ml"},
        {"id": "skill-3", "name": "React", "category": "frontend"},
        {"id": "skill-4", "name": "FastAPI", "category": "backend"},
    ]
    text = "We are using python programming, PyTorch deep learning, and react.js framework."
    extracted = extractor.extract_skills(text, mock_taxonomy)

    names = [e.normalized_name for e in extracted]
    assert "Python" in names
    assert "PyTorch" in names
    assert "React" in names
    assert "FastAPI" not in names  # Not mentioned

    # Verify attributes
    py_skill = next(e for e in extracted if e.normalized_name == "Python")
    assert py_skill.matched_skill_id == "skill-1"
    assert py_skill.confidence > 0.8
    assert py_skill.source in ("taxonomy_exact", "taxonomy_alias")
    assert py_skill.category == "ai_ml"


def test_taxonomy_skill_extractor_empty_input():
    """Verify extractor returns an empty list for empty descriptions."""
    extractor = TaxonomyMatchSkillExtractor()
    assert extractor.extract_skills("", [{"id": "1", "name": "Python"}]) == []
    assert extractor.extract_skills("Some random text with no tech", []) == []


# ==============================================================================
# 4. Project Analysis Service Integration Tests
# ==============================================================================

def test_project_analysis_service_structured_result():
    """Verify ProjectAnalysisService returns a fully validated ProjectAnalysisResult."""
    user_id = str(uuid.uuid4())
    proj = create_project(
        user_id,
        ProjectCreate(
            title="Computer Vision Edge Node",
            description="Developing real-time detection models with **PyTorch** and **FastAPI** deployment.",
            status="open",
        ),
    )
    service = ProjectAnalysisService()
    result = service.analyze_project(str(proj["id"]), user_id)

    assert isinstance(result, ProjectAnalysisResult)
    assert result.project_id == str(proj["id"])
    assert "PyTorch and FastAPI" in result.normalized_description
    assert result.analysis_status == "completed"
    assert result.embedding_available is True
    assert result.embedding_dimension == 384
    assert result.model_name == "sentence-transformers/all-MiniLM-L6-v2"
    assert isinstance(result.warnings, list)
    assert any(s.skill_name in ("PyTorch", "FastAPI") for s in result.extracted_skills)


def test_project_analysis_service_trivial_description_not_ready():
    """Short or empty descriptions must produce analysis_status='not_ready'."""
    user_id = str(uuid.uuid4())
    proj = create_project(
        user_id,
        ProjectCreate(
            title="Short Title",
            description="Brief",
            status="open",
        ),
    )
    service = ProjectAnalysisService()
    result = service.analyze_project(str(proj["id"]), user_id)

    assert result.analysis_status == "not_ready"
    assert len(result.extracted_skills) == 0
    assert any("too short" in w for w in result.warnings)


# ==============================================================================
# 5. Protected API Route Tests (POST /api/v1/projects/{project_id}/analyze)
# ==============================================================================

@pytest.mark.asyncio
async def test_api_analyze_unauthenticated_returns_401():
    """Unauthenticated POST to analyze must return 401."""
    transport = ASGITransport(app=app)
    fake_id = str(uuid.uuid4())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(f"/api/v1/projects/{fake_id}/analyze")
        assert res.status_code == 401


@pytest.mark.asyncio
async def test_api_analyze_not_found_returns_404():
    """Attempting to analyze a non-existent project returns 404."""
    user_id = str(uuid.uuid4())
    token = create_test_jwt(user_id)
    headers = {"Authorization": f"Bearer {token}"}
    fake_id = str(uuid.uuid4())

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(f"/api/v1/projects/{fake_id}/analyze", headers=headers)
        assert res.status_code == 404
        assert "not found" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_api_analyze_non_owner_returns_403():
    """Attempting to analyze another student's project must return 403 Forbidden."""
    owner_id = str(uuid.uuid4())
    other_user_id = str(uuid.uuid4())
    owner_token = create_test_jwt(owner_id)
    other_token = create_test_jwt(other_user_id)
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Owner creates project
        create_res = await client.post(
            "/api/v1/projects",
            json={
                "title": "Robotics System",
                "description": "Autonomous navigation with ROS2 and PyTorch.",
            },
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        proj_id = create_res.json()["id"]

        # Other user attempts to analyze owner's project -> 403
        analyze_res = await client.post(
            f"/api/v1/projects/{proj_id}/analyze",
            headers={"Authorization": f"Bearer {other_token}"},
        )
        assert analyze_res.status_code == 403
        assert "permission" in analyze_res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_api_analyze_owner_success_returns_structured_result():
    """Owner successfully analyzes project description and receives structured output."""
    owner_id = str(uuid.uuid4())
    owner_token = create_test_jwt(owner_id)
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Create project with descriptive tech stack
        create_res = await client.post(
            "/api/v1/projects",
            json={
                "title": "Decentralized AI",
                "description": "Building a **Python** backend with **FastAPI** and **Docker** containers.",
            },
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        proj_id = create_res.json()["id"]

        # 2. Call analyze endpoint
        analyze_res = await client.post(
            f"/api/v1/projects/{proj_id}/analyze",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert analyze_res.status_code == 200
        data = analyze_res.json()

        # Validate schema compliance
        assert data["project_id"] == proj_id
        assert "Python backend with FastAPI and Docker" in data["normalized_description"]
        assert data["analysis_status"] == "completed"
        assert data["embedding_available"] is True
        assert data["embedding_dimension"] == 384
        assert data["model_name"] == "sentence-transformers/all-MiniLM-L6-v2"
        assert isinstance(data["warnings"], list)
        assert isinstance(data["extracted_skills"], list)

        # Check extracted skills
        skill_names = [s["skill_name"] for s in data["extracted_skills"]]
        assert "Python" in skill_names
        assert "FastAPI" in skill_names
        assert "Docker" in skill_names


def test_taxonomy_skill_extractor_duplicate_prevention():
    """Verify multiple mentions and aliases of the same skill produce exactly one extracted entry."""
    extractor = TaxonomyMatchSkillExtractor()
    mock_taxonomy = [
        {"id": "skill-1", "name": "Python", "category": "ai_ml"},
        {"id": "skill-2", "name": "React", "category": "frontend"},
    ]
    text = "We write Python code, using Python 3 and python programming with React.js and React framework."
    extracted = extractor.extract_skills(text, mock_taxonomy)

    python_skills = [e for e in extracted if e.normalized_name == "Python"]
    react_skills = [e for e in extracted if e.normalized_name == "React"]
    assert len(python_skills) == 1
    assert len(react_skills) == 1


def test_taxonomy_skill_extractor_unmatched_terms():
    """Verify technical terms outside master taxonomy are identified as unmatched candidates."""
    extractor = TaxonomyMatchSkillExtractor()
    mock_taxonomy = [
        {"id": "skill-1", "name": "Python", "category": "ai_ml"},
    ]
    text = "We use Python with Kubernetes clusters and query services using GraphQL."
    extracted = extractor.extract_skills(text, mock_taxonomy)

    names = [e.normalized_name for e in extracted]
    assert "Python" in names
    assert "Kubernetes" in names
    assert "GraphQL" in names

    k8s = next(e for e in extracted if e.normalized_name == "Kubernetes")
    assert k8s.matched_skill_id is None
    assert k8s.source == "unmatched_candidate"

    gql = next(e for e in extracted if e.normalized_name == "GraphQL")
    assert gql.matched_skill_id is None
    assert gql.source == "unmatched_candidate"


def test_project_analysis_does_not_mutate_database():
    """Verify project analysis is strictly read-only and does not mutate project or required skills."""
    user_id = str(uuid.uuid4())
    proj = create_project(
        user_id,
        ProjectCreate(
            title="Read-Only Verification",
            description="Autonomous platform with **Python** and **FastAPI**.",
            status="open",
        ),
    )
    proj_id = str(proj["id"])
    initial_project = db.select_by_id("projects", proj_id)
    initial_skills = db.select_by_field("project_skills", "project_id", proj_id)

    service = ProjectAnalysisService()
    result = service.analyze_project(proj_id, user_id)

    # Skills were extracted in analysis
    assert len(result.extracted_skills) > 0

    # But database records remain identical
    after_project = db.select_by_id("projects", proj_id)
    after_skills = db.select_by_field("project_skills", "project_id", proj_id)
    assert after_project["title"] == initial_project["title"]
    assert after_project["description"] == initial_project["description"]
    assert after_project["status"] == initial_project["status"]
    assert len(after_skills) == len(initial_skills) == 0


def test_sentence_transformer_and_torch_imports():
    """Verify sentence-transformers and PyTorch CPU imports succeed."""
    import sentence_transformers
    import torch
    assert sentence_transformers.__version__ is not None
    assert torch.__version__ is not None
    assert torch.cuda.is_available() is False  # CPU only


def test_real_embedding_generation_and_dimension():
    """
    Test real embedding generation against sample description using CPU SentenceTransformer.
    Verifies actual 384-dimensional output and repeatable deterministic vectors.
    """
    provider = SentenceTransformerEmbeddingProvider(model_name=settings.SENTENCE_TRANSFORMER_MODEL)
    assert provider.is_available is True
    assert provider.embedding_dimension == 384
    assert provider.status_message == "Ready"

    sample_text = "Build a student collaboration platform using Python, FastAPI, React and machine learning."
    emb1 = provider.embed_text(sample_text)
    assert emb1 is not None
    assert isinstance(emb1, list)
    assert len(emb1) == 384
    assert all(isinstance(x, (int, float)) for x in emb1)

    # Determinism / repeatability test within floating point tolerance
    emb2 = provider.embed_text(sample_text)
    assert emb2 is not None
    assert len(emb2) == 384
    assert all(abs(a - b) < 1e-5 for a, b in zip(emb1, emb2))


def test_embedding_empty_and_whitespace_input():
    """Verify empty or whitespace-only strings return None safely."""
    provider = SentenceTransformerEmbeddingProvider(model_name=settings.SENTENCE_TRANSFORMER_MODEL)
    assert provider.embed_text("") is None
    assert provider.embed_text("   \n\t  ") is None


@pytest.mark.asyncio
async def test_api_analyze_invalid_uuid_returns_422():
    """POST to analyze with invalid UUID format returns 422."""
    user_id = str(uuid.uuid4())
    token = create_test_jwt(user_id)
    headers = {"Authorization": f"Bearer {token}"}
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/api/v1/projects/invalid-uuid-format/analyze", headers=headers)
        assert res.status_code == 422
