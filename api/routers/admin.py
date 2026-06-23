"""System administration (superadmin): users CRUD, audit logs, file-log viewer."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.deps import get_services
from api.permissions import require_role
from api.responses import export_response
from application.dto.user_dto import UserCreateDTO, UserDTO

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ----------------------------------------------------------------- users
@router.get("/roles")
def roles(user=Depends(require_role()), services=Depends(get_services)):
    return [{"value": rid, "label": name} for rid, name in services["auth"].get_all_roles()]


@router.get("/users")
def list_users(user=Depends(require_role()), services=Depends(get_services)):
    return [{"id": u.id, "username": u.username, "full_name": u.full_name,
             "email": u.email, "phone": u.phone, "role_id": u.role_id,
             "role_name": u.role_name, "is_active": u.is_active}
            for u in services["auth"].get_all_users()]


class UserCreateBody(BaseModel):
    username: str
    password: str
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    role_id: Optional[int] = None


class UserUpdateBody(BaseModel):
    username: str
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    role_id: Optional[int] = None
    is_active: bool = True
    password: Optional[str] = None


@router.post("/users")
def create_user(body: UserCreateBody, user=Depends(require_role()), services=Depends(get_services)):
    result = services["auth"].create_user(UserCreateDTO(**body.model_dump()))
    if not result.success:
        raise HTTPException(409, result.message)
    return {"success": True}


@router.put("/users/{uid}")
def update_user(uid: int, body: UserUpdateBody, user=Depends(require_role()),
                services=Depends(get_services)):
    dto = UserDTO(id=uid, username=body.username, full_name=body.full_name,
                  email=body.email, phone=body.phone, role_id=body.role_id,
                  is_active=body.is_active)
    result = services["auth"].update_user(uid, dto)
    if not result.success:
        raise HTTPException(409, result.message)
    if body.password:
        services["auth"].change_password(uid, body.password)
    return {"success": True}


@router.delete("/users/{uid}")
def delete_user(uid: int, user=Depends(require_role()), services=Depends(get_services)):
    if uid == user.id:
        raise HTTPException(409, "لا يمكنك حذف حسابك الحالي")
    try:
        services["auth"].delete_user(uid)
    except Exception:
        raise HTTPException(409, "تعذّر الحذف لارتباط الحساب بسجلات")
    return {"success": True}


# ----------------------------------------------------------------- audit logs
@router.get("/audit")
def audit_logs(user=Depends(require_role()), services=Depends(get_services)):
    out = []
    for log, username in services["audit"].get_all_logs()[:500]:
        out.append({
            "id": log.id,
            "timestamp": log.timestamp.strftime("%Y-%m-%d %H:%M:%S") if log.timestamp else "",
            "username": username or "System", "module": log.module,
            "action": log.action, "entity_type": log.entity_type or "-",
        })
    return out


@router.get("/audit/export")
def export_audit(fmt: str = "excel", user=Depends(require_role()), services=Depends(get_services)):
    headers = ["التاريخ والوقت", "المستخدم", "الوحدة", "الإجراء", "الكيان"]
    rows = []
    for log, username in services["audit"].get_all_logs():
        ts = log.timestamp.strftime("%Y-%m-%d %H:%M:%S") if log.timestamp else ""
        rows.append([ts, username or "System", log.module, log.action, log.entity_type or "-"])
    return export_response(services["report"], fmt, "audit_logs", headers, rows, "سجل العمليات")


# ----------------------------------------------------------------- file logs
@router.get("/logs/files")
def log_files(user=Depends(require_role())):
    from config.logging_config import list_log_files
    return [{"label": label, "path": str(path)} for label, path in list_log_files()]


@router.get("/logs/content")
def log_content(path: Optional[str] = None, user=Depends(require_role())):
    from config.logging_config import read_log_tail
    text = read_log_tail(path)
    return {"content": text}


@router.get("/logs/export")
def export_logs(path: Optional[str] = None, fmt: str = "excel",
                user=Depends(require_role()), services=Depends(get_services)):
    from config.logging_config import read_log_tail, parse_log_lines
    rows = parse_log_lines(read_log_tail(path))
    headers = ["الوقت", "المستوى", "المصدر", "الرسالة"]
    return export_response(services["report"], fmt, "full_logs", headers, rows, "السجل الكامل")
