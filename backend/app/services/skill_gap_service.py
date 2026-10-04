"""
Skill-Gap Analysis Service
==========================
Coordinates skill-gap evaluation comparing a student's technical skills and
proficiency levels against the required skills and proficiency levels of a project.

Key Features:
- Classifies each project-required skill into:
  1. MATCHED: Student has the skill and student proficiency >= required proficiency.
  2. PARTIAL: Student has the skill but student proficiency < required proficiency.
  3. MISSING: Student does not have the required skill.
- Calculates total required skills, matched count, partial count, missing count,
  skill coverage ratio, proficiency gap count, and overall gap summary.
- Adheres strictly to the 1-4 proficiency scale.
- Enforces authorization:
  * Any authenticated student can evaluate their own skill-gap against any project.
  * Project owners can evaluate candidate students against their project.
  * Unrelated students cannot view other students' private skill gap reports (403).
- Supports Demo Mode with zero database mutations or reads.
"""

from typing import Dict, Any, List, Optional
from uuid import UUID
from fastapi import HTTPException, status

from app.services.db_adapter import db
from app.services.student_service import get_or_create_student
from app.services.reference_service import get_skills
from app.schemas.skill_gap import (
    SkillGapResponse,
    SkillGapSummary,
    SkillGapItem,
    SkillGapStatus,
)


