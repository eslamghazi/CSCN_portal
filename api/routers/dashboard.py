"""Dashboard KPIs."""
from fastapi import APIRouter, Depends

from api.deps import require_login, get_services

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

# (key, module, title, accent-name, value function)
_KPIS = [
    ("employees", "hr", "عدد الموظفين", "green",
     lambda s: len(s["hr"].get_all_employees())),
    ("standards", "quality", "إجمالي المعايير", "blue",
     lambda s: len(s["quality"].get_all_standards())),
    ("documents", "documents", "الوثائق المعتمدة", "amber",
     lambda s: len([d for d in s["document"].get_all_documents() if d.status == "approved"])),
    ("training", "training", "البرامج التدريبية", "purple",
     lambda s: len(s["training"].get_all_programs())),
]


@router.get("/kpis")
def kpis(user=Depends(require_login), services: dict = Depends(get_services)):
    perm = services["permission"]
    out = []
    for key, module, title, accent, value_fn in _KPIS:
        if not perm.has_permission(module, "view"):
            continue
        try:
            value = value_fn(services)
        except Exception:
            value = 0
        out.append({"key": key, "module": module, "title": title,
                    "accent": accent, "value": value})
    return {"kpis": out}
