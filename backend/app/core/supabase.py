from typing import Optional
from supabase import create_client, Client
from app.core.config import settings

_supabase_client: Optional[Client] = None
_supabase_admin_client: Optional[Client] = None


def is_supabase_configured() -> bool:
    """Check if valid Supabase connection details are present in environment."""
    return bool(
        settings.SUPABASE_URL
        and settings.SUPABASE_ANON_KEY
        and "your-supabase" not in settings.SUPABASE_URL
        and "your-supabase" not in settings.SUPABASE_ANON_KEY
    )


def get_supabase_client() -> Optional[Client]:
    """Get or create singleton Supabase client using anon key."""
    global _supabase_client
    if not is_supabase_configured():
        return None
    if _supabase_client is None:
        _supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
    return _supabase_client


def get_supabase_admin_client() -> Optional[Client]:
    """Get or create singleton Supabase client using service role key (backend only)."""
    global _supabase_admin_client
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        return None
    if _supabase_admin_client is None:
        _supabase_admin_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
    return _supabase_admin_client
