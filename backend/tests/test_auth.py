import pytest
import jwt
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings


@pytest.mark.asyncio
async def test_auth_me_unauthenticated_returns_401():
    """Verify that accessing GET /api/v1/auth/me without authorization header returns 401."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Authentication required" in data["detail"]


@pytest.mark.asyncio
async def test_auth_me_invalid_token_returns_401():
    """Verify that accessing GET /api/v1/auth/me with invalid bearer token returns 401."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {"Authorization": "Bearer invalid.token.payload"}
        response = await client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_auth_me_valid_jwt_with_secret():
    """Verify that a cryptographically signed Supabase-format JWT returns 200 and claims."""
    # Temporarily set a test JWT secret in settings
    original_secret = settings.SUPABASE_JWT_SECRET
    test_secret = "test-secret-key-32-chars-minimum-length!!"
    settings.SUPABASE_JWT_SECRET = test_secret

    try:
        # Create standard Supabase JWT payload
        test_payload = {
            "sub": "b2c3d4e5-6789-01bc-def0-123456789abc",
            "email": "student@college.edu",
            "aud": "authenticated",
            "role": "authenticated",
            "exp": 9999999999,  # Far future
        }
        token = jwt.encode(test_payload, test_secret, algorithm="HS256")

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            headers = {"Authorization": f"Bearer {token}"}
            response = await client.get("/api/v1/auth/me", headers=headers)
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == "b2c3d4e5-6789-01bc-def0-123456789abc"
            assert data["email"] == "student@college.edu"
            assert data["authenticated"] is True
    finally:
        settings.SUPABASE_JWT_SECRET = original_secret
