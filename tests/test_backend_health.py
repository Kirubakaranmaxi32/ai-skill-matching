import sys
from pathlib import Path
import pytest
from httpx import AsyncClient, ASGITransport

# Ensure backend directory is in python path
backend_path = Path(__file__).resolve().parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from app.main import app


@pytest.mark.asyncio
async def test_backend_health_from_root():
    """Verify that root GET /health returns 200 from root test suite."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "ai-skill-matching-backend"


@pytest.mark.asyncio
async def test_backend_v1_health_from_root():
    """Verify that GET /api/v1/health returns 200 from root test suite."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "v1"
