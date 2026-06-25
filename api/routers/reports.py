"""Report generation: 9 report types -> Excel/PDF download. Builders ported
verbatim from the desktop ReportsDashboardView."""
from fastapi import APIRouter, Depends, HTTPException

from api.deps import get_services, require_login
from api.responses import export_response

router = APIRouter(prefix="/api/reports", tags=["reports"])


def _d(value, fmt="%Y-%m-%d"):
    return value.strftime(fmt) if value else "-"


def _builders(services):
    def employees():
        rows = [[str(e.id), e.full_name, e.position.title if e.position else "-",
                 e.phone or "-", e.email or "-", _d(e.hire_date)]
                for e in services["hr"].get_all_employees()]
        return ("employees", "تقرير الموظفين",
                ["الرقم", "الاسم", "المنصب", "الهاتف", "البريد", "تاريخ التعيين"], rows)

    def financial():
        rows = [[_d(t.date), "إيراد" if t.transaction_type == "revenue" else "مصروف",
                 f"{float(t.amount):,.2f}", getattr(t, "category", None) or "-", t.description]
                for t in services["financial"].get_all_transactions()]
        return ("financial", "تقرير المعاملات المالية",
                ["التاريخ", "النوع", "المبلغ", "التصنيف", "البيان"], rows)

    def standards():
        q = services["quality"]
        rows = [[s.code, s.name, s.category.name if s.category else "-",
                 "نشط" if s.status == "active" else "غير نشط",
                 f"{int(q.calculate_compliance(s.id))}%"] for s in q.get_all_standards()]
        return ("standards", "تقرير المعايير ونِسب المطابقة",
                ["الكود", "اسم المعيار", "التصنيف", "الحالة", "نسبة المطابقة"], rows)

    def documents():
        rows = [[d.title, d.doc_type, d.category.name if d.category else "-", d.current_version,
                 "معتمد" if d.status == "approved" else "مسودة", _d(d.effective_date)]
                for d in services["document"].get_all_documents()]
        return ("documents", "تقرير الوثائق",
                ["العنوان", "النوع", "التصنيف", "الإصدار", "الحالة", "تاريخ السريان"], rows)

    def records():
        rows = [[r.record_number, r.title, r.record_type.name if r.record_type else "-",
                 r.storage_location or "-", "نشط" if r.status == "active" else "مؤرشف"]
                for r in services["record"].get_all_records()]
        return ("records", "تقرير السجلات",
                ["رقم السجل", "العنوان", "النوع", "مكان الحفظ", "الحالة"], rows)

    def training():
        types = {"training": "تدريب", "workshop": "ورشة", "course": "دورة"}
        rows = [[p.name, types.get(p.program_type, p.program_type), p.status,
                 _d(p.start_date), _d(p.end_date), str(p.total_hours or "-")]
                for p in services["training"].get_all_programs()]
        return ("training", "تقرير البرامج التدريبية",
                ["البرنامج", "النوع", "الحالة", "البداية", "النهاية", "الساعات"], rows)

    def partnerships():
        rows = [[p.name, p.contact_person or "-", p.email or "-", p.phone or "-", p.address or "-"]
                for p in services["partnership"].get_all_partners()]
        return ("partnerships", "تقرير الشراكات",
                ["الجهة", "مسؤول التواصل", "البريد", "الهاتف", "العنوان"], rows)

    def users():
        role_ar = {"superadmin": "مدير النظام", "admin": "مشرف", "user": "مستخدم عادي"}
        rows = [[u.full_name, u.username, role_ar.get(u.role_name, u.role_name or "-"),
                 "نشط" if u.is_active else "موقوف"] for u in services["auth"].get_all_users()]
        return ("users", "تقرير المستخدمين",
                ["الاسم", "اسم المستخدم", "الصلاحية", "الحالة"], rows)

    def audit_logs():
        rows = []
        for log, username in services["audit"].get_all_logs():
            ts = log.timestamp.strftime("%Y-%m-%d %H:%M:%S") if log.timestamp else ""
            rows.append([ts, username or "System", log.module, log.action, log.entity_type or "-"])
        return ("audit_logs", "تقرير سجل العمليات",
                ["التاريخ والوقت", "المستخدم", "الوحدة", "الإجراء", "الكيان"], rows)

    # key -> (label, permission-module or None for superadmin-only, builder)
    return {
        "employees": ("تقرير الموظفين (شؤون العاملين)", "hr", employees),
        "financial": ("تقرير المعاملات المالية", "financial", financial),
        "standards": ("تقرير المعايير ونِسب المطابقة", "quality", standards),
        "documents": ("تقرير الوثائق", "documents", documents),
        "records": ("تقرير السجلات", "records", records),
        "training": ("تقرير البرامج التدريبية", "training", training),
        "partnerships": ("تقرير الشراكات", "partnership", partnerships),
        "users": ("تقرير المستخدمين (الحسابات)", "__superadmin__", users),
        "audit_logs": ("تقرير سجل العمليات (Audit Logs)", "__superadmin__", audit_logs),
    }


def _allowed(key, spec, user, services):
    _label, module, _fn = spec
    if module == "__superadmin__":
        return (user.role_name or "") == "superadmin"
    return services["permission"].has_permission(module, "view")


@router.get("")
def list_reports(user=Depends(require_login), services=Depends(get_services)):
    builders = _builders(services)
    return [{"key": k, "label": spec[0]} for k, spec in builders.items()
            if _allowed(k, spec, user, services)]


@router.get("/{key}/data")
def report_data(key: str, user=Depends(require_login), services=Depends(get_services)):
    """Return the report's title/headers/rows as JSON for on-screen preview."""
    builders = _builders(services)
    if key not in builders:
        raise HTTPException(404, "تقرير غير معروف")
    spec = builders[key]
    if not _allowed(key, spec, user, services):
        raise HTTPException(403, "ليس لديك صلاحية لهذا التقرير")
    _label, _module, builder = spec
    _module_name, title, headers, rows = builder()
    return {"title": title, "headers": headers, "rows": rows, "count": len(rows)}


@router.get("/{key}")
def generate_report(key: str, fmt: str = "excel", user=Depends(require_login),
                    services=Depends(get_services)):
    builders = _builders(services)
    if key not in builders:
        raise HTTPException(404, "تقرير غير معروف")
    spec = builders[key]
    if not _allowed(key, spec, user, services):
        raise HTTPException(403, "ليس لديك صلاحية لهذا التقرير")
    _label, _module, builder = spec
    module, title, headers, rows = builder()
    return export_response(services["report"], fmt, module, headers, rows, title)
