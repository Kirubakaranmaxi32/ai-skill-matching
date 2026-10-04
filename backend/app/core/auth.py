from typing import Dict, Any, Optional
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings
from app.core.supabase import get_supabase_client, is_supabase_configured

# HTTP Bearer scheme
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict[str, Any]:
    """
    FastAPI reusable authentication dependency for Supabase JWT validation.
    Reads Authorization: Bearer <token>, cryptographically validates the token,
    and returns authenticated user claims.

    Rejects missing, expired, or invalid tokens with HTTP 401 Unauthorized.
    """
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Bearer token missing.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # Case A: Cryptographic verification using SUPABASE_JWT_SECRET if provided
    if settings.SUPABASE_JWT_SECRET:
        try:
            payload = jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                audience="authenticated",
                options={"verify_exp": True, "verify_aud": True},
            )
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload: missing subject identifier.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return {
                "id": user_id,
                "email": payload.get("email"),
                "role": payload.get("role", "authenticated"),
                "app_metadata": payload.get("app_metadata", {}),
                "user_metadata": payload.get("user_metadata", {}),
            }
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication token has expired. Please log in again.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid authentication token: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # Case B: Verification via live Supabase client if configured
    if is_supabase_configured():
        supabase_client = get_supabase_client()
        if supabase_client:
            try:
                auth_response = supabase_client.auth.get_user(token)
                if auth_response and auth_response.user:
                    u = auth_response.user
                    return {
                        "id": u.id,
                        "email": u.email,
                        "role": getattr(u, "role", "authenticated"),
                        "app_metadata": getattr(u, "app_metadata", {}),
                        "user_metadata": getattr(u, "user_metadata", {}),
                    }
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Failed to validate token with Supabase: {str(e)}",
                    headers={"WWW-Authenticate": "Bearer"},
                )

    # If Supabase is not configured or token cannot be verified
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or unverified authentication token.",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_admin(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    FastAPI authorization dependency for administrative endpoints.
    Enforces that the authenticated user possesses verified administrative privileges.

    Authorization Verification:
    1. Cryptographically verified JWT `app_metadata.role` in ('admin', 'super_admin').
       (Note: `app_metadata` can only be authored server-side by service_role, never client-side).
    2. Server-side lookup in `public.admin_users` table matching `user_id`.

    Security Constraints:
    - Never trusts `user_metadata` (which is client-editable).
    - Never uses hard-coded email lists.
    - Rejects authenticated non-admins with HTTP 403 Forbidden.
    - Rejects unauthenticated requests with HTTP 401 Unauthorized (via get_current_user).
    """
    # 1. Check server-managed app_metadata claim
    app_meta = current_user.get("app_metadata", {})
    if isinstance(app_meta, dict) and app_meta.get("role") in ("admin", "super_admin"):
        return current_user

    # 2. Check dedicated admin_users table via DatabaseAdapter
    try:
        from app.services.db_adapter import db
        user_id = current_user.get("id")
        if user_id:
            admin_records = db.select_by_field("admin_users", "user_id", str(user_id))
            if admin_records and len(admin_records) > 0:
                return current_user
    except Exception:
        pass

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Administrative access required. You do not have permission to access this resource.",
    )