def calculate_skill_gap(
    required_skills: List[Dict[str, Any]],
    student_skills: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Pure computational function comparing project required skills against student skills.
    
    Args:
        required_skills: List of dicts with:
            - skill_id: str or UUID
            - skill_name: str
            - required_proficiency: int (1-4)
            - category: Optional[str]
        student_skills: List of dicts with:
            - skill_id: str or UUID
            - proficiency or proficiency_level: int (1-4)
            - skill_name: Optional[str]
            - category: Optional[str]
            
    Returns:
        Dict with 'summary' dict and 'skills' list of evaluated items.
    """
    # 1. Map student skills by skill_id
    student_skill_map: Dict[str, int] = {}
    for s in student_skills:
        sid = str(s.get("skill_id") or s.get("id") or "")
        if sid:
            # Supports both 'proficiency' (db) and 'proficiency_level' (demo/api)
            prof = int(s.get("proficiency") or s.get("proficiency_level") or 1)
            student_skill_map[sid] = prof

    items: List[SkillGapItem] = []
    matched_count = 0
    partial_count = 0
    missing_count = 0

    # 2. Evaluate each required skill
    for req in required_skills:
        req_id_raw = req.get("skill_id") or req.get("id")
        if not req_id_raw:
            continue
        req_id_str = str(req_id_raw)
        req_id_uuid = UUID(req_id_str)
        req_name = req.get("skill_name") or req.get("name") or "Technical Skill"
        req_prof = int(req.get("required_proficiency") or req.get("proficiency") or 1)
        category = req.get("category")

        if req_id_str in student_skill_map:
            stu_prof = student_skill_map[req_id_str]
            if stu_prof >= req_prof:
                status_val = SkillGapStatus.MATCHED
                gap_val = None
                matched_count += 1
            else:
                status_val = SkillGapStatus.PARTIAL
                gap_val = req_prof - stu_prof
                partial_count += 1
            items.append(
                SkillGapItem(
                    skill_id=req_id_uuid,
                    skill_name=req_name,
                    category=category,
                    required_proficiency=req_prof,
                    student_proficiency=stu_prof,
                    status=status_val,
                    proficiency_gap=gap_val,
                )
            )
        else:
            missing_count += 1
            items.append(
                SkillGapItem(
                    skill_id=req_id_uuid,
                    skill_name=req_name,
                    category=category,
                    required_proficiency=req_prof,
                    student_proficiency=None,
                    status=SkillGapStatus.MISSING,
                    proficiency_gap=None,
                )
            )

    total_required = len(items)
    if total_required == 0:
        coverage_ratio = 1.0
        summary_text = "Project specifies no required skills. Full coverage."
    else:
        coverage_ratio = round(matched_count / total_required, 4)
        summary_text = (
            f"Candidate fully matches {matched_count} of {total_required} required skills "
            f"({int(coverage_ratio * 100)}% coverage), with {partial_count} partial "
            f"proficiency gap(s) and {missing_count} missing skill(s)."
        )

    summary = SkillGapSummary(
        total_required_skills=total_required,
        matched_count=matched_count,
        partial_count=partial_count,
        missing_count=missing_count,
        skill_coverage_ratio=coverage_ratio,
        proficiency_gap_count=partial_count,
        overall_gap_summary=summary_text,
    )

    return {
        "summary": summary,
        "skills": items,
    }


class SkillGapService:
    """Service orchestrating skill gap lookups, authorization, and computation."""

    def get_project_skill_gap(
        self,
        project_id: str,
        user_id: str,
        student_id: Optional[str] = None,
    ) -> SkillGapResponse:
        """
        Calculates skill-gap analysis between a student and a project from the database.
        
        Authorization:
        - Authenticated user can analyze their own student profile for any visible project.
        - Project owner can analyze any candidate student profile for their project.
        - Unauthorized requests (non-owner querying other student) return 403 Forbidden.
        """
        # 1. Retrieve project
        project = db.select_by_id("projects", project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project not found with ID: {project_id}",
            )

        # 2. Retrieve requesting student
        requesting_student = get_or_create_student(user_id)
        requesting_student_id = str(requesting_student["id"])
        project_owner_id = str(project.get("owner_id"))

        # 3. Resolve target student
        if student_id is None or str(student_id) == requesting_student_id:
            target_student = requesting_student
            target_student_id = requesting_student_id
        else:
            # Querying another student: caller MUST be project owner
            if project_owner_id != requesting_student_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized: You can only view your own skill gap or candidate skill gaps for projects you own.",
                )
            target_student = db.select_by_id("students", str(student_id))
            if not target_student:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Student not found with ID: {student_id}",
                )
            target_student_id = str(student_id)

        # 4. Fetch project required skills enriched with taxonomy
        taxonomy_skills = {str(s["id"]): s for s in get_skills()}
        project_skills = db.select_by_field("project_skills", "project_id", project_id)
        enriched_req_skills: List[Dict[str, Any]] = []
        for ps in project_skills:
            tax = taxonomy_skills.get(str(ps.get("skill_id")), {})
            enriched_req_skills.append({
                "skill_id": str(ps.get("skill_id")),
                "skill_name": tax.get("name", "Technical Skill"),
                "category": tax.get("category", "general"),
                "required_proficiency": ps.get("required_proficiency", 2),
            })

        # 5. Fetch target student skills
        raw_student_skills = db.select_by_field("student_skills", "student_id", target_student_id)
        student_skills: List[Dict[str, Any]] = []
        for ss in raw_student_skills:
            tax = taxonomy_skills.get(str(ss.get("skill_id")), {})
            student_skills.append({
                "skill_id": str(ss.get("skill_id")),
                "skill_name": tax.get("name", "Technical Skill"),
                "proficiency": ss.get("proficiency", 1),
                "category": tax.get("category", "general"),
            })

        # 6. Calculate gap
        gap_data = calculate_skill_gap(enriched_req_skills, student_skills)

        return SkillGapResponse(
            project_id=UUID(project_id),
            project_title=project.get("title"),
            student_id=UUID(target_student_id),
            student_name=target_student.get("full_name"),
            summary=gap_data["summary"],
            skills=gap_data["skills"],
        )

    def get_demo_project_skill_gap(
        self,
        project_id: str,
        student_id: Optional[str] = None,
    ) -> SkillGapResponse:
        """
        Computes skill-gap analysis using purely local synthetic demonstration data.
        Never executes any database queries or mutations.
        """
        from app.services.demo_service import (
            load_demo_students,
            load_demo_projects,
            get_demo_project_by_id,
        )

        demo_project = get_demo_project_by_id(project_id)
        all_students = load_demo_students()

        # Find target student
        target_student: Optional[Dict[str, Any]] = None
        if student_id:
            for s in all_students:
                if str(s.get("id")) == str(student_id):
                    target_student = s
                    break
            if not target_student:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Demo student not found with ID: {student_id}",
                )
        else:
            # Default to first non-owner student (candidate) or first student
            owner_id = str(demo_project.get("owner_id"))
            for s in all_students:
                if str(s.get("id")) != owner_id:
                    target_student = s
                    break
            if not target_student and all_students:
                target_student = all_students[0]

        if not target_student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No demo student available for skill gap analysis",
            )

        gap_data = calculate_skill_gap(
            required_skills=demo_project.get("required_skills", []),
            student_skills=target_student.get("skills", []),
        )

        return SkillGapResponse(
            project_id=UUID(str(demo_project["id"])),
            project_title=demo_project.get("title"),
            student_id=UUID(str(target_student["id"])),
            student_name=target_student.get("full_name"),
            summary=gap_data["summary"],
            skills=gap_data["skills"],
        )


skill_gap_service = SkillGapService()
