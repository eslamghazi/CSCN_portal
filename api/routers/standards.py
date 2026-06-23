"""Quality standards CRUD + compliance % + nested indicators."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.deps import get_services, require_perm
from api.responses import export_response
from application.services.quality_service import StandardDTO, IndicatorDTO

router = APIRouter(prefix="/api/standards", tags=["standards"])
MODULE = "quality"


def _std(s, compliance=None) -> dict:
    return {
        "id": s.id, "code": s.code, "name": s.name, "description": s.description,
        "category_id": s.category_id, "category": s.category.name if s.category else None,
        "status": s.status, "compliance": compliance,
    }


class StandardBody(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    category_id: Optional[int] = None
    status: str = "active"


@router.get("/categories")
def categories(user=Depends(require_perm(MODULE, "view")), services=Depends(get_services)):
    return [{"value": c.id, "label": c.name} for c in services["quality"].get_all_categories()]


@router.get("")
def list_standards(user=Depends(require_perm(MODULE, "view")), services=Depends(get_services)):
    q = services["quality"]
    out = []
    for s in q.get_all_standards():
        out.append(_std(s, int(q.calculate_compliance(s.id))))
    return out


@router.post("")
def create_standard(body: StandardBody, user=Depends(require_perm(MODULE, "create")),
                    services=Depends(get_services)):
    if not body.code.strip() or not body.name.strip():
        raise HTTPException(422, "الكود والاسم مطلوبان")
    s = services["quality"].create_standard(StandardDTO(**body.model_dump()))
    return _std(s)


@router.put("/{sid}")
def update_standard(sid: int, body: StandardBody, user=Depends(require_perm(MODULE, "edit")),
                    services=Depends(get_services)):
    s = services["quality"].update_standard(StandardDTO(id=sid, **body.model_dump()))
    if not s:
        raise HTTPException(404, "المعيار غير موجود")
    return _std(s)


@router.delete("/{sid}")
def delete_standard(sid: int, user=Depends(require_perm(MODULE, "delete")),
                    services=Depends(get_services)):
    try:
        services["quality"].delete_standard(sid)
    except Exception:
        raise HTTPException(409, "تعذّر الحذف لارتباط المعيار بمؤشرات أو سجلات")
    return {"success": True}


@router.get("/export")
def export_standards(fmt: str = "excel", user=Depends(require_perm(MODULE, "view")),
                     services=Depends(get_services)):
    q = services["quality"]
    headers = ["الكود", "اسم المعيار", "التصنيف", "الحالة", "نسبة الإنجاز %"]
    rows = [[s.code, s.name, (s.category.name if s.category else "-"),
             "نشط" if s.status == "active" else "غير نشط", int(q.calculate_compliance(s.id))]
            for s in q.get_all_standards()]
    return export_response(q if False else services["report"], fmt, "standards", headers, rows, "المعايير")


# ----------------------------------------------------------------- indicators
class IndicatorBody(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    weight: Optional[float] = None
    status: str = "active"
    sort_order: int = 0


@router.get("/{sid}/indicators")
def list_indicators(sid: int, user=Depends(require_perm(MODULE, "view")),
                    services=Depends(get_services)):
    return [{"id": i.id, "code": i.code, "name": i.name, "description": i.description,
             "weight": i.weight, "status": i.status, "sort_order": i.sort_order}
            for i in services["quality"].get_indicators(sid)]


@router.post("/{sid}/indicators")
def create_indicator(sid: int, body: IndicatorBody, user=Depends(require_perm(MODULE, "edit")),
                     services=Depends(get_services)):
    i = services["quality"].create_indicator(IndicatorDTO(standard_id=sid, **body.model_dump()))
    return {"id": i.id}


@router.put("/indicators/{iid}")
def update_indicator(iid: int, body: IndicatorBody, user=Depends(require_perm(MODULE, "edit")),
                     services=Depends(get_services)):
    services["quality"].update_indicator(IndicatorDTO(id=iid, **body.model_dump()))
    return {"success": True}


@router.delete("/indicators/{iid}")
def delete_indicator(iid: int, user=Depends(require_perm(MODULE, "edit")),
                     services=Depends(get_services)):
    services["quality"].delete_indicator(iid)
    return {"success": True}
