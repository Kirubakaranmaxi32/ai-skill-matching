"""
AI Skill Matching - Matching Service
====================================
Coordinates data retrieval and single-pair compatibility scoring between
authenticated students and projects using the trained PyTorch MLP model.
"""

from typing import Dict, Any, Optional
import sys
from pathlib import Path
from uuid import UUID
from fastapi import HTTPException, status

from app.services.db_adapter import db
from app.services.student_service import get_or_create_student
from app.schemas.matching import CompatibilityRequest, CompatibilityResponse

# Ensure root workspace is available for ai package imports
root_workspace = Path(__file__).resolve().parent.parent.parent.parent
if str(root_workspace) not in sys.path:
    sys.path.insert(0, str(root_workspace))

from ai.inference import CompatibilityInferenceService


class MatchingService:
    """
    Coordinates data retrieval and inference for student-project compatibility.
    """

    def __init__(self):
        self._inference_service = CompatibilityInferenceService()

    def evaluate_compatibility(
        self,
        request: CompatibilityRequest,
        current_user_id: str,
    ) -> CompatibilityResponse:
        """
        Evaluates compatibility between a target student and project.
        
        Security:
        - Authenticated user can evaluate their own compatibility with any existing project.
        - A project owner can evaluate any candidate student against their owned project.
        - Non-owners cannot query compatibility of other students (403 Forbidden).
        - Unknown project or student returns 404 Not Found.
        """
        project_id_str = str(request.project_id)
        current_student = get_or_create_student(current_user_id)
        current_student_id = str(current_student["id"])

        # 1. Verify project existence
        project = db.select_by_id("projects", project_id_str)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        # 2. Determine target student ID
        if request.student_id:
            target_student_id = str(request.student_id)
        else:
            target_student_id = current_student_id

        # 3. Privacy & Authorization check
        if target_student_id != current_student_id:
            # Caller must be the project owner
            if str(project.get("owner_id")) != current_student_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to evaluate compatibility for other students on this project",
                )

        # 4. Verify target student exists
        target_student = db.select_by_id("students", target_student_id)
        if not target_student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found",
            )

        # 5. Retrieve student profile relational data
        student_skills = db.select_by_field("student_skills", "student_id", target_student_id)
        student_interests = db.select_by_field("student_interests", "student_id", target_student_id)
        previous_projects = db.select_by_field("previous_projects", "student_id", target_student_id)
        certifications = db.select_by_field("certifications", "student_id", target_student_id)

        # 6. Retrieve project required skills
        required_skills = db.select_by_field("project_skills", "project_id", project_id_str)

        # 7. Formulate data dictionaries
        student_data = {
            "student": target_student,
            "skills": student_skills,
            "interests": student_interests,
            "previous_projects": previous_projects,
            "certifications": certifications,
        }
        project_data = {
            "project": project,
            "required_skills": required_skills,
        }

        # 8. Execute PyTorch MLP forward pass
        result = self._inference_service.evaluate_pair(student_data, project_data)

        return CompatibilityResponse(
            student_id=UUID(target_student_id),
            project_id=UUID(project_id_str),
            compatibility_score=result.compatibility_score,
            model_version=result.model_version,
            feature_contributions=result.feature_contributions,
        )


matching_service = MatchingService()
