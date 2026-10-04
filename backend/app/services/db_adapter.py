from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime, timezone
from app.core.supabase import get_supabase_admin_client, is_supabase_configured

# In-memory test store used for local testing or when direct PostgREST is unreachable
_in_memory_db: Dict[str, Dict[str, Dict[str, Any]]] = {
    "departments": {},
    "skills": {},
    "interests": {},
    "students": {},
    "student_skills": {},
    "student_interests": {},
    "certifications": {},
    "previous_projects": {},
    "projects": {},
    "project_skills": {},
    "project_members": {},
    "invitations": {},
    "project_progress": {},
    "project_tasks": {},
    "recommendation_feedback": {},
    "admin_users": {},
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def reset_in_memory_db() -> None:
    """Helper to reset in-memory tables for tests."""
    for table in _in_memory_db:
        _in_memory_db[table].clear()


class DatabaseAdapter:
    """
    Unified database adapter.
    Uses Supabase client when available; seamlessly falls back to test store
    for offline unit and integration testing.
    """

    def __init__(self):
        self._supabase = get_supabase_admin_client() if is_supabase_configured() else None

    # --------------------------------------------------------------------------
    # Generic Helpers
    # --------------------------------------------------------------------------
    def select_all(self, table: str) -> List[Dict[str, Any]]:
        if self._supabase:
            try:
                res = self._supabase.table(table).select("*").execute()
                if res.data and len(res.data) > 0:
                    return res.data
            except Exception:
                pass
        return list(_in_memory_db[table].values())

    def select_by_id(self, table: str, item_id: str) -> Optional[Dict[str, Any]]:
        if self._supabase:
            try:
                res = self._supabase.table(table).select("*").eq("id", str(item_id)).execute()
                if res.data and len(res.data) > 0:
                    return res.data[0]
            except Exception:
                pass
        return _in_memory_db[table].get(str(item_id))

    def select_by_field(self, table: str, field: str, value: Any) -> List[Dict[str, Any]]:
        if self._supabase:
            try:
                res = self._supabase.table(table).select("*").eq(field, str(value)).execute()
                if res.data and len(res.data) > 0:
                    return res.data
            except Exception:
                pass
        return [row for row in _in_memory_db[table].values() if str(row.get(field)) == str(value)]

    def insert(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        item = dict(data)
        if "id" not in item:
            item["id"] = str(uuid.uuid4())
        if "created_at" not in item:
            item["created_at"] = _now_iso()
        if "updated_at" not in item and table in ["projects", "students", "student_skills"]:
            item["updated_at"] = item["created_at"]
        if "joined_at" not in item and table == "project_members":
            item["joined_at"] = item["created_at"]

        # Update in-memory
        _in_memory_db[table][str(item["id"])] = dict(item)

        if self._supabase:
            try:
                res = self._supabase.table(table).insert(item).execute()
                if res.data and len(res.data) > 0:
                    return res.data[0]
            except Exception:
                pass
        return item

    def update(self, table: str, item_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        existing = self.select_by_id(table, item_id)
        if not existing:
            return None

        updated_item = {**existing, **updates}
        if "updated_at" not in updates and "updated_at" in existing:
            updated_item["updated_at"] = _now_iso()

        _in_memory_db[table][str(item_id)] = dict(updated_item)

        if self._supabase:
            try:
                res = self._supabase.table(table).update(updates).eq("id", str(item_id)).execute()
                if res.data and len(res.data) > 0:
                    return res.data[0]
            except Exception:
                pass
        return updated_item

    def delete(self, table: str, item_id: str) -> bool:
        existed = str(item_id) in _in_memory_db[table]
        if existed:
            del _in_memory_db[table][str(item_id)]

        if self._supabase:
            try:
                res = self._supabase.table(table).delete().eq("id", str(item_id)).execute()
                if res.data and len(res.data) > 0:
                    return True
            except Exception:
                pass
        return existed

    def delete_by_fields(self, table: str, filters: Dict[str, Any]) -> bool:
        to_delete = []
        for item_id, row in _in_memory_db[table].items():
            match = all(str(row.get(k)) == str(v) for k, v in filters.items())
            if match:
                to_delete.append(item_id)

        for item_id in to_delete:
            del _in_memory_db[table][item_id]

        if self._supabase:
            try:
                query = self._supabase.table(table).delete()
                for k, v in filters.items():
                    query = query.eq(k, str(v))
                res = query.execute()
                if res.data and len(res.data) > 0:
                    return True
            except Exception:
                pass

        return len(to_delete) > 0


db = DatabaseAdapter()
