"""Partnerships (organizations) + agreements."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel

from api.deps import get_services, require_perm
from api.responses import export_response, file_download, XLSX_MEDIA
from api.excel_io import parse_xlsx
from application.services.partnership_service import PartnershipDTO

router = APIRouter(prefix="/api/partnerships", tags=["partnerships"])
MODULE = "partnership"
IMPORT_COLS = ["اسم الجهة", "مسؤول التواصل", "البريد الإلكتروني", "رقم الهاتف", "العنوان"]


def _p(p) -> dict:
    return {"id": p.id, "name": p.name, "contact_person": p.contact_person,
            "email": p.email, "phone": p.phone, "address": p.address}


class PartnerBody(BaseModel):
    name: str
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None


@router.get("")
def list_partners(user=Depends(require_perm(MODULE, "view")), services=Depends(get_services)):
    return [_p(p) for p in services["partnership"].get_all_partners()]


@router.post("")
def create_partner(body: PartnerBody, user=Depends(require_perm(MODULE, "create")),
                   services=Depends(get_services)):
    if not body.name.strip():
        raise HTTPException(422, "اسم الجهة مطلوب")
    return _p(services["partnership"].add_partner(PartnershipDTO(**body.model_dump())))


@router.put("/{pid}")
def update_partner(pid: int, body: PartnerBody, user=Depends(require_perm(MODULE, "edit")),
                   services=Depends(get_services)):
    p = services["partnership"].update_partner(PartnershipDTO(id=pid, **body.model_dump()))
    if not p:
        raise HTTPException(404, "الجهة غير موجودة")
    return _p(p)


@router.delete("/{pid}")
def delete_partner(pid: int, user=Depends(require_perm(MODULE, "delete")),
                   services=Depends(get_services)):
    services["partnership"].delete_partner(pid)
    return {"success": True}


@router.get("/export")
def export_partners(fmt: str = "excel", user=Depends(require_perm(MODULE, "view")),
                    services=Depends(get_services)):
    headers = ["اسم الجهة", "مسؤول التواصل", "البريد", "الهاتف", "العنوان"]
    rows = [[p.name, p.contact_person or "-", p.email or "-", p.phone or "-", p.address or "-"]
            for p in services["partnership"].get_all_partners()]
    return export_response(services["report"], fmt, "partnerships", headers, rows, "الشراكات")


@router.get("/template")
def partners_template(user=Depends(require_perm(MODULE, "create")), services=Depends(get_services)):
    path = services["report"].export_to_excel("partnerships_template", IMPORT_COLS, [], title="قالب الشراكات")
    return file_download(path, "قالب_الشراكات.xlsx", XLSX_MEDIA)


@router.post("/import")
async def import_partners(file: UploadFile = File(...), user=Depends(require_perm(MODULE, "create")),
                          services=Depends(get_services)):
    rows = parse_xlsx(await file.read(), IMPORT_COLS)
    count = 0
    for r in rows:
        name = (r.get("اسم الجهة") or "").strip()
        if not name:
            continue
        services["partnership"].add_partner(PartnershipDTO(
            name=name, contact_person=r.get("مسؤول التواصل") or None,
            email=r.get("البريد الإلكتروني") or None, phone=r.get("رقم الهاتف") or None,
            address=r.get("العنوان") or None))
        count += 1
    return {"success": True, "imported": count}


# ----------------------------------------------------------------- agreements
class AgreementBody(BaseModel):
    title: str
    agreement_type: str = "agreement"
    start_date: Optional[str] = None
    end_date: Optional[str] = None


def _d(s):
    from datetime import date
    if not s:
        return None
    try:
        return date.fromisoformat(s)
    except ValueError:
        return None


@router.get("/{pid}/agreements")
def list_agreements(pid: int, user=Depends(require_perm(MODULE, "view")),
                    services=Depends(get_services)):
    return [{"id": a.id, "title": a.title, "agreement_type": a.agreement_type,
             "start_date": a.start_date.isoformat() if a.start_date else None,
             "end_date": a.end_date.isoformat() if a.end_date else None, "status": a.status}
            for a in services["partnership"].list_agreements(pid)]


@router.post("/{pid}/agreements")
def add_agreement(pid: int, body: AgreementBody, user=Depends(require_perm(MODULE, "edit")),
                  services=Depends(get_services)):
    a = services["partnership"].add_agreement(pid, body.title, _d(body.start_date),
                                               _d(body.end_date), body.agreement_type)
    return {"id": a.id}


@router.delete("/agreements/{aid}")
def delete_agreement(aid: int, user=Depends(require_perm(MODULE, "edit")),
                     services=Depends(get_services)):
    services["partnership"].delete_agreement(aid)
    return {"success": True}
