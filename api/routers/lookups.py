"""Reference-data (lookups) CRUD: standard categories, document categories,
record types, job positions. Admin/superadmin only."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.deps import get_services
from api.permissions import require_role

router = APIRouter(prefix="/api/lookups", tags=["lookups"])


# Each kind maps to (list_fn, create_fn, update_fn, delete_fn) returning items
# as (id, name, description). Positions use `title` instead of `name`.
def _kinds(services):
    q, d, r, hr = services["quality"], services["document"], services["record"], services["hr"]
    return {
        "standard-categories": {
            "label": "تصنيفات المعايير",
            "list": lambda: [(c.id, c.name, c.description) for c in q.get_all_categories()],
            "create": lambda n, de: q.create_category(n, de),
            "update": lambda i, n, de: q.update_category(i, n, de),
            "delete": lambda i: q.delete_category(i),
        },
        "document-categories": {
            "label": "تصنيفات الوثائق",
            "list": lambda: [(c.id, c.name, c.description) for c in d.get_categories()],
            "create": lambda n, de: d.create_category(n, de),
            "update": lambda i, n, de: d.update_category(i, n, de),
            "delete": lambda i: d.delete_category(i),
        },
        "record-types": {
            "label": "أنواع السجلات",
            "list": lambda: [(t.id, t.name, t.description) for t in r.get_all_record_types()],
            "create": lambda n, de: r.add_record_type(n, de),
            "update": lambda i, n, de: r.update_record_type(i, n, de),
            "delete": lambda i: r.delete_record_type(i),
        },
        "positions": {
            "label": "المناصب الوظيفية",
            "list": lambda: [(p.id, p.title, p.description) for p in hr.get_all_positions()],
            "create": lambda n, de: hr.create_position(n, de),
            "update": lambda i, n, de: hr.update_position(i, n, de),
            "delete": lambda i: hr.delete_position(i),
        },
    }


class LookupBody(BaseModel):
    name: str
    description: Optional[str] = None


def _get_kind(kind: str, services):
    kinds = _kinds(services)
    if kind not in kinds:
        raise HTTPException(404, "نوع غير معروف")
    return kinds[kind]


@router.get("/kinds")
def kinds(user=Depends(require_role("admin")), services=Depends(get_services)):
    return [{"key": k, "label": v["label"]} for k, v in _kinds(services).items()]


@router.get("/{kind}")
def list_items(kind: str, user=Depends(require_role("admin")), services=Depends(get_services)):
    spec = _get_kind(kind, services)
    return [{"id": i, "name": n, "description": de or ""} for (i, n, de) in spec["list"]()]


@router.post("/{kind}")
def create_item(kind: str, body: LookupBody, user=Depends(require_role("admin")),
                services=Depends(get_services)):
    spec = _get_kind(kind, services)
    if not body.name.strip():
        raise HTTPException(422, "الاسم مطلوب")
    spec["create"](body.name.strip(), body.description or None)
    return {"success": True}


@router.put("/{kind}/{item_id}")
def update_item(kind: str, item_id: int, body: LookupBody, user=Depends(require_role("admin")),
                services=Depends(get_services)):
    spec = _get_kind(kind, services)
    spec["update"](item_id, body.name.strip(), body.description or None)
    return {"success": True}


@router.delete("/{kind}/{item_id}")
def delete_item(kind: str, item_id: int, user=Depends(require_role("admin")),
                services=Depends(get_services)):
    spec = _get_kind(kind, services)
    try:
        spec["delete"](item_id)
    except Exception:
        raise HTTPException(409, "لا يمكن الحذف لارتباط العنصر بسجلات أخرى")
    return {"success": True}
