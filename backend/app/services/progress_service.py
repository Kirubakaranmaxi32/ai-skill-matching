"""
Progress Service
================
Orchestrates project tasks, milestones, and progress tracking:
- Validates that callers are project owners or accepted team members (Phase 13 compliance).
- Provides task management with member assignments, priority, and workflow statuses.
- Provides milestone and progress update tracking.
- Implements isolated in-memory Demo Mode with zero Supabase mutations.
"""

from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID
from datetime import datetime, timezone
import uuid
from fastapi import HTTPException, status

from app.services.db_adapter import db, _now_iso
from app.services.student_service import get_or_create_student
from app.schemas.progress import (
    ProjectProgressCreate,
    ProjectProgressUpdate,
    ProjectProgressResponse,
    ProjectTaskCreate,
    ProjectTaskUpdate,
    ProjectTaskResponse,
    ProjectProgressOverviewResponse,
)

# In-memory Demo stores
_demo_tasks_store: Dict[str, Dict[str, Any]] = {}
_demo_progress_store: Dict[str, Dict[str, Any]] = {}


def reset_demo_progress_and_tasks() -> None:
    """Helper to clear local demo stores."""
    _demo_tasks_store.clear()
    _demo_progress_store.clear()


def _init_demo_seeds(project_id: str) -> None:
    """Seed demo project with initial tasks and progress checkpoint if empty."""
    if not any(t["project_id"] == project_id for t in _demo_tasks_store.values()):
        task1_id = str(uuid.uuid4())
        task2_id = str(uuid.uuid4())
        task3_id = str(uuid.uuid4())
        now = _now_iso()

        _demo_tasks_store[task1_id] = {
            "id": task1_id,
            "project_id": project_id,
            "title": "Setup PyTorch Model Architecture (Demo)",
            "description": "Construct neural network layers and initialize checkpoint loading pipeline.",
            "assigned_student_id": "00000000-de00-0000-0000-000000000001",
            "status": "completed",
            "priority": "high",
            "due_date": now,
            "completed_at": now,
            "created_by": "00000000-de00-0000-0000-000000000001",
            "created_at": now,
            "updated_at": now,
        }
        _demo_tasks_store[task2_id] = {
            "id": task2_id,
            "project_id": project_id,
            "title": "Design REST API Endpoints (Demo)",
            "description": "Build FastAPI routers for data ingestion and real-time inference.",
            "assigned_student_id": "00000000-de00-0000-0000-000000000002",
            "status": "in_progress",
            "priority": "medium",
            "due_date": now,
            "completed_at": None,
            "created_by": "00000000-de00-0000-0000-000000000001",
            "created_at": now,
            "updated_at": now,
        }
        _demo_tasks_store[task3_id] = {
            "id": task3_id,
            "project_id": project_id,
            "title": "Frontend Integration & UI Testing (Demo)",
            "description": "Connect React components to backend APIs with comprehensive test suites.",
            "assigned_student_id": None,
            "status": "todo",
            "priority": "medium",
            "due_date": None,
            "completed_at": None,
            "created_by": "00000000-de00-0000-0000-000000000001",
            "created_at": now,
            "updated_at": now,
        }

    if not any(p["project_id"] == project_id for p in _demo_progress_store.values()):
        prog_id = str(uuid.uuid4())
        now = _now_iso()
        _demo_progress_store[prog_id] = {
            "id": prog_id,
            "project_id": project_id,
            "title": "Sprint 1 — Core Architecture Complete (Demo)",
            "description": "Foundational models and service layers established successfully.",
            "progress_percentage": 50,
            "status": "on_track",
            "created_by": "00000000-de00-0000-0000-000000000001",
            "created_at": now,
            "updated_at": now,
            "completed_at": None,
        }


