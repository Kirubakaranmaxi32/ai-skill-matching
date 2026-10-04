from typing import Dict, Any, List, Optional
from fastapi import HTTPException, status
from app.services.db_adapter import db, _now_iso
from app.services.student_service import get_or_create_student
from app.services.reference_service import get_skills
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectSkillCreate


def create_project(user_id: str, payload: ProjectCreate) -> Dict[str, Any]:
    """Create a new project owned by the authenticated student."""
    student = get_or_create_student(user_id)
    project_data = {
        "owner_id": str(student["id"]),
        "title": payload.title,
        "description": payload.description,
        "status": payload.status,
    }
    project = db.insert("projects", project_data)

    # Automatically add creator as owner member in project_members
    member_data = {
        "project_id": str(project["id"]),
        "student_id": str(student["id"]),
        "role": "owner",
        "joined_at": _now_iso(),
    }
    db.insert("project_members", member_data)

    return project


def get_my_projects(user_id: str) -> List[Dict[str, Any]]:
    """Retrieve all projects owned by the authenticated student, newest first."""
    student = get_or_create_student(user_id)
    projects = db.select_by_field("projects", "owner_id", str(student["id"]))
    # Sort descending by created_at
    projects.sort(key=lambda p: str(p.get("created_at", "")), reverse=True)
    return projects


def get_joined_projects(user_id: str) -> List[Dict[str, Any]]:
    """Retrieve all projects where the authenticated student is a team member (not owner)."""
    student = get_or_create_student(user_id)
    student_id_str = str(student["id"])
    memberships = db.select_by_field("project_members", "student_id", student_id_str)
    # Filter where role != 'owner'
    member_project_ids = [str(m.get("project_id")) for m in memberships if m.get("role") != "owner"]

    joined: List[Dict[str, Any]] = []
    seen = set()
    for pid in member_project_ids:
        if pid not in seen:
            seen.add(pid)
            proj = db.select_by_id("projects", pid)
            if proj and proj.get("status") != "archived":
                joined.append(proj)
    joined.sort(key=lambda p: str(p.get("created_at", "")), reverse=True)
    return joined


def get_discoverable_projects(_user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve all open and in_progress projects across the platform for student discovery."""
    all_projects = db.select_all("projects")
    discoverable = [p for p in all_projects if p.get("status") in ("open", "in_progress")]
    discoverable.sort(key=lambda p: str(p.get("created_at", "")), reverse=True)
    return discoverable



def get_project_by_id(project_id: str, user_id: str) -> Dict[str, Any]:
    """
    Retrieve project details, owner info, required skills, and members.
    Archived projects are only accessible by their owner.
    """
    project = db.select_by_id("projects", project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    student = get_or_create_student(user_id)
    is_owner = str(project.get("owner_id")) == str(student["id"])

    if project.get("status") == "archived" and not is_owner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or archived",
        )

    # Enrich owner
    owner_record = db.select_by_id("students", str(project.get("owner_id")))
    owner_info = None
    if owner_record:
        owner_info = {
            "id": owner_record["id"],
            "user_id": owner_record["user_id"],
            "full_name": owner_record.get("full_name", "Project Creator"),
            "academic_year": owner_record.get("academic_year"),
        }

    # Enrich required skills
    project_skills = db.select_by_field("project_skills", "project_id", project_id)
    taxonomy_skills = {str(s["id"]): s for s in get_skills()}
    enriched_skills = []
    for ps in project_skills:
        tax = taxonomy_skills.get(str(ps.get("skill_id")), {})
        enriched_skills.append({
            **ps,
            "skill_name": tax.get("name", "Unknown Skill"),
            "category": tax.get("category", "general"),
        })

    # Enrich members
    project_members = db.select_by_field("project_members", "project_id", project_id)
    enriched_members = []
    for pm in project_members:
        member_student = db.select_by_id("students", str(pm.get("student_id")))
        student_name = member_student.get("full_name", "Team Member") if member_student else "Team Member"
        enriched_members.append({
            **pm,
            "student_name": student_name,
        })

    return {
        **project,
        "owner": owner_info,
        "required_skills": enriched_skills,
        "members": enriched_members,
    }


def update_project(project_id: str, user_id: str, payload: ProjectUpdate) -> Dict[str, Any]:
    """Update project details with strict ownership verification."""
    project = db.select_by_id("projects", project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    student = get_or_create_student(user_id)
    if str(project.get("owner_id")) != str(student["id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to update this project",
        )

    updates: Dict[str, Any] = {}
    if payload.title is not None:
        updates["title"] = payload.title
    if payload.description is not None:
        updates["description"] = payload.description
    if payload.status is not None:
        updates["status"] = payload.status

    if not updates:
        return project

    updated = db.update("projects", project_id, updates)
    return updated or project


def archive_project(project_id: str, user_id: str) -> Dict[str, Any]:
    """Archive a project (soft status update, non-destructive)."""
    project = db.select_by_id("projects", project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    student = get_or_create_student(user_id)
    if str(project.get("owner_id")) != str(student["id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to archive this project",
        )

    updated = db.update("projects", project_id, {"status": "archived"})
    return updated or {**project, "status": "archived"}


def add_project_skill(project_id: str, user_id: str, payload: ProjectSkillCreate) -> Dict[str, Any]:
    """Add a required skill to a project (owner only)."""
    project = db.select_by_id("projects", project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    student = get_or_create_student(user_id)
    if str(project.get("owner_id")) != str(student["id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify skills for this project",
        )

    # Verify skill exists in taxonomy
    taxonomy = {str(s["id"]): s for s in get_skills()}
    skill_key = str(payload.skill_id)
    if skill_key not in taxonomy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Specified skill does not exist in taxonomy",
        )

    # Prevent duplicate
    existing = db.select_by_field("project_skills", "project_id", project_id)
    for ps in existing:
        if str(ps.get("skill_id")) == skill_key:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This skill is already required for the project",
            )

    item_data = {
        "project_id": str(project_id),
        "skill_id": skill_key,
        "required_proficiency": payload.required_proficiency,
    }
    created = db.insert("project_skills", item_data)
    tax = taxonomy[skill_key]
    return {
        **created,
        "skill_name": tax.get("name"),
        "category": tax.get("category"),
    }


def get_project_skills(project_id: str, user_id: str) -> List[Dict[str, Any]]:
    """Retrieve required skills for a project."""
    project = db.select_by_id("projects", project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    student = get_or_create_student(user_id)
    is_owner = str(project.get("owner_id")) == str(student["id"])
    if project.get("status") == "archived" and not is_owner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or archived",
        )

    project_skills = db.select_by_field("project_skills", "project_id", project_id)
    taxonomy = {str(s["id"]): s for s in get_skills()}
    results = []
    for ps in project_skills:
        tax = taxonomy.get(str(ps.get("skill_id")), {})
        results.append({
            **ps,
            "skill_name": tax.get("name", "Unknown Skill"),
            "category": tax.get("category", "general"),
        })
    return results


def delete_project_skill(project_id: str, skill_id: str, user_id: str) -> None:
    """Remove a required skill from a project (owner only)."""
    project = db.select_by_id("projects", project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    student = get_or_create_student(user_id)
    if str(project.get("owner_id")) != str(student["id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to remove skills from this project",
        )

    project_skills = db.select_by_field("project_skills", "project_id", project_id)
    match = next((ps for ps in project_skills if str(ps.get("skill_id")) == str(skill_id)), None)
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill is not associated with this project",
        )

    db.delete("project_skills", str(match["id"]))
