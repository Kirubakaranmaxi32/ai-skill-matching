from typing import List, Dict, Any
from datetime import datetime, timezone
import uuid
from fastapi import HTTPException, status
from app.services.db_adapter import db
from app.services.student_service import get_or_create_student
from app.services.reference_service import get_interests


def get_student_interests(user_id: str) -> List[Dict[str, Any]]:
    """Retrieve all interests selected by the authenticated student."""
    student = get_or_create_student(user_id)
    student_interests = db.select_by_field("student_interests", "student_id", str(student["id"]))

    enriched = []
    for si in student_interests:
        interest_info = db.select_by_id("interests", str(si["interest_id"]))
        enriched.append({
            **si,
            "interest_name": interest_info.get("name") if interest_info else "Unknown",
        })
    return enriched


def add_student_interest(user_id: str, interest_id: str) -> Dict[str, Any]:
    """Add an interest area for the authenticated student."""
    student = get_or_create_student(user_id)

    # Validate interest exists in taxonomy
    interest = db.select_by_id("interests", str(interest_id))
    if not interest:
        all_interests = get_interests()
        matching = [i for i in all_interests if str(i["id"]) == str(interest_id)]
        if not matching:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Interest with ID {interest_id} does not exist in interests taxonomy."
            )
        interest = matching[0]

    # Check for existing association (unique constraint)
    existing_interests = db.select_by_field("student_interests", "student_id", str(student["id"]))
    existing = next((i for i in existing_interests if str(i["interest_id"]) == str(interest_id)), None)
    if existing:
        return {
            **existing,
            "interest_name": interest["name"],
        }

    now = datetime.now(timezone.utc).isoformat()
    new_record = {
        "id": str(uuid.uuid4()),
        "student_id": str(student["id"]),
        "interest_id": str(interest_id),
        "created_at": now,
    }
    inserted = db.insert("student_interests", new_record)
    return {
        **inserted,
        "interest_name": interest["name"],
    }


def delete_student_interest(user_id: str, interest_id: str) -> bool:
    """
    Remove an interest selection for the authenticated student.
    Accepts either the interest_id (from taxonomy) or the student_interests entry UUID.
    """
    student = get_or_create_student(user_id)
    existing_interests = db.select_by_field("student_interests", "student_id", str(student["id"]))

    matching = next(
        (i for i in existing_interests if str(i["interest_id"]) == str(interest_id) or str(i["id"]) == str(interest_id)),
        None
    )
    if not matching:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interest association '{interest_id}' not found for the current student."
        )

    db.delete("student_interests", str(matching["id"]))
    return True
