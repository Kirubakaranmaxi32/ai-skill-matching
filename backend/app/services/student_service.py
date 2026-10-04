from typing import Dict, Any, Optional
import uuid
from datetime import datetime, timezone
from fastapi import HTTPException, status
from app.services.db_adapter import db
from app.schemas.student import StudentProfileUpdate


def get_or_create_student(
    user_id: str,
    email: Optional[str] = None,
    full_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Retrieves the student record linked to the authenticated Supabase user_id.
    If the student row does not yet exist, initializes it lazily.
    """
    students = db.select_by_field("students", "user_id", user_id)
    if students:
        return students[0]

    # Handle lazy student creation for newly registered users
    display_name = full_name
    if not display_name and email:
        display_name = email.split("@")[0].replace(".", " ").title()
    if not display_name:
        display_name = "Student User"

    new_student = {
        "id": str(uuid.uuid4()),
        "user_id": str(user_id),
        "full_name": display_name,
        "department_id": None,
        "academic_year": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    created = db.insert("students", new_student)
    return created


def get_student_profile(
    user_id: str,
    email: Optional[str] = None,
    full_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Get student profile with department details."""
    student = get_or_create_student(user_id, email=email, full_name=full_name)
    dept_name = None
    if student.get("department_id"):
        dept = db.select_by_id("departments", str(student["department_id"]))
        if dept:
            dept_name = dept.get("name")
    
    return {
        **student,
        "department_name": dept_name,
    }


def update_student_profile(user_id: str, update_data: StudentProfileUpdate) -> Dict[str, Any]:
    """Update profile fields for the authenticated student."""
    student = get_or_create_student(user_id)
    updates: Dict[str, Any] = {}

    if update_data.full_name is not None:
        updates["full_name"] = update_data.full_name.strip()

    if update_data.department_id is not None:
        # Validate department exists
        dept = db.select_by_id("departments", str(update_data.department_id))
        if not dept:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Department with ID {update_data.department_id} does not exist."
            )
        updates["department_id"] = str(update_data.department_id)

    if update_data.academic_year is not None:
        updates["academic_year"] = update_data.academic_year

    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    updated = db.update("students", str(student["id"]), updates)
    if not updated:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update profile.")

    return get_student_profile(user_id)
