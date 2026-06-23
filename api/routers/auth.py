"""Authentication endpoints: login / logout / current-user (me)."""
from typing import Optional

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel

from api.deps import get_services, load_current_user
from api.config_api import SESSION_MAX_AGE, REMEMBER_MAX_AGE
from api.permissions import build_permission_map
from application.dto.user_dto import UserDTO

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginBody(BaseModel):
    username: str
    password: str
    remember: bool = False


def _user_public(user: UserDTO, services: dict) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "email": user.email,
        "phone": user.phone,
        "role_name": user.role_name,
        "permissions": build_permission_map(services["permission"]),
    }


@router.post("/login")
def login(body: LoginBody, request: Request, response: Response,
          services: dict = Depends(get_services)):
    result = services["auth"].login(body.username, body.password)
    if not result.success or not result.user:
        return {"success": False, "message": result.message}
    request.session["uid"] = result.user.id
    request.session["role"] = result.user.role_name
    # Starlette re-issues the cookie with the middleware's max_age; we set a flag
    # so the middleware (configured per-request) can choose the longer lifetime.
    request.session["remember"] = bool(body.remember)
    return {"success": True, "message": result.message,
            "user": _user_public(result.user, services)}


@router.post("/logout")
def logout(request: Request, services: dict = Depends(get_services)):
    services["auth"].logout()
    request.session.clear()
    return {"success": True}


@router.get("/me")
def me(request: Request,
       user: Optional[UserDTO] = Depends(load_current_user),
       services: dict = Depends(get_services)):
    if not user:
        return {"authenticated": False}
    return {"authenticated": True, "user": _user_public(user, services)}
