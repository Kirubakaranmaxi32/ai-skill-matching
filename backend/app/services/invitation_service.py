"""
Invitation Service
==================
Implements voluntary team formation workflows:
- Project owners send invitations to recommended candidates.
- Candidates review received invitations in an inbox.
- Voluntary acceptance (adds student to project_members as 'member').
- Rejection (does not add student).
- Project owner cancellation of pending invitations.
- Prevents duplicate pending invitations and self-invitation.
- Strict authorization and IDOR protection.
- Isolated in-memory Demo Mode support.
"""

from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime, timezone
import uuid
from fastapi import HTTPException, status

from app.services.db_adapter import db, _now_iso
from app.services.student_service import get_or_create_student
from app.schemas.invitation import (
    InvitationResponse,
    InvitationStatus,
    SafeProjectSummary,
    SafeStudentSummary,
)

# In-memory store for Demo Mode invitations to guarantee zero Supabase writes
_demo_invitations_store: Dict[str, Dict[str, Any]] = {}


def reset_demo_invitations() -> None:
    """Helper to clear local demo invitations."""
    _demo_invitations_store.clear()


class InvitationService:
    """Service orchestrating voluntary team invitations and membership."""

    # --------------------------------------------------------------------------
    # Helper: Enrichment
    # --------------------------------------------------------------------------
    def _enrich_invitation(self, inv: Dict[str, Any], is_demo: bool = False) -> InvitationResponse:
        """Enriches raw invitation dict with sanitized project and student details."""
        proj_id = str(inv["project_id"])
        inviter_id = str(inv["inviter_id"])
        invited_id = str(inv["invited_student_id"])

        if is_demo or proj_id.startswith("00000000-de00"):
            from app.services.demo_service import load_demo_projects, load_demo_students
            projects = {str(p["id"]): p for p in load_demo_projects()}
            students = {str(s["id"]): s for s in load_demo_students()}

            p = projects.get(proj_id, {})
            inviter = students.get(inviter_id, {})
            invited = students.get(invited_id, {})

            proj_summary = SafeProjectSummary(
                id=UUID(proj_id),
                title=p.get("title", "Demo Project"),
                description=p.get("description", ""),
                status=p.get("status", "open"),
                owner_id=UUID(str(p.get("owner_id", inviter_id))),
            )
            inviter_summary = SafeStudentSummary(
                id=UUID(inviter_id),
                full_name=inviter.get("full_name", "Student Inviter (Demo)"),
                academic_year=inviter.get("academic_year"),
                department=inviter.get("department"),
            )
            invited_summary = SafeStudentSummary(
                id=UUID(invited_id),
                full_name=invited.get("full_name", "Student Candidate (Demo)"),
                academic_year=invited.get("academic_year"),
                department=invited.get("department"),
            )
        else:
            p_rec = db.select_by_id("projects", proj_id) or {}
            inviter_rec = db.select_by_id("students", inviter_id) or {}
            invited_rec = db.select_by_id("students", invited_id) or {}

            proj_summary = SafeProjectSummary(
                id=UUID(proj_id),
                title=p_rec.get("title", "Project"),
                description=p_rec.get("description", ""),
                status=p_rec.get("status", "open"),
                owner_id=UUID(str(p_rec.get("owner_id", inviter_id))),
            )
            inviter_summary = SafeStudentSummary(
                id=UUID(inviter_id),
                full_name=inviter_rec.get("full_name", "Student Inviter"),
                academic_year=inviter_rec.get("academic_year"),
                department=inviter_rec.get("department"),
            )
            invited_summary = SafeStudentSummary(
                id=UUID(invited_id),
                full_name=invited_rec.get("full_name", "Student Candidate"),
                academic_year=invited_rec.get("academic_year"),
                department=invited_rec.get("department"),
            )

        created_dt = inv.get("created_at")
        if isinstance(created_dt, str):
            created_dt = datetime.fromisoformat(created_dt.replace("Z", "+00:00"))

        updated_dt = inv.get("updated_at")
        if isinstance(updated_dt, str):
            updated_dt = datetime.fromisoformat(updated_dt.replace("Z", "+00:00"))

        resp_dt = inv.get("responded_at")
        if isinstance(resp_dt, str):
            resp_dt = datetime.fromisoformat(resp_dt.replace("Z", "+00:00"))

        return InvitationResponse(
            id=UUID(str(inv["id"])),
            project_id=UUID(proj_id),
            inviter_id=UUID(inviter_id),
            invited_student_id=UUID(invited_id),
            status=InvitationStatus(inv["status"]),
            created_at=created_dt,
            updated_at=updated_dt,
            responded_at=resp_dt,
            project=proj_summary,
            inviter=inviter_summary,
            invited_student=invited_summary,
        )

    # --------------------------------------------------------------------------
    # 1. Create Invitation
    # --------------------------------------------------------------------------
    def create_invitation(
        self,
        project_id: str,
        user_id: str,
        target_student_id: str,
    ) -> InvitationResponse:
        """
        Allows project owner to send an invitation to an eligible candidate.
        """
        # Demo mode intercept
        if project_id.startswith("00000000-de00"):
            return self._create_demo_invitation(project_id, target_student_id)

        # 1. Look up authenticated student
        sender_student = get_or_create_student(user_id)
        sender_student_id = str(sender_student["id"])

        # 2. Look up project
        project = db.select_by_id("projects", project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project not found with ID: {project_id}",
            )

        # 3. Project status must be open
        if project.get("status") != "open":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot invite members to a project with status '{project.get('status')}'. Project must be 'open'.",
            )

        # 4. Authenticated user must be project owner
        if str(project.get("owner_id")) != sender_student_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized: Only the project owner can send invitations.",
            )

        # 5. Target student must exist
        target_student = db.select_by_id("students", target_student_id)
        if not target_student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidate student not found with ID: {target_student_id}",
            )

        # 6. Target student cannot be the project owner
        if str(target_student["id"]) == sender_student_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot invite yourself. You are already the project owner.",
            )

        # 7. Target student cannot already be a project member
        members = db.select_by_field("project_members", "project_id", project_id)
        if any(str(m.get("student_id")) == target_student_id for m in members):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Candidate is already a team member of this project.",
            )

        # 8. Check for existing pending invitation
        existing_invs = db.select_by_field("invitations", "project_id", project_id)
        if any(
            str(inv.get("invited_student_id")) == target_student_id
            and inv.get("status") == "pending"
            for inv in existing_invs
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An active pending invitation already exists for this candidate.",
            )

        # 9. Insert invitation
        now_ts = _now_iso()
        inv_record = {
            "project_id": project_id,
            "inviter_id": sender_student_id,
            "invited_student_id": target_student_id,
            "status": "pending",
            "created_at": now_ts,
            "updated_at": now_ts,
            "responded_at": None,
        }
        created = db.insert("invitations", inv_record)
        return self._enrich_invitation(created, is_demo=False)

    # --------------------------------------------------------------------------
    # 2. List Invitations (for authenticated student)
    # --------------------------------------------------------------------------
    def get_my_invitations(
        self,
        user_id: str,
        status_filter: Optional[str] = None,
        role_filter: str = "received",
    ) -> List[InvitationResponse]:
        """
        Retrieves invitations where current student is recipient ('received') or sender ('sent').
        """
        student = get_or_create_student(user_id)
        student_id = str(student["id"])

        if role_filter == "sent":
            invs = db.select_by_field("invitations", "inviter_id", student_id)
        else:
            invs = db.select_by_field("invitations", "invited_student_id", student_id)

        if status_filter:
            invs = [i for i in invs if i.get("status") == status_filter]

        # Sort newest first
        invs.sort(key=lambda x: str(x.get("created_at", "")), reverse=True)
        return [self._enrich_invitation(i, is_demo=False) for i in invs]

    # --------------------------------------------------------------------------
    # 3. Project Invitations (for project owner)
    # --------------------------------------------------------------------------
    def get_project_invitations(
        self,
        project_id: str,
        user_id: str,
    ) -> List[InvitationResponse]:
        """
        Retrieves all invitations for a project. Accessible strictly to project owner.
        """
        if project_id.startswith("00000000-de00"):
            return self._get_demo_project_invitations(project_id)

        project = db.select_by_id("projects", project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project not found with ID: {project_id}",
            )

        student = get_or_create_student(user_id)
        if str(project.get("owner_id")) != str(student["id"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized: Only the project owner can view invitations for this project.",
            )

        invs = db.select_by_field("invitations", "project_id", project_id)
        invs.sort(key=lambda x: str(x.get("created_at", "")), reverse=True)
        return [self._enrich_invitation(i, is_demo=False) for i in invs]

    # --------------------------------------------------------------------------
    # 4. Accept Invitation (Voluntary Team Formation)
    # --------------------------------------------------------------------------
    def accept_invitation(self, invitation_id: str, user_id: str) -> InvitationResponse:
        """
        Invited student accepts the invitation.
        Adds student to project_members with role='member'.
        """
        # Demo mode check
        if invitation_id in _demo_invitations_store:
            return self._accept_demo_invitation(invitation_id)

        inv = db.select_by_id("invitations", invitation_id)
        if not inv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Invitation not found with ID: {invitation_id}",
            )

        student = get_or_create_student(user_id)
        student_id = str(student["id"])

        # 1. Authorization: user must be the invited student
        if str(inv.get("invited_student_id")) != student_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized: Only the invited student can accept this invitation.",
            )

        # 2. Status must be pending
        curr_status = inv.get("status")
        if curr_status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot accept invitation. Current status is '{curr_status}'.",
            )

        # 3. Project must exist and permit joining
        project_id = str(inv["project_id"])
        project = db.select_by_id("projects", project_id)
        if not project or project.get("status") in ["archived", "completed"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot join project: project is completed or archived.",
            )

        # 4. Atomic updates: Add to project_members if not already member
        now_ts = _now_iso()
        existing_members = db.select_by_field("project_members", "project_id", project_id)
        if not any(str(m.get("student_id")) == student_id for m in existing_members):
            db.insert("project_members", {
                "project_id": project_id,
                "student_id": student_id,
                "role": "member",
                "joined_at": now_ts,
            })

        # 5. Update invitation status
        updated = db.update("invitations", invitation_id, {
            "status": "accepted",
            "responded_at": now_ts,
            "updated_at": now_ts,
        })
        return self._enrich_invitation(updated, is_demo=False)

    # --------------------------------------------------------------------------
    # 5. Reject Invitation
    # --------------------------------------------------------------------------
    def reject_invitation(self, invitation_id: str, user_id: str) -> InvitationResponse:
        """
        Invited student declines the invitation.
        Does NOT add student to project_members.
        """
        if invitation_id in _demo_invitations_store:
            return self._reject_demo_invitation(invitation_id)

        inv = db.select_by_id("invitations", invitation_id)
        if not inv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Invitation not found with ID: {invitation_id}",
            )

        student = get_or_create_student(user_id)
        student_id = str(student["id"])

        if str(inv.get("invited_student_id")) != student_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized: Only the invited student can reject this invitation.",
            )

        curr_status = inv.get("status")
        if curr_status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot reject invitation. Current status is '{curr_status}'.",
            )

        now_ts = _now_iso()
        updated = db.update("invitations", invitation_id, {
            "status": "rejected",
            "responded_at": now_ts,
            "updated_at": now_ts,
        })
        return self._enrich_invitation(updated, is_demo=False)

    # --------------------------------------------------------------------------
    # 6. Cancel Invitation
    # --------------------------------------------------------------------------
    def cancel_invitation(self, invitation_id: str, user_id: str) -> InvitationResponse:
        """
        Project owner cancels a pending invitation before response.
        """
        if invitation_id in _demo_invitations_store:
            return self._cancel_demo_invitation(invitation_id)

        inv = db.select_by_id("invitations", invitation_id)
        if not inv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Invitation not found with ID: {invitation_id}",
            )

        student = get_or_create_student(user_id)
        student_id = str(student["id"])

        project = db.select_by_id("projects", str(inv["project_id"]))
        if not project or str(project.get("owner_id")) != student_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized: Only the project owner can cancel this invitation.",
            )

        curr_status = inv.get("status")
        if curr_status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel invitation. Current status is '{curr_status}'.",
            )

        now_ts = _now_iso()
        updated = db.update("invitations", invitation_id, {
            "status": "cancelled",
            "responded_at": now_ts,
            "updated_at": now_ts,
        })
        return self._enrich_invitation(updated, is_demo=False)

    # --------------------------------------------------------------------------
    # Demo Mode Isolated Operations (Zero Supabase Access)
    # --------------------------------------------------------------------------
    def _create_demo_invitation(self, project_id: str, target_student_id: str) -> InvitationResponse:
        from app.services.demo_service import load_demo_projects, load_demo_students
        projects = {str(p["id"]): p for p in load_demo_projects()}
        students = {str(s["id"]): s for s in load_demo_students()}

        if project_id not in projects:
            raise HTTPException(status_code=404, detail="Demo project not found")
        if target_student_id not in students:
            raise HTTPException(status_code=404, detail="Demo candidate student not found")

        demo_p = projects[project_id]
        owner_id = str(demo_p["owner_id"])

        if target_student_id == owner_id:
            raise HTTPException(status_code=400, detail="Cannot invite yourself. You are the project owner.")

        # Check existing pending demo invitation
        for inv in _demo_invitations_store.values():
            if (
                inv["project_id"] == project_id
                and inv["invited_student_id"] == target_student_id
                and inv["status"] == "pending"
            ):
                raise HTTPException(status_code=409, detail="An active pending invitation already exists for this candidate.")

        now_ts = _now_iso()
        inv_id = str(uuid.uuid4())
        record = {
            "id": inv_id,
            "project_id": project_id,
            "inviter_id": owner_id,
            "invited_student_id": target_student_id,
            "status": "pending",
            "created_at": now_ts,
            "updated_at": now_ts,
            "responded_at": None,
        }
        _demo_invitations_store[inv_id] = record
        return self._enrich_invitation(record, is_demo=True)

    def _get_demo_project_invitations(self, project_id: str) -> List[InvitationResponse]:
        results = [
            self._enrich_invitation(inv, is_demo=True)
            for inv in _demo_invitations_store.values()
            if inv["project_id"] == project_id
        ]
        return results

    def _accept_demo_invitation(self, invitation_id: str) -> InvitationResponse:
        inv = _demo_invitations_store[invitation_id]
        if inv["status"] != "pending":
            raise HTTPException(status_code=400, detail=f"Cannot accept invitation in '{inv['status']}' status.")
        now_ts = _now_iso()
        inv["status"] = "accepted"
        inv["responded_at"] = now_ts
        inv["updated_at"] = now_ts
        return self._enrich_invitation(inv, is_demo=True)

    def _reject_demo_invitation(self, invitation_id: str) -> InvitationResponse:
        inv = _demo_invitations_store[invitation_id]
        if inv["status"] != "pending":
            raise HTTPException(status_code=400, detail=f"Cannot reject invitation in '{inv['status']}' status.")
        now_ts = _now_iso()
        inv["status"] = "rejected"
        inv["responded_at"] = now_ts
        inv["updated_at"] = now_ts
        return self._enrich_invitation(inv, is_demo=True)

    def _cancel_demo_invitation(self, invitation_id: str) -> InvitationResponse:
        inv = _demo_invitations_store[invitation_id]
        if inv["status"] != "pending":
            raise HTTPException(status_code=400, detail=f"Cannot cancel invitation in '{inv['status']}' status.")
        now_ts = _now_iso()
        inv["status"] = "cancelled"
        inv["responded_at"] = now_ts
        inv["updated_at"] = now_ts
        return self._enrich_invitation(inv, is_demo=True)


invitation_service = InvitationService()
