"""
Matching & Compatibility API Endpoints
======================================
Provides protected endpoints for evaluating single-pair compatibility between
students and projects using the trained PyTorch MLP model.
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, status

from app.core.auth import get_current_user
from app.schemas.matching import CompatibilityRequest, CompatibilityResponse
from app.services.matching_service import matching_service

router = APIRouter(prefix="/matching", tags=["Matching & Compatibility"])


@router.post(
    "/compatibility",
    response_model=CompatibilityResponse,
    status_code=status.HTTP_200_OK,
    summary="Evaluate student-project compatibility using PyTorch MLP",
)
async def evaluate_compatibility(
    request: CompatibilityRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> CompatibilityResponse:
    """
    Evaluates compatibility between a single student and project:
    1. Authenticates request via Supabase JWT.
    2. Enforces privacy rules (students can assess themselves; owners can assess candidates).
    3. Engineers 10-dimensional normalized feature vector.
    4. Runs inference using the trained PyTorch CompatibilityMLP model on CPU.
    5. Returns compatibility score [0.0, 1.0] and feature contributions.
    """
    return matching_service.evaluate_compatibility(request, current_user["id"])
