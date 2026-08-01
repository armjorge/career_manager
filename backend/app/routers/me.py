from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Request

from app.auth import get_current_user_id

router = APIRouter(tags=["me"])


@router.get("/me")
def me(
    request: Request,
    user_id: UUID = Depends(get_current_user_id),
) -> dict[str, Any]:
    event = request.scope.get("aws.event") or {}
    claims = (
        event.get("requestContext", {})
        .get("authorizer", {})
        .get("jwt", {})
        .get("claims", {})
    )
    email = claims.get("email") if isinstance(claims, dict) else None
    return {
        "authenticated": True,
        "sub": str(user_id),
        "email": email,
    }
