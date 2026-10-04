from typing import List, Dict, Any
from datetime import datetime, timezone
import uuid
from fastapi import HTTPException, status
from app.services.db_adapter import db
from app.services.student_service import get_or_create_student
from app.schemas.certification import CertificationCreate


def get_student_certifications(user_id: str) -> List[Dict[str, Any]]:
    """Retrieve all certifications for the authenticated student."""
    student = get_or_create_student(user_id)
    return db.select_by_field("certifications", "student_id", str(student["id"]))


def add_student_certification(user_id: str, data: CertificationCreate) -> Dict[str, Any]:
    """Add a new verified certification for the authenticated student."""
    student = get_or_create_student(user_id)
    now = datetime.now(timezone.utc).isoformat()

    new_record = {
        "id": str(uuid.uuid4()),
        "student_id": str(student["id"]),
        "name": data.name.strip(),
        "issuing_organization": data.issuing_organization.strip(),
        "issue_date": data.issue_date.isoformat(),
        "credential_url": data.credential_url.strip() if data.credential_url else None,
        "created_at": now,
    }
    return db.insert("certifications", new_record)


def delete_student_certification(user_id: str, certification_id: str) -> bool:
    """
    Delete a certification.
    Enforces strict ownership: students may only delete their own certifications.
    """
    student = get_or_create_student(user_id)
    cert = db.select_by_id("certifications", str(certification_id))

    if not cert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certification with ID {certification_id} not found."
        )

    # Ownership check
    if str(cert.get("student_id")) != str(student["id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You cannot delete another student's certification."
        )

    db.delete("certifications", str(certification_id))
    return True
