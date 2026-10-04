from typing import List, Dict, Any
from datetime import datetime, timezone
import uuid
from fastapi import HTTPException, status
from app.services.db_adapter import db
from app.services.student_service import get_or_create_student
from app.services.reference_service import get_skills


def get_student_skills(user_id: str) -> List[Dict[str, Any]]:
    """Retrieve all skills associated with the authenticated student."""
    student = get_or_create_student(user_id)
    student_skills = db.select_by_field("student_skills", "student_id", str(student["id"]))
    
    # Enrich with skill metadata (name, category)
    enriched = []
    for ss in student_skills:
        skill_info = db.select_by_id("skills", str(ss["skill_id"]))
        enriched.append({
            **ss,
            "skill_name": skill_info.get("name") if skill_info else "Unknown",
            "skill_category": skill_info.get("category") if skill_info else "general",
        })
    return enriched


def add_student_skill(user_id: str, skill_id: str, proficiency: int) -> Dict[str, Any]:
    """Add or update a skill proficiency rating for the authenticated student."""
    student = get_or_create_student(user_id)

    # Validate skill exists in taxonomy
    skill = db.select_by_id("skills", str(skill_id))
    if not skill:
        # Check against available skills or auto-seed
        all_skills = get_skills()
        matching = [s for s in all_skills if str(s["id"]) == str(skill_id)]
        if not matching:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Skill with ID {skill_id} does not exist in skills taxonomy."
            )
        skill = matching[0]

    # Check for existing association (unique constraint on student_id, skill_id)
    existing_skills = db.select_by_field("student_skills", "student_id", str(student["id"]))
    existing_record = next((s for s in existing_skills if str(s["skill_id"]) == str(skill_id)), None)

    now = datetime.now(timezone.utc).isoformat()
    if existing_record:
        # Update proficiency
        updated = db.update(
            "student_skills",
            str(existing_record["id"]),
            {"proficiency": proficiency, "updated_at": now}
        )
        return {
            **updated,
            "skill_name": skill["name"],
            "skill_category": skill["category"],
        }

    # Insert new record
    new_skill_record = {
        "id": str(uuid.uuid4()),
        "student_id": str(student["id"]),
        "skill_id": str(skill_id),
        "proficiency": proficiency,
        "created_at": now,
        "updated_at": now,
    }
    inserted = db.insert("student_skills", new_skill_record)
    return {
        **inserted,
        "skill_name": skill["name"],
        "skill_category": skill["category"],
    }


def delete_student_skill(user_id: str, skill_id: str) -> bool:
    """
    Remove a skill rating from the authenticated student.
    Accepts either the skill_id (from taxonomy) or the student_skills entry UUID.
    """
    student = get_or_create_student(user_id)
    existing_skills = db.select_by_field("student_skills", "student_id", str(student["id"]))

    matching = next(
        (s for s in existing_skills if str(s["skill_id"]) == str(skill_id) or str(s["id"]) == str(skill_id)),
        None
    )
    if not matching:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill association '{skill_id}' not found for the current student."
        )

    db.delete("student_skills", str(matching["id"]))
    return True
