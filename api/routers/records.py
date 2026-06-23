"""Records & archives CRUD."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.deps import get_services, require_perm
from api.responses import export_response

router = APIRouter(prefix="/api/records", tags=["records"])
MODULE = "records"


def _rec(r) -> dict:
    return {
        "id": r.id, "record_number": r.record_number, "title": r.title,
        "record_type_id": r.record_type_id,
        "record_type": r.record_type.name if r.record_type else None,
        "storage_location": r.storage_location,
        "retention_period_months": r.retention_period_months,
        "disposal_method": r.disposal_method, "status": r.status, "notes": r.notes,
    }


class RecordBody(BaseModel):
    record_number: str
    title: str
    record_type_id: Optional[int] = None
    storage_location: Optional[str] = None
    retention_period_months: Optional[int] = None
    disposal_method: Optional[str] = None
    status: str = "active"
    notes: Optional[str] = None


@router.get("/types")
def types(user=Depends(require_perm(MODULE, "view")), services=Depends(get_services)):
    return [{"value": t.id, "label": t.name} for t in services["record"].get_all_record_types()]


@router.get("")
def list_records(user=Depends(require_perm(MODULE, "view")), services=Depends(get_services)):
    return [_rec(r) for r in services["record"].get_all_records()]


@router.post("")
def create_record(body: RecordBody, user=Depends(require_perm(MODULE, "create")),
                  services=Depends(get_services)):
    if not body.record_number.strip() or not body.title.strip():
        raise HTTPException(422, "رقم السجل والعنوان مطلوبان")
    r = services["record"].add_record(
        record_number=body.record_number.strip(), title=body.title.strip(),
        record_type_id=body.record_type_id or None, storage_location=body.storage_location or None,
        retention_period_months=body.retention_period_months or None,
        disposal_method=body.disposal_method or None, status=body.status or "active",
        notes=body.notes or None)
    return _rec(r)


@router.put("/{rid}")
def update_record(rid: int, body: RecordBody, user=Depends(require_perm(MODULE, "edit")),
                  services=Depends(get_services)):
    svc = services["record"]
    rec = svc.get_record_by_id(rid)
    if not rec:
        raise HTTPException(404, "السجل غير موجود")
    rec.record_number = body.record_number.strip()
    rec.title = body.title.strip()
    rec.record_type_id = body.record_type_id or None
    rec.storage_location = body.storage_location or None
    rec.retention_period_months = body.retention_period_months or None
    rec.disposal_method = body.disposal_method or None
    rec.status = body.status or "active"
    rec.notes = body.notes or None
    return _rec(svc.update_record(rec))


@router.delete("/{rid}")
def delete_record(rid: int, user=Depends(require_perm(MODULE, "delete")),
                  services=Depends(get_services)):
    services["record"].delete_record(rid)
    return {"success": True}


@router.get("/export")
def export_records(fmt: str = "excel", user=Depends(require_perm(MODULE, "view")),
                   services=Depends(get_services)):
    headers = ["رقم السجل", "العنوان", "النوع", "مكان الحفظ", "الحالة"]
    rows = [[r.record_number, r.title, (r.record_type.name if r.record_type else "-"),
             r.storage_location or "-", "نشط" if r.status == "active" else "مؤرشف"]
            for r in services["record"].get_all_records()]
    return export_response(services["report"], fmt, "records", headers, rows, "السجلات")
