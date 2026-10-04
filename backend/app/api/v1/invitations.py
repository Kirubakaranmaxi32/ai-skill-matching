"""
Invitation API Router
=====================
Defines endpoints for Phase 13: Voluntary Team Formation & Invitations:
- Candidate inbox: GET /api/v1/invitations (list received/sent invitations)
- Voluntary acceptance: POST /api/v1/invitations/{id}/accept
- Voluntary rejection: POST /api/v1/invitations/{id}/reject
- Project owner cancellation: POST /api/v1/invitations/{id}/cancel
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status

from app.core.auth import get_current_user
from app.schemas.invitation import (
    InvitationResponse,
    InvitationStatus,
)
from app.services.invitation_service import invitation_service

router = APIRouter(prefix="/invitations", tags=["Invitations"])


@router.get(
    "",
    response_model=List[InvitationResponse],
    summary="List invitations for authenticated student",
)
async def list_my_invitations(
    status_filter: Optional[InvitationStatus] = Query(
        None,
        alias="status",
        description="Filter by invitation status (pending, accepted, rejected, cancelled)",
    ),
    role: str = Query(
        "received",
        pattern="^(received|sent)$",
        description="Filter by 'received' (inbox) or 'sent' (outbox)",
    ),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> List[InvitationResponse]:
    """
    Retrieves project invitations where the current student is either:
    - the recipient candidate ('received' - default inbox view)
    - the sending project owner ('sent' - outbox view)
    """
    return invitation_service.get_my_invitations(
        user_id=current_user["id"],
        status_filter=status_filter.value if status_filter else None,
        role_filter=role,
    )


@router.post(
    "/{invitation_id}/accept",
    response_model=InvitationResponse,
    summary="Accept a project invitation (Voluntary Team Formation)",
)
async def accept_invitation(
    invitation_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> InvitationResponse:
    """
    Voluntary acceptance by the invited student:
    1. Verifies the caller is the invited student.
    2. Validates invitation is pending and project is active.
    3. Atomically adds the student to project_members with role='member'.
    4. Updates invitation status to 'accepted'.
    """
    return invitation_service.accept_invitation(
        invitation_id=str(invitation_id),
        user_id=current_user["id"],
    )


@router.post(
    "/{invitation_id}/reject",
    response_model=InvitationResponse,
    summary="Decline a project invitation",
)
async def reject_invitation(
    invitation_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> InvitationResponse:
    """
    Voluntary decline by the invited student:
    1. Verifies the caller is the invited student.
    2. Updates invitation status to 'rejected'.
    3. Does NOT modify project_members.
    """
    return invitation_service.reject_invitation(
        invitation_id=str(invitation_id),
        user_id=current_user["id"],
    )


@router.post(
    "/{invitation_id}/cancel",
    response_model=InvitationResponse,
    summary="Cancel a pending project invitation (Project Owner only)",
)
async def cancel_invitation(
    invitation_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> InvitationResponse:
    """
    Withdrawal by the project owner:
    1. Verifies caller is the project owner.
    2. Updates invitation status from 'pending' to 'cancelled'.
    """
    return invitation_service.cancel_invitation(
        invitation_id=str(invitation_id),
        user_id=current_user["id"],
    )
