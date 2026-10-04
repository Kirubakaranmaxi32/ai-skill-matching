from typing import List, Dict, Any
from datetime import datetime, timezone
import uuid
from fastapi import HTTPException, status
from app.services.db_adapter import db
from app.services.student_service import get_or_create_student
from app.schemas.previous_project import PreviousProjectCreate


def get_student_projects(user_id: str) -> List[Dict[str, Any]]:
    """Retrieve all previous portfolio projects for the authenticated student."""
    student = get_or_create_student(user_id)
    return db.select_by_field("previous_projects", "student_id", str(student["id"]))


def add_student_project(user_id: str, data: PreviousProjectCreate) -> Dict[str, Any]:
    """Add a new past project to the authenticated student's portfolio."""
    student = get_or_create_student(user_id)
    now = datetime.now(timezone.utc).isoformat()

    new_record = {
        "id": str(uuid.uuid4()),
        "student_id": str(student["id"]),
        "title": data.title.strip(),
        "description": data.description.strip() if data.description else None,
        "technologies": data.technologies or [],
        "project_url": data.project_url.strip() if data.project_url else None,
        "created_at": now,
    }
    return db.insert("previous_projects", new_record)


def delete_student_project(user_id: str, project_id: str) -> bool:
    """
    Delete a previous project.
    Enforces strict ownership: students may only delete their own portfolio projects.
    """
    student = get_or_create_student(user_id)
    proj = db.select_by_id("previous_projects", str(project_id))

    if not proj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} not found."
        )

    # Ownership check
    if str(proj.get("student_id")) != str(student["id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You cannot delete another student's project."
        )

    db.delete("previous_projects", str(project_id))
    return True
