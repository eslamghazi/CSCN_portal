from datetime import datetime

from qtpy.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QFileDialog
from qtpy.QtCore import QUrl
from qtpy.QtGui import QDesktopServices
from loguru import logger

from ui.widgets.card import Card
from ui.widgets.page_header import PageHeader
from ui.widgets.icon_button import IconButton
from ui.widgets.toast import Toast
from ui.widgets.busy import busy


def _d(value, fmt="%Y-%m-%d"):
    return value.strftime(fmt) if value else "-"


class ReportsDashboardView(QWidget):
    def __init__(self, services: dict):
        super().__init__()
        self.services = services
        self.report_engine = services["report"]
        self.reports = self._build_report_list()
        self.setup_ui()

    def _build_report_list(self):
        """Reports suited to the current user's role/permissions.

        Operational reports appear only for modules the user may view (so an
        admin and a superadmin each see what fits their permissions). System
        reports — user accounts and the operations/audit log — are added for the
        superadmin, who is the only role with access to those areas.
        Each builder returns (module, title, headers, rows)."""
        perm = self.services.get("permission")

        def can_view(module: str) -> bool:
            return perm.has_permission(module, "view") if perm else True

        # (label, permission-module, builder)
        operational = [
            ("تقرير الموظفين (شؤون العاملين)", "hr", self._employees),
            ("تقرير المعاملات المالية", "financial", self._financial),
            ("تقرير المعايير ونِسب المطابقة", "quality", self._standards),
            ("تقرير الوثائق", "documents", self._documents),
            ("تقرير السجلات", "records", self._records),
            ("تقرير البرامج التدريبية", "training", self._training),
            ("تقرير الشراكات", "partnership", self._partnerships),
        ]
        reports = [(label, fn) for label, module, fn in operational if can_view(module)]

        current = self.services["auth"].get_current_user()
        if current and current.role_name == "superadmin":
            reports.append(("تقرير المستخدمين (الحسابات)", self._users))
            reports.append(("تقرير سجل العمليات (Audit Logs)", self._audit_logs))
        return reports

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)

        card = Card()
        card.add(PageHeader("توليد التقارير والإحصائيات",
                            subtitle="اختر التقرير والصيغة ثم احفظه في المكان الذي تريده."))

        row = QHBoxLayout()
        row.setSpacing(12)
        row.addWidget(QLabel("التقرير:"))
        self.report_combo = QComboBox()
        self.report_combo.setMinimumWidth(280)
        for label, _fn in self.reports:
            self.report_combo.addItem(label)
        row.addWidget(self.report_combo)

        row.addWidget(QLabel("الصيغة:"))
        self.format_combo = QComboBox()
        self.format_combo.addItem("Excel (.xlsx)", "excel")
        self.format_combo.addItem("PDF (.pdf)", "pdf")
        row.addWidget(self.format_combo)

        self.export_btn = IconButton("حفظ باسم...", "export", variant="primary")
        self.export_btn.clicked.connect(self.on_export_clicked)
        row.addWidget(self.export_btn)
        row.addStretch()
        card.add_layout(row)

        main_layout.addWidget(card)
        main_layout.addStretch()

    # ------------------------------------------------------------ datasets
    def _employees(self):
        rows = [
            [str(e.id), e.full_name, e.position.title if e.position else "-",
             e.phone or "-", e.email or "-", _d(e.hire_date)]
            for e in self.services["hr"].get_all_employees()
        ]
        return ("employees", "تقرير الموظفين",
                ["الرقم", "الاسم", "المنصب", "الهاتف", "البريد", "تاريخ التعيين"], rows)

    def _financial(self):
        rows = [
            [_d(t.date), "إيراد" if t.transaction_type == "revenue" else "مصروف",
             f"{t.amount:,.2f}", t.category or "-", t.description]
            for t in self.services["financial"].get_all_transactions()
        ]
        return ("financial", "تقرير المعاملات المالية",
                ["التاريخ", "النوع", "المبلغ", "التصنيف", "البيان"], rows)

    def _standards(self):
        q = self.services["quality"]
        rows = [
            [s.code, s.name, s.category.name if s.category else "-",
             "نشط" if s.status == "active" else "غير نشط",
             f"{int(q.calculate_compliance(s.id))}%"]
            for s in q.get_all_standards()
        ]
        return ("standards", "تقرير المعايير ونِسب المطابقة",
                ["الكود", "اسم المعيار", "التصنيف", "الحالة", "نسبة المطابقة"], rows)

    def _documents(self):
        rows = [
            [d.title, d.doc_type, d.category.name if d.category else "-",
             d.current_version, "معتمد" if d.status == "approved" else "مسودة", _d(d.effective_date)]
            for d in self.services["document"].get_all_documents()
        ]
        return ("documents", "تقرير الوثائق",
                ["العنوان", "النوع", "التصنيف", "الإصدار", "الحالة", "تاريخ السريان"], rows)

    def _records(self):
        rows = [
            [r.record_number, r.title, r.record_type.name if r.record_type else "-",
             r.storage_location or "-", "نشط" if r.status == "active" else "مؤرشف"]
            for r in self.services["record"].get_all_records()
        ]
        return ("records", "تقرير السجلات",
                ["رقم السجل", "العنوان", "النوع", "مكان الحفظ", "الحالة"], rows)

    def _training(self):
        types = {"training": "تدريب", "workshop": "ورشة", "course": "دورة"}
        rows = [
            [p.name, types.get(p.program_type, p.program_type), p.status,
             _d(p.start_date), _d(p.end_date), str(p.total_hours or "-")]
            for p in self.services["training"].get_all_programs()
        ]
        return ("training", "تقرير البرامج التدريبية",
                ["البرنامج", "النوع", "الحالة", "البداية", "النهاية", "الساعات"], rows)

    def _partnerships(self):
        rows = [
            [p.name, p.contact_person or "-", p.email or "-", p.phone or "-", p.address or "-"]
            for p in self.services["partnership"].get_all_partners()
        ]
        return ("partnerships", "تقرير الشراكات",
                ["الجهة", "مسؤول التواصل", "البريد", "الهاتف", "العنوان"], rows)

    # ----------------------------------------------- system (superadmin) reports
    def _users(self):
        role_ar = {"superadmin": "مدير النظام", "admin": "مشرف", "user": "مستخدم عادي"}
        rows = [
            [u.full_name, u.username, role_ar.get(u.role_name, u.role_name or "-"),
             "نشط" if u.is_active else "موقوف"]
            for u in self.services["auth"].get_all_users()
        ]
        return ("users", "تقرير المستخدمين",
                ["الاسم", "اسم المستخدم", "الصلاحية", "الحالة"], rows)

    def _audit_logs(self):
        rows = []
        for log, username in self.services["audit"].get_all_logs():
            ts = log.timestamp.strftime("%Y-%m-%d %H:%M:%S") if log.timestamp else ""
            rows.append([ts, username or "System", log.module, log.action,
                         log.entity_type or "-"])
        return ("audit_logs", "تقرير سجل العمليات",
                ["التاريخ والوقت", "المستخدم", "الوحدة", "الإجراء", "الكيان"], rows)

    # ------------------------------------------------------------ export
    def on_export_clicked(self):
        fmt = self.format_combo.currentData()
        ext = "pdf" if fmt == "pdf" else "xlsx"
        label, builder = self.reports[self.report_combo.currentIndex()]
        try:
            module, title, headers, rows = builder()
        except Exception as e:
            logger.error(f"Report dataset failed: {e}")
            Toast.error(self, "تعذّر تجهيز بيانات التقرير")
            return

        default_name = f"{title} - {datetime.now().strftime('%Y%m%d')}.{ext}"
        file_filter = "PDF (*.pdf)" if fmt == "pdf" else "Excel (*.xlsx)"
        dest, _ = QFileDialog.getSaveFileName(self, "حفظ التقرير باسم", default_name, file_filter)
        if not dest:
            return
        try:
            with busy(self, "جاري توليد التقرير..."):
                if fmt == "pdf":
                    path = self.report_engine.export_to_pdf(
                        module, headers, rows, title=title, dest_path=dest)
                else:
                    path = self.report_engine.export_to_excel(
                        module, headers, rows, title=title, dest_path=dest)
            logger.info(f"Report exported to {path}")
            Toast.success(self, "تم حفظ التقرير بنجاح")
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))
        except Exception as e:
            logger.error(f"Report export failed: {e}")
            Toast.error(self, "حدث خطأ أثناء حفظ التقرير")
