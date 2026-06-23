"""HR / employees: CRUD + sub-tables (qualifications/experience/evaluations) +
Excel export/import/template."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel

from api.deps import get_services, require_perm
from api.responses import export_response
from api.excel_io import parse_xlsx
from application.services.hr_service import EmployeeDTO

router = APIRouter(prefix="/api/hr", tags=["hr"])

MODULE = "hr"
IMPORT_COLS = ["الاسم بالكامل", "البريد الإلكتروني", "رقم الهاتف"]


def _emp(e) -> dict:
    return {
        "id": e.id,
        "full_name": e.full_name,
        "email": e.email,
        "phone": e.phone,
        "position_id": e.position_id,
        "position": e.position.title if e.position else None,
        "hire_date": e.hire_date.isoformat() if e.hire_date else None,
        "status": e.status,
    }


class EmployeeBody(BaseModel):
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    position_id: Optional[int] = None
    hire_date: Optional[str] = None
    status: str = "active"


def _to_dto(body: EmployeeBody, id: int = None) -> EmployeeDTO:
    from datetime import date
    hd = None
    if body.hire_date:
        try:
            hd = date.fromisoformat(body.hire_date)
        except ValueError:
            hd = None
    return EmployeeDTO(id=id, full_name=body.full_name.strip(), email=body.email or None,
                       phone=body.phone or None, position_id=body.position_id or None,
                       hire_date=hd, status=body.status or "active")


# ----------------------------------------------------------------- positions
@router.get("/positions")
def positions(user=Depends(require_perm(MODULE, "view")), services=Depends(get_services)):
    return [{"value": p.id, "label": p.title} for p in services["hr"].get_all_positions()]


# ----------------------------------------------------------------- employees
@router.get("/employees")
def list_employees(user=Depends(require_perm(MODULE, "view")), services=Depends(get_services)):
    return [_emp(e) for e in services["hr"].get_all_employees()]


@router.post("/employees")
def create_employee(body: EmployeeBody, user=Depends(require_perm(MODULE, "create")),
                    services=Depends(get_services)):
    if not body.full_name.strip():
        raise HTTPException(422, "الاسم مطلوب")
    return _emp(services["hr"].add_employee(_to_dto(body)))


@router.put("/employees/{emp_id}")
def update_employee(emp_id: int, body: EmployeeBody,
                    user=Depends(require_perm(MODULE, "edit")), services=Depends(get_services)):
    updated = services["hr"].update_employee(_to_dto(body, emp_id))
    if not updated:
        raise HTTPException(404, "الموظف غير موجود")
    return _emp(updated)


@router.delete("/employees/{emp_id}")
def delete_employee(emp_id: int, user=Depends(require_perm(MODULE, "delete")),
                    services=Depends(get_services)):
    services["hr"].delete_employee(emp_id)
    return {"success": True}


@router.get("/employees/export")
def export_employees(fmt: str = "excel", user=Depends(require_perm(MODULE, "view")),
                     services=Depends(get_services)):
    headers = ["الرقم", "الاسم بالكامل", "المنصب", "رقم الهاتف", "البريد", "تاريخ التعيين", "الحالة"]
    rows = [[e.id, e.full_name, (e.position.title if e.position else "-"), e.phone or "-",
             e.email or "-", e.hire_date.isoformat() if e.hire_date else "-",
             "نشط" if e.status == "active" else "غير نشط"]
            for e in services["hr"].get_all_employees()]
    return export_response(services["report"], fmt, "employees", headers, rows, "قائمة الموظفين")


@router.get("/employees/template")
def employees_template(user=Depends(require_perm(MODULE, "create")), services=Depends(get_services)):
    from api.responses import file_download, XLSX_MEDIA
    path = services["report"].export_to_excel("employees_template", IMPORT_COLS, [], title="قالب الموظفين")
    return file_download(path, "قالب_الموظفين.xlsx", XLSX_MEDIA)


@router.post("/employees/import")
async def import_employees(file: UploadFile = File(...),
                           user=Depends(require_perm(MODULE, "create")),
                           services=Depends(get_services)):
    rows = parse_xlsx(await file.read(), IMPORT_COLS)
    count = 0
    for r in rows:
        name = (r.get("الاسم بالكامل") or "").strip()
        if not name:
            continue
        services["hr"].add_employee(EmployeeDTO(
            full_name=name, email=r.get("البريد الإلكتروني") or None,
            phone=r.get("رقم الهاتف") or None))
        count += 1
    return {"success": True, "imported": count}


# ------------------------------------------------------- employee detail + subs
@router.get("/employees/{emp_id}")
def employee_detail(emp_id: int, user=Depends(require_perm(MODULE, "view")),
                    services=Depends(get_services)):
    hr = services["hr"]
    emp = hr.employee_repo.get_by_id(emp_id)
    if not emp:
        raise HTTPException(404, "الموظف غير موجود")
    quals = [{"id": q.id, "degree": q.degree, "institution": q.institution,
              "year_obtained": q.year_obtained} for q in hr.get_qualifications(emp_id)]
    exps = [{"id": x.id, "job_title": x.job_title, "company": x.company,
             "start_date": x.start_date.isoformat() if x.start_date else None,
             "end_date": x.end_date.isoformat() if x.end_date else None,
             "description": x.description} for x in hr.get_experience(emp_id)]
    evals = [{"id": v.id, "evaluation_date": v.evaluation_date.isoformat() if v.evaluation_date else None,
              "score": v.score, "notes": v.notes} for v in hr.get_evaluations(emp_id)]
    return {"employee": _emp(emp), "qualifications": quals, "experience": exps, "evaluations": evals}


class QualBody(BaseModel):
    degree: str
    institution: str
    year_obtained: Optional[int] = None


@router.post("/employees/{emp_id}/qualifications")
def add_qual(emp_id: int, body: QualBody, user=Depends(require_perm(MODULE, "edit")),
             services=Depends(get_services)):
    q = services["hr"].add_qualification(emp_id, body.degree, body.institution, body.year_obtained)
    return {"id": q.id}


@router.put("/qualifications/{qid}")
def upd_qual(qid: int, body: QualBody, user=Depends(require_perm(MODULE, "edit")),
             services=Depends(get_services)):
    services["hr"].update_qualification(qid, body.degree, body.institution, body.year_obtained)
    return {"success": True}


@router.delete("/qualifications/{qid}")
def del_qual(qid: int, user=Depends(require_perm(MODULE, "edit")), services=Depends(get_services)):
    services["hr"].delete_qualification(qid)
    return {"success": True}


class ExpBody(BaseModel):
    job_title: str
    company: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None


def _d(s):
    from datetime import date
    if not s:
        return None
    try:
        return date.fromisoformat(s)
    except ValueError:
        return None


@router.post("/employees/{emp_id}/experience")
def add_exp(emp_id: int, body: ExpBody, user=Depends(require_perm(MODULE, "edit")),
            services=Depends(get_services)):
    x = services["hr"].add_experience(emp_id, body.job_title, body.company,
                                       _d(body.start_date), _d(body.end_date), body.description)
    return {"id": x.id}


@router.put("/experience/{xid}")
def upd_exp(xid: int, body: ExpBody, user=Depends(require_perm(MODULE, "edit")),
            services=Depends(get_services)):
    services["hr"].update_experience(xid, body.job_title, body.company,
                                      _d(body.start_date), _d(body.end_date), body.description)
    return {"success": True}


@router.delete("/experience/{xid}")
def del_exp(xid: int, user=Depends(require_perm(MODULE, "edit")), services=Depends(get_services)):
    services["hr"].delete_experience(xid)
    return {"success": True}


class EvalBody(BaseModel):
    evaluation_date: str
    score: Optional[float] = None
    notes: Optional[str] = None


@router.post("/employees/{emp_id}/evaluations")
def add_eval(emp_id: int, body: EvalBody, user=Depends(require_perm(MODULE, "edit")),
             services=Depends(get_services)):
    v = services["hr"].add_evaluation(emp_id, _d(body.evaluation_date), body.score, body.notes)
    return {"id": v.id}


@router.put("/evaluations/{vid}")
def upd_eval(vid: int, body: EvalBody, user=Depends(require_perm(MODULE, "edit")),
             services=Depends(get_services)):
    services["hr"].update_evaluation(vid, _d(body.evaluation_date), body.score, body.notes)
    return {"success": True}


@router.delete("/evaluations/{vid}")
def del_eval(vid: int, user=Depends(require_perm(MODULE, "edit")), services=Depends(get_services)):
    services["hr"].delete_evaluation(vid)
    return {"success": True}