class ProgressService:
    """Service managing project progress, tasks, and team milestones."""

    def _verify_membership(
        self, project_id: str, user_id: str
    ) -> Tuple[Dict[str, Any], Dict[str, Any], bool]:
        """
        Validates caller access:
        Returns (student, project, is_owner).
        Raises 403 Forbidden if student is neither owner nor accepted team member.
        """
        student = get_or_create_student(user_id)
        student_id = str(student["id"])

        project = db.select_by_id("projects", project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project not found with ID: {project_id}",
            )

        is_owner = str(project.get("owner_id")) == student_id
        if is_owner:
            return student, project, True

        # Check accepted membership in project_members
        members = db.select_by_field("project_members", "project_id", project_id)
        is_member = any(str(m.get("student_id")) == student_id for m in members)

        if not is_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized: Only the project owner and accepted team members can access project progress and tasks.",
            )

        return student, project, False

    # --------------------------------------------------------------------------
    # Task Management
    # --------------------------------------------------------------------------
    def create_task(
        self, project_id: str, user_id: str, payload: ProjectTaskCreate
    ) -> ProjectTaskResponse:
        """Create a new task for an active project team."""
        if project_id.startswith("00000000-de00"):
            return self._create_demo_task(project_id, payload)

        student, project, _ = self._verify_membership(project_id, user_id)
        student_id = str(student["id"])

        # Validate assigned student if provided
        assigned_name = None
        if payload.assigned_student_id:
            assigned_id_str = str(payload.assigned_student_id)
            # Must be owner or member
            is_assignee_owner = str(project.get("owner_id")) == assigned_id_str
            members = db.select_by_field("project_members", "project_id", project_id)
            is_assignee_member = any(
                str(m.get("student_id")) == assigned_id_str for m in members
            )
            if not is_assignee_owner and not is_assignee_member:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Assigned student must be an active project owner or accepted team member.",
                )
            assigned_student_rec = db.select_by_id("students", assigned_id_str)
            if assigned_student_rec:
                assigned_name = assigned_student_rec.get("full_name")

        now_ts = _now_iso()
        completed_ts = now_ts if payload.status == "completed" else None

        record = {
            "project_id": project_id,
            "title": payload.title,
            "description": payload.description,
            "assigned_student_id": (
                str(payload.assigned_student_id)
                if payload.assigned_student_id
                else None
            ),
            "status": payload.status,
            "priority": payload.priority,
            "due_date": payload.due_date.isoformat() if payload.due_date else None,
            "completed_at": completed_ts,
            "created_by": student_id,
            "created_at": now_ts,
            "updated_at": now_ts,
        }
        created = db.insert("project_tasks", record)
        return self._format_task(created, assigned_name=assigned_name, creator_name=student.get("full_name"))

    def get_project_tasks(
        self, project_id: str, user_id: str
    ) -> List[ProjectTaskResponse]:
        """List tasks for an authenticated team project."""
        if project_id.startswith("00000000-de00"):
            return self._get_demo_tasks(project_id)

        self._verify_membership(project_id, user_id)
        tasks = db.select_by_field("project_tasks", "project_id", project_id)
        tasks.sort(key=lambda x: str(x.get("created_at", "")), reverse=True)
        return [self._format_task(t) for t in tasks]

    def update_task(
        self, project_id: str, task_id: str, user_id: str, payload: ProjectTaskUpdate
    ) -> ProjectTaskResponse:
        """Update an existing task."""
        if project_id.startswith("00000000-de00"):
            return self._update_demo_task(project_id, task_id, payload)

        student, project, is_owner = self._verify_membership(project_id, user_id)
        student_id = str(student["id"])

        task = db.select_by_id("project_tasks", task_id)
        if not task or str(task.get("project_id")) != project_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task not found with ID: {task_id}",
            )

        # Authorized if owner, creator, or assigned member
        is_creator = str(task.get("created_by")) == student_id
        is_assigned = str(task.get("assigned_student_id")) == student_id
        if not is_owner and not is_creator and not is_assigned:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized: Only the project owner, task creator, or assigned member can update this task.",
            )

        updates: Dict[str, Any] = {"updated_at": _now_iso()}
        if payload.title is not None:
            updates["title"] = payload.title
        if payload.description is not None:
            updates["description"] = payload.description
        if payload.priority is not None:
            updates["priority"] = payload.priority
        if payload.due_date is not None:
            updates["due_date"] = payload.due_date.isoformat()
        if payload.assigned_student_id is not None:
            updates["assigned_student_id"] = str(payload.assigned_student_id)

        if payload.status is not None:
            updates["status"] = payload.status
            if payload.status == "completed" and not task.get("completed_at"):
                updates["completed_at"] = _now_iso()
            elif payload.status != "completed":
                updates["completed_at"] = None

        updated = db.update("project_tasks", task_id, updates)
        return self._format_task(updated or {**task, **updates})

    def delete_task(self, project_id: str, task_id: str, user_id: str) -> Dict[str, str]:
        """Delete a task (Owner or creator only)."""
        if project_id.startswith("00000000-de00"):
            if task_id in _demo_tasks_store:
                del _demo_tasks_store[task_id]
            return {"status": "success", "message": "Demo task deleted"}

        student, _, is_owner = self._verify_membership(project_id, user_id)
        student_id = str(student["id"])

        task = db.select_by_id("project_tasks", task_id)
        if not task or str(task.get("project_id")) != project_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task not found with ID: {task_id}",
            )

        is_creator = str(task.get("created_by")) == student_id
        if not is_owner and not is_creator:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized: Only the project owner or task creator can delete this task.",
            )

        db.delete("project_tasks", task_id)
        return {"status": "success", "message": "Task deleted successfully"}

    # --------------------------------------------------------------------------
    # Progress & Milestones
    # --------------------------------------------------------------------------
    def create_progress_update(
        self, project_id: str, user_id: str, payload: ProjectProgressCreate
    ) -> ProjectProgressResponse:
        """Create a progress checkpoint update."""
        if project_id.startswith("00000000-de00"):
            return self._create_demo_progress(project_id, payload)

        student, _, _ = self._verify_membership(project_id, user_id)
        student_id = str(student["id"])
        now_ts = _now_iso()
        completed_ts = now_ts if payload.status == "completed" or payload.progress_percentage == 100 else None

        record = {
            "project_id": project_id,
            "title": payload.title,
            "description": payload.description,
            "progress_percentage": payload.progress_percentage,
            "status": payload.status,
            "created_by": student_id,
            "created_at": now_ts,
            "updated_at": now_ts,
            "completed_at": completed_ts,
        }
        created = db.insert("project_progress", record)
        return self._format_progress(created, creator_name=student.get("full_name"))

    def get_project_progress_overview(
        self, project_id: str, user_id: str
    ) -> ProjectProgressOverviewResponse:
        """Retrieve overall progress overview, milestone updates, and tasks."""
        if project_id.startswith("00000000-de00"):
            return self._get_demo_progress_overview(project_id)

        self._verify_membership(project_id, user_id)

        tasks = db.select_by_field("project_tasks", "project_id", project_id)
        updates = db.select_by_field("project_progress", "project_id", project_id)

        tasks.sort(key=lambda x: str(x.get("created_at", "")), reverse=True)
        updates.sort(key=lambda x: str(x.get("created_at", "")), reverse=True)

        total_tasks = len(tasks)
        completed_tasks = sum(1 for t in tasks if t.get("status") == "completed")
        in_progress_tasks = sum(1 for t in tasks if t.get("status") == "in_progress")
        blocked_tasks = sum(1 for t in tasks if t.get("status") == "blocked")
        todo_tasks = sum(1 for t in tasks if t.get("status") == "todo")

        # Overall completion percentage:
        # If tasks exist, compute based on completed task ratio; blend with latest progress update
        if total_tasks > 0:
            task_ratio = (completed_tasks / total_tasks) * 100
            overall_pct = int(task_ratio)
        elif updates:
            overall_pct = int(updates[0].get("progress_percentage", 0))
        else:
            overall_pct = 0

        latest_status = updates[0].get("status", "on_track") if updates else "on_track"

        return ProjectProgressOverviewResponse(
            project_id=UUID(project_id),
            overall_progress_percentage=overall_pct,
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            in_progress_tasks=in_progress_tasks,
            blocked_tasks=blocked_tasks,
            todo_tasks=todo_tasks,
            latest_milestone_status=latest_status,
            tasks=[self._format_task(t) for t in tasks],
            updates=[self._format_progress(u) for u in updates],
        )

    def update_progress_update(
        self, project_id: str, progress_id: str, user_id: str, payload: ProjectProgressUpdate
    ) -> ProjectProgressResponse:
        """Update a progress checkpoint."""
        if project_id.startswith("00000000-de00"):
            return self._update_demo_progress(project_id, progress_id, payload)

        student, _, is_owner = self._verify_membership(project_id, user_id)
        student_id = str(student["id"])

        prog = db.select_by_id("project_progress", progress_id)
        if not prog or str(prog.get("project_id")) != project_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Progress record not found with ID: {progress_id}",
            )

        if not is_owner and str(prog.get("created_by")) != student_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized: Only the project owner or record author can update this progress record.",
            )

        updates: Dict[str, Any] = {"updated_at": _now_iso()}
        if payload.title is not None:
            updates["title"] = payload.title
        if payload.description is not None:
            updates["description"] = payload.description
        if payload.progress_percentage is not None:
            updates["progress_percentage"] = payload.progress_percentage
        if payload.status is not None:
            updates["status"] = payload.status

        updated = db.update("project_progress", progress_id, updates)
        return self._format_progress(updated or {**prog, **updates})

    def delete_progress_update(
        self, project_id: str, progress_id: str, user_id: str
    ) -> Dict[str, str]:
        """Delete a progress record (Owner only)."""
        if project_id.startswith("00000000-de00"):
            if progress_id in _demo_progress_store:
                del _demo_progress_store[progress_id]
            return {"status": "success", "message": "Demo progress record deleted"}

        _, _, is_owner = self._verify_membership(project_id, user_id)
        if not is_owner:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized: Only the project owner can delete progress updates.",
            )

        db.delete("project_progress", progress_id)
        return {"status": "success", "message": "Progress update deleted successfully"}

    # --------------------------------------------------------------------------
    # Formatters
    # --------------------------------------------------------------------------
    def _format_task(
        self,
        t: Dict[str, Any],
        assigned_name: Optional[str] = None,
        creator_name: Optional[str] = None,
    ) -> ProjectTaskResponse:
        assigned_id = t.get("assigned_student_id")
        created_by_id = t.get("created_by")

        if not assigned_name and assigned_id:
            s_rec = db.select_by_id("students", str(assigned_id))
            if s_rec:
                assigned_name = s_rec.get("full_name")

        if not creator_name and created_by_id:
            c_rec = db.select_by_id("students", str(created_by_id))
            if c_rec:
                creator_name = c_rec.get("full_name")

        created_dt = t.get("created_at")
        if isinstance(created_dt, str):
            created_dt = datetime.fromisoformat(created_dt.replace("Z", "+00:00"))

        updated_dt = t.get("updated_at")
        if isinstance(updated_dt, str):
            updated_dt = datetime.fromisoformat(updated_dt.replace("Z", "+00:00"))

        due_dt = t.get("due_date")
        if isinstance(due_dt, str):
            due_dt = datetime.fromisoformat(due_dt.replace("Z", "+00:00"))

        completed_dt = t.get("completed_at")
        if isinstance(completed_dt, str):
            completed_dt = datetime.fromisoformat(completed_dt.replace("Z", "+00:00"))

        return ProjectTaskResponse(
            id=UUID(str(t["id"])),
            project_id=UUID(str(t["project_id"])),
            title=t["title"],
            description=t.get("description"),
            assigned_student_id=UUID(str(assigned_id)) if assigned_id else None,
            assigned_student_name=assigned_name,
            status=t.get("status", "todo"),
            priority=t.get("priority", "medium"),
            due_date=due_dt,
            completed_at=completed_dt,
            created_by=UUID(str(created_by_id)) if created_by_id else UUID("00000000-0000-0000-0000-000000000000"),
            created_by_name=creator_name,
            created_at=created_dt,
            updated_at=updated_dt,
        )

    def _format_progress(
        self, p: Dict[str, Any], creator_name: Optional[str] = None
    ) -> ProjectProgressResponse:
        created_by_id = p.get("created_by")
        if not creator_name and created_by_id:
            c_rec = db.select_by_id("students", str(created_by_id))
            if c_rec:
                creator_name = c_rec.get("full_name")

        created_dt = p.get("created_at")
        if isinstance(created_dt, str):
            created_dt = datetime.fromisoformat(created_dt.replace("Z", "+00:00"))

        updated_dt = p.get("updated_at")
        if isinstance(updated_dt, str):
            updated_dt = datetime.fromisoformat(updated_dt.replace("Z", "+00:00"))

        completed_dt = p.get("completed_at")
        if isinstance(completed_dt, str):
            completed_dt = datetime.fromisoformat(completed_dt.replace("Z", "+00:00"))

        return ProjectProgressResponse(
            id=UUID(str(p["id"])),
            project_id=UUID(str(p["project_id"])),
            title=p["title"],
            description=p.get("description"),
            progress_percentage=p.get("progress_percentage", 0),
            status=p.get("status", "on_track"),
            created_by=UUID(str(created_by_id)) if created_by_id else UUID("00000000-0000-0000-0000-000000000000"),
            created_by_name=creator_name,
            created_at=created_dt,
            updated_at=updated_dt,
            completed_at=completed_dt,
        )

    # --------------------------------------------------------------------------
    # Demo Mode Implementations (Zero Supabase Writes)
    # --------------------------------------------------------------------------
    def _create_demo_task(
        self, project_id: str, payload: ProjectTaskCreate
    ) -> ProjectTaskResponse:
        _init_demo_seeds(project_id)
        now = _now_iso()
        t_id = str(uuid.uuid4())
        record = {
            "id": t_id,
            "project_id": project_id,
            "title": payload.title,
            "description": payload.description,
            "assigned_student_id": (
                str(payload.assigned_student_id)
                if payload.assigned_student_id
                else None
            ),
            "status": payload.status,
            "priority": payload.priority,
            "due_date": payload.due_date.isoformat() if payload.due_date else None,
            "completed_at": now if payload.status == "completed" else None,
            "created_by": "00000000-de00-0000-0000-000000000001",
            "created_at": now,
            "updated_at": now,
        }
        _demo_tasks_store[t_id] = record
        return self._format_task(record, assigned_name="Student Candidate (Demo)", creator_name="Student A (Demo)")

    def _get_demo_tasks(self, project_id: str) -> List[ProjectTaskResponse]:
        _init_demo_seeds(project_id)
        items = [t for t in _demo_tasks_store.values() if t["project_id"] == project_id]
        return [self._format_task(t, assigned_name="Team Member (Demo)", creator_name="Student A (Demo)") for t in items]

    def _update_demo_task(
        self, project_id: str, task_id: str, payload: ProjectTaskUpdate
    ) -> ProjectTaskResponse:
        _init_demo_seeds(project_id)
        if task_id not in _demo_tasks_store:
            raise HTTPException(status_code=404, detail="Demo task not found")
        task = _demo_tasks_store[task_id]
        if payload.title is not None:
            task["title"] = payload.title
        if payload.description is not None:
            task["description"] = payload.description
        if payload.status is not None:
            task["status"] = payload.status
            task["completed_at"] = _now_iso() if payload.status == "completed" else None
        if payload.priority is not None:
            task["priority"] = payload.priority
        if payload.assigned_student_id is not None:
            task["assigned_student_id"] = str(payload.assigned_student_id)
        task["updated_at"] = _now_iso()
        return self._format_task(task, assigned_name="Team Member (Demo)", creator_name="Student A (Demo)")

    def _create_demo_progress(
        self, project_id: str, payload: ProjectProgressCreate
    ) -> ProjectProgressResponse:
        _init_demo_seeds(project_id)
        now = _now_iso()
        p_id = str(uuid.uuid4())
        record = {
            "id": p_id,
            "project_id": project_id,
            "title": payload.title,
            "description": payload.description,
            "progress_percentage": payload.progress_percentage,
            "status": payload.status,
            "created_by": "00000000-de00-0000-0000-000000000001",
            "created_at": now,
            "updated_at": now,
            "completed_at": now if payload.status == "completed" else None,
        }
        _demo_progress_store[p_id] = record
        return self._format_progress(record, creator_name="Student A (Demo)")

    def _get_demo_progress_overview(
        self, project_id: str
    ) -> ProjectProgressOverviewResponse:
        _init_demo_seeds(project_id)
        tasks = [t for t in _demo_tasks_store.values() if t["project_id"] == project_id]
        updates = [u for u in _demo_progress_store.values() if u["project_id"] == project_id]

        total_tasks = len(tasks)
        completed_tasks = sum(1 for t in tasks if t.get("status") == "completed")
        in_progress_tasks = sum(1 for t in tasks if t.get("status") == "in_progress")
        blocked_tasks = sum(1 for t in tasks if t.get("status") == "blocked")
        todo_tasks = sum(1 for t in tasks if t.get("status") == "todo")

        overall_pct = int((completed_tasks / total_tasks * 100)) if total_tasks > 0 else 50
        latest_status = updates[0].get("status", "on_track") if updates else "on_track"

        return ProjectProgressOverviewResponse(
            project_id=UUID(project_id),
            overall_progress_percentage=overall_pct,
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            in_progress_tasks=in_progress_tasks,
            blocked_tasks=blocked_tasks,
            todo_tasks=todo_tasks,
            latest_milestone_status=latest_status,
            tasks=[self._format_task(t, assigned_name="Team Member (Demo)", creator_name="Student A (Demo)") for t in tasks],
            updates=[self._format_progress(u, creator_name="Student A (Demo)") for u in updates],
        )

    def _update_demo_progress(
        self, project_id: str, progress_id: str, payload: ProjectProgressUpdate
    ) -> ProjectProgressResponse:
        _init_demo_seeds(project_id)
        if progress_id not in _demo_progress_store:
            raise HTTPException(status_code=404, detail="Demo progress record not found")
        prog = _demo_progress_store[progress_id]
        if payload.title is not None:
            prog["title"] = payload.title
        if payload.description is not None:
            prog["description"] = payload.description
        if payload.progress_percentage is not None:
            prog["progress_percentage"] = payload.progress_percentage
        if payload.status is not None:
            prog["status"] = payload.status
        prog["updated_at"] = _now_iso()
        return self._format_progress(prog, creator_name="Student A (Demo)")


progress_service = ProgressService()
