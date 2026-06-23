"""Account profile: view current account, update username/password."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from api.deps import get_services, require_login

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("/profile")
def profile(user=Depends(require_login)):
    return {"id": user.id, "username": user.username, "full_name": user.full_name,
            "email": user.email, "phone": user.phone, "role_name": user.role_name}


class ProfileBody(BaseModel):
    username: str
    password: Optional[str] = None


@router.put("/profile")
def update_profile(body: ProfileBody, request: Request, user=Depends(require_login),
                   services=Depends(get_services)):
    result = services["auth"].update_own_profile(
        user.id, body.username.strip(), body.password or None)
    if not result.success:
        raise HTTPException(409, result.message)
    # Keep the session valid (uid unchanged); username may have changed.
    request.session["uid"] = user.id
    return {"success": True, "message": result.message}
