"""Training programs CRUD + program detail (courses/workshops/sessions) +
trainees (single/bulk add with optional fee→revenue, xlsx import/template)."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel

from api.deps import get_services, require_perm
from api.responses import export_response, file_download, XLSX_MEDIA
from api.excel_io import parse_xlsx
from application.services.training_service import TrainingProgramDTO
from application.services.financial_service import TransactionDTO

router = APIRouter(prefix="/api/training", tags=["training"])
MODULE = "training"
TRAINEE_COLS = ["الاسم", "الجهة", "رقم الهاتف", "البريد"]


def _prog(p) -> dict:
    return {"id": p.id, "name": p.name, "description": p.description,
            "program_type": p.program_type,
            "start_date": p.start_date.isoformat() if p.start_date else None,
            "end_date": p.end_date.isoformat() if p.end_date else None,
            "total_hours": p.total_hours, "status": p.status}


def _d(s):
    from datetime import date
    if not s:
        return None
    try:
        return date.fromisoformat(s)
    except ValueError:
        return None


class ProgramBody(BaseModel):
    name: str
    description: Optional[str] = None
    program_type: str = "training"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    total_hours: Optional[int] = None
    status: str = "active"


@router.get("/programs")
def list_programs(user=Depends(require_perm(MODULE, "view")), services=Depends(get_services)):
    return [_prog(p) for p in services["training"].get_all_programs()]


@router.post("/programs")
def create_program(body: ProgramBody, user=Depends(require_perm(MODULE, "create")),
                   services=Depends(get_services)):
    if not body.name.strip():
        raise HTTPException(422, "اسم البرنامج مطلوب")
    dto = TrainingProgramDTO(name=body.name.strip(), description=body.description,
                             program_type=body.program_type, start_date=_d(body.start_date),
                             end_date=_d(body.end_date), total_hours=body.total_hours,
                             status=body.status)
    return _prog(services["training"].create_program(dto))


@router.put("/programs/{pid}")
def update_program(pid: int, body: ProgramBody, user=Depends(require_perm(MODULE, "edit")),
                   services=Depends(get_services)):
    dto = TrainingProgramDTO(id=pid, name=body.name.strip(), description=body.description,
                             program_type=body.program_type, start_date=_d(body.start_date),
                             end_date=_d(body.end_date), total_hours=body.total_hours,
                             status=body.status)
    p = services["training"].update_program(dto)
    if not p:
        raise HTTPException(404, "البرنامج غير موجود")
    return _prog(p)


@router.delete("/programs/{pid}")
def delete_program(pid: int, user=Depends(require_perm(MODULE, "delete")),
                   services=Depends(get_services)):
    services["training"].delete_program(pid)
    return {"success": True}


@router.get("/programs/export")
def export_programs(fmt: str = "excel", user=Depends(require_perm(MODULE, "view")),
                    services=Depends(get_services)):
    labels = {"training": "تدريب", "workshop": "ورشة", "course": "دورة"}
    headers = ["اسم البرنامج", "النوع", "تاريخ البداية", "تاريخ النهاية", "الساعات", "الحالة"]
    rows = [[p.name, labels.get(p.program_type, p.program_type),
             p.start_date.isoformat() if p.start_date else "-",
             p.end_date.isoformat() if p.end_date else "-", p.total_hours or "-", p.status]
            for p in services["training"].get_all_programs()]
    return export_response(services["report"], fmt, "training", headers, rows, "البرامج التدريبية")


# ----------------------------------------------------------- program detail
@router.get("/programs/{pid}/detail")
def program_detail(pid: int, user=Depends(require_perm(MODULE, "view")),
                   services=Depends(get_services)):
    t = services["training"]
    prog = t.get_program(pid)
    if not prog:
        raise HTTPException(404, "البرنامج غير موجود")
    courses = [{"id": c.id, "name": c.name, "description": c.description}
               for c in t.get_program_courses(pid)]
    workshops = [{"id": w.id, "name": w.name, "description": w.description}
                 for w in t.get_program_workshops(pid)]
    sessions = [{"id": s.id, "session_date": s.session_date.isoformat() if s.session_date else None,
                 "duration_hours": s.duration_hours, "topic": s.topic,
                 "course_id": s.course_id, "workshop_id": s.workshop_id}
                for s in t.get_program_sessions(pid)]
    return {"program": _prog(prog), "courses": courses, "workshops": workshops, "sessions": sessions}


class NamedBody(BaseModel):
    name: str
    description: Optional[str] = None


@router.post("/programs/{pid}/courses")
def add_course(pid: int, body: NamedBody, user=Depends(require_perm(MODULE, "edit")),
               services=Depends(get_services)):
    c = services["training"].create_course(pid, body.name, body.description)
    return {"id": c.id}


@router.delete("/courses/{cid}")
def del_course(cid: int, user=Depends(require_perm(MODULE, "edit")), services=Depends(get_services)):
    services["training"].delete_course(cid)
    return {"success": True}


@router.post("/programs/{pid}/workshops")
def add_workshop(pid: int, body: NamedBody, user=Depends(require_perm(MODULE, "edit")),
                 services=Depends(get_services)):
    w = services["training"].create_workshop(pid, body.name, body.description)
    return {"id": w.id}


@router.delete("/workshops/{wid}")
def del_workshop(wid: int, user=Depends(require_perm(MODULE, "edit")), services=Depends(get_services)):
    services["training"].delete_workshop(wid)
    return {"success": True}


class SessionBody(BaseModel):
    session_date: str
    duration_hours: int = 1
    topic: Optional[str] = None
    course_id: Optional[int] = None
    workshop_id: Optional[int] = None


@router.post("/programs/{pid}/sessions")
def add_session(pid: int, body: SessionBody, user=Depends(require_perm(MODULE, "edit")),
                services=Depends(get_services)):
    s = services["training"].schedule_session(
        _d(body.session_date), body.duration_hours, body.topic,
        course_id=body.course_id, workshop_id=body.workshop_id)
    return {"id": s.id}


@router.put("/sessions/{sid}")
def update_session(sid: int, body: SessionBody, user=Depends(require_perm(MODULE, "edit")),
                   services=Depends(get_services)):
    services["training"].update_session(sid, _d(body.session_date), body.duration_hours, body.topic)
    return {"success": True}


@router.delete("/sessions/{sid}")
def delete_session(sid: int, user=Depends(require_perm(MODULE, "edit")), services=Depends(get_services)):
    services["training"].delete_session(sid)
    return {"success": True}


# ----------------------------------------------------------------- trainees
@router.get("/trainees")
def list_trainees(user=Depends(require_perm(MODULE, "view")), services=Depends(get_services)):
    return [{"id": t.id, "full_name": t.full_name, "organization": t.organization,
             "phone": t.phone, "email": t.email}
            for t in services["training"].get_all_trainees()]


class TraineeBody(BaseModel):
    full_name: str
    organization: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None


@router.post("/trainees")
def add_trainee(body: TraineeBody, user=Depends(require_perm(MODULE, "create")),
                services=Depends(get_services)):
    if not body.full_name.strip():
        raise HTTPException(422, "الاسم مطلوب")
    t = services["training"].create_trainee(body.full_name.strip(), body.email or None,
                                            body.phone or None, body.organization or None)
    return {"id": t.id}


class BulkTraineeBody(BaseModel):
    prefix: str = "طالب"
    count: int
    start: int = 1
    organization: Optional[str] = None
    fee: Optional[float] = None  # if set, record count*fee as revenue


@router.post("/trainees/bulk")
def bulk_trainees(body: BulkTraineeBody, user=Depends(require_perm(MODULE, "create")),
                  services=Depends(get_services)):
    if body.count <= 0:
        raise HTTPException(422, "العدد يجب أن يكون أكبر من صفر")
    created = services["training"].bulk_create_trainees(
        body.prefix, body.count, body.start, body.organization)
    revenue = 0.0
    if body.fee and body.fee > 0:
        from datetime import date
        revenue = body.fee * created
        services["financial"].add_transaction(TransactionDTO(
            transaction_type="revenue", amount=revenue, date=date.today(),
            description=f"رسوم اشتراك {created} متدرب ({body.prefix})",
            source="رسوم تدريب"))
    return {"created": created, "revenue": revenue}


@router.post("/trainees/import")
async def import_trainees(file: UploadFile = File(...), user=Depends(require_perm(MODULE, "create")),
                          services=Depends(get_services)):
    rows = parse_xlsx(await file.read(), TRAINEE_COLS)
    records = [{"full_name": r.get("الاسم"), "organization": r.get("الجهة"),
               "phone": r.get("رقم الهاتف"), "email": r.get("البريد")} for r in rows]
    count = services["training"].import_trainees(records)
    return {"success": True, "imported": count}


@router.get("/trainees/template")
def trainees_template(user=Depends(require_perm(MODULE, "create")), services=Depends(get_services)):
    path = services["report"].export_to_excel("trainees_template", TRAINEE_COLS, [], title="قالب المتدربين")
    return file_download(path, "قالب_المتدربين.xlsx", XLSX_MEDIA)
