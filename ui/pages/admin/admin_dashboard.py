from datetime import datetime

from qtpy.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QComboBox, QLabel, QFileDialog,
)
from sqlalchemy.exc import IntegrityError
from loguru import logger

from ui.widgets.data_table import DataTable, Row, Badge, Action
from ui.widgets.page_header import PageHeader
from ui.widgets.icon_button import IconButton
from ui.widgets.toast import Toast
from ui.widgets.confirm import confirm
from ui.widgets.busy import busy
from ui.widgets.log_console import LogConsole
from ui.pages.admin.user_dialog import UserDialog
from config.logging_config import read_log_tail, list_log_files, parse_log_lines


class AdminDashboardView(QWidget):
    def __init__(self, services: dict):
        super().__init__()
        self.services = services
        self.auth_service = services["auth"]
        self.audit_service = services["audit"]
        self.permission_service = services.get("permission")
        self.report_engine = services.get("report")
        self.setup_ui()
        self.load_users()
        self.load_logs()
        self.load_full_log()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        self.users_tab = QWidget()
        self.setup_users_tab()
        self.tabs.addTab(self.users_tab, "إدارة المستخدمين")

        self.logs_tab = QWidget()
        self.setup_logs_tab()
        self.tabs.addTab(self.logs_tab, "سجل عمليات النظام")

        # The superadmin additionally gets the full file-based logging (logs.log)
        # — the raw DEBUG-level application log, not just the DB audit trail.
        current = self.auth_service.get_current_user()
        if current and current.role_name == "superadmin":
            self.full_log_tab = QWidget()
            self.setup_full_log_tab()
            self.tabs.addTab(self.full_log_tab, "السجل الكامل (logs.log)")

    def setup_users_tab(self):
        layout = QVBoxLayout(self.users_tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        header = PageHeader(
            "المستخدمون المسجلون",
            action_text="إضافة مستخدم جديد", action_icon="add",
        )
        header.action_clicked.connect(self.on_add_user)
        layout.addWidget(header)

        self.users_table = DataTable(
            ["الاسم", "اسم المستخدم", "الصلاحية", "الحالة", "إجراءات"])
        self.users_table.add_filter("الحالة", [("نشط", True), ("موقوف", False)])
        layout.addWidget(self.users_table)

    def setup_logs_tab(self):
        layout = QVBoxLayout(self.logs_tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        header = PageHeader(
            "سجل المراقبة (Audit Logs)",
            action_text="تصدير", action_icon="export",
        )
        header.action_clicked.connect(self.on_export_audit_logs)
        layout.addWidget(header)

        self.logs_table = DataTable(
            ["التاريخ والوقت", "المستخدم", "الوحدة", "الإجراء", "الكيان"])
        layout.addWidget(self.logs_table)

    def setup_full_log_tab(self):
        layout = QVBoxLayout(self.full_log_tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        header = PageHeader(
            "السجل الكامل للنظام (logs.log)",
            subtitle="التسجيل التفصيلي الكامل لعمليات التطبيق",
            action_text="تحديث", action_icon="refresh",
        )
        header.action_clicked.connect(self.load_full_log)
        layout.addWidget(header)

        # Date picker: choose which day's log file to view (only days that
        # actually have a log file on disk are listed).
        picker_row = QHBoxLayout()
        picker_row.setSpacing(8)
        picker_row.addWidget(QLabel("التاريخ:"))
        self.log_date_combo = QComboBox()
        self.log_date_combo.setMinimumWidth(220)
        self.log_date_combo.currentIndexChanged.connect(self._display_selected_log)
        picker_row.addWidget(self.log_date_combo)
        picker_row.addStretch()
        self.export_log_btn = IconButton("تصدير", "export", variant="secondary", compact=True)
        self.export_log_btn.clicked.connect(self.on_export_full_log)
        picker_row.addWidget(self.export_log_btn)
        layout.addLayout(picker_row)

        self.full_log_view = LogConsole()
        layout.addWidget(self.full_log_view)

    def load_users(self):
        try:
            with busy(self, "جاري تحميل المستخدمين..."):
                self._populate_users()
        except Exception as e:
            logger.error(f"Users load failed: {e}")
            Toast.error(self, "حدث خطأ أثناء جلب المستخدمين")

    def _populate_users(self):
        users = self.auth_service.get_all_users()
        rows = []
        for u in users:
            role_str = u.role_name if u.role_name else "غير محدد"
            status_text = "نشط" if u.is_active else "موقوف"
            rows.append(Row(
                cells=[
                    u.full_name, u.username, role_str,
                    Badge(status_text, "active" if u.is_active else "inactive"),
                ],
                actions=[
                    Action("edit", "تعديل",
                           (lambda user=u: self.on_edit_user(user)), "primary"),
                    Action("delete", "حذف",
                           (lambda user=u: self.on_delete_user(user)), "danger"),
                ],
                search=f"{u.full_name} {u.username} {role_str}",
                sort=[u.full_name, u.username, role_str, status_text],
                tags={"الحالة": u.is_active},
            ))
        self.users_table.set_records(rows)

    def load_logs(self):
        try:
            with busy(self, "جاري تحميل السجلات..."):
                logs_with_users = self.audit_service.get_all_logs()[:500]
                rows = []
                for log, username in logs_with_users:
                    ts = log.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                    user = username or "System"
                    rows.append(Row(
                        cells=[ts, user, log.module, log.action, log.entity_type or "-"],
                        search=f"{user} {log.module} {log.action}",
                        sort=[ts, user, log.module, log.action, log.entity_type or "-"],
                    ))
                self.logs_table.set_records(rows)
        except Exception as e:
            logger.error(f"Logs load failed: {e}")
            Toast.error(self, "حدث خطأ أثناء جلب السجلات")

    def load_full_log(self):
        """Refresh the list of available log dates, then display the selected one.
        Superadmin-only tab; the widgets are absent for other roles."""
        if not hasattr(self, "log_date_combo"):
            return
        files = list_log_files()  # [(label, Path), ...] newest first
        combo = self.log_date_combo
        # Repopulate without firing currentIndexChanged for each add; keep the
        # previously-selected date if it still exists, otherwise show the newest.
        previous = combo.currentData()
        combo.blockSignals(True)
        combo.clear()
        for label, path in files:
            combo.addItem(label, str(path))
        idx = combo.findData(previous) if previous else -1
        combo.setCurrentIndex(idx if idx >= 0 else 0)
        combo.blockSignals(False)
        self._display_selected_log()

    def _display_selected_log(self):
        """Read and show the log file for the date currently chosen in the combo."""
        if not hasattr(self, "full_log_view"):
            return
        path = self.log_date_combo.currentData()
        if not path:
            self.full_log_view.set_log_text("لا يوجد سجل متاح بعد.")
            return
        try:
            with busy(self, "جاري تحميل السجل الكامل..."):
                content = read_log_tail(path)
            self.full_log_view.set_log_text(content or "ملف السجل فارغ.")
        except Exception as e:
            logger.error(f"Full log load failed: {e}")
            Toast.error(self, "حدث خطأ أثناء جلب السجل الكامل")

    def _export_table(self, dest: str, selected_filter: str, title: str,
                      headers: list, rows: list):
        """Write `rows` to `dest` as Excel or PDF (never CSV), choosing the format
        from the file type and fixing the extension if the user omitted it."""
        is_pdf = dest.lower().endswith(".pdf") or "pdf" in (selected_filter or "").lower()
        if is_pdf:
            if not dest.lower().endswith(".pdf"):
                dest += ".pdf"
            self.report_engine.export_to_pdf(title, headers, rows, title=title, dest_path=dest)
        else:
            if not dest.lower().endswith(".xlsx"):
                dest += ".xlsx"
            self.report_engine.export_to_excel(title, headers, rows, title=title, dest_path=dest)

    def on_export_audit_logs(self):
        """Export the database audit trail to Excel or PDF (never CSV)."""
        if not self.report_engine:
            Toast.error(self, "محرّك التقارير غير متاح")
            return
        default = f"CSCN_audit_logs_{datetime.now():%Y%m%d_%H%M%S}"
        dest, selected = QFileDialog.getSaveFileName(
            self, "تصدير سجل العمليات", default, "Excel (*.xlsx);;PDF (*.pdf)")
        if not dest:
            return
        headers = ["التاريخ والوقت", "المستخدم", "الوحدة", "الإجراء", "الكيان"]
        try:
            with busy(self, "جاري تصدير السجلات..."):
                rows = []
                for log, username in self.audit_service.get_all_logs():
                    ts = log.timestamp.strftime("%Y-%m-%d %H:%M:%S") if log.timestamp else ""
                    rows.append([ts, username or "System", log.module,
                                 log.action, log.entity_type or ""])
                self._export_table(dest, selected, "سجل العمليات", headers, rows)
            Toast.success(self, "تم تصدير سجل العمليات بنجاح")
        except Exception as e:
            logger.error(f"Audit logs export failed: {e}")
            Toast.error(self, "تعذّر تصدير السجلات")

    def on_export_full_log(self):
        """Export the full file-based log for the selected date to Excel or PDF
        (parsed into time/level/source/message columns; never CSV)."""
        if not self.report_engine:
            Toast.error(self, "محرّك التقارير غير متاح")
            return
        path = self.log_date_combo.currentData()
        if not path:
            Toast.error(self, "لا يوجد سجل لتصديره")
            return
        default = f"CSCN_log_{self.log_date_combo.currentText().replace(' ', '_')}"
        dest, selected = QFileDialog.getSaveFileName(
            self, "تصدير السجل الكامل", default, "Excel (*.xlsx);;PDF (*.pdf)")
        if not dest:
            return
        headers = ["الوقت", "المستوى", "المصدر", "الرسالة"]
        try:
            with busy(self, "جاري تصدير السجل..."):
                # Read the whole file (rotation caps each file at 10 MB).
                content = read_log_tail(path, max_bytes=20_000_000)
                rows = parse_log_lines(content)
                self._export_table(dest, selected, "السجل الكامل", headers, rows)
            Toast.success(self, "تم تصدير السجل بنجاح")
        except Exception as e:
            logger.error(f"Full log export failed: {e}")
            Toast.error(self, "تعذّر تصدير السجل")

    def _can(self, action: str) -> bool:
        if not self.permission_service:
            return True
        return self.permission_service.has_permission("users", action)

    def on_add_user(self):
        if not self._can("create"):
            Toast.error(self, "ليس لديك صلاحية لإضافة مستخدمين")
            return
        dialog = UserDialog(self.auth_service, self)
        if dialog.exec():
            self.load_users()
            self.load_logs()
            Toast.success(self, "تمت إضافة المستخدم بنجاح")

    def on_edit_user(self, user):
        if not self._can("edit"):
            Toast.error(self, "ليس لديك صلاحية لتعديل المستخدمين")
            return
        dialog = UserDialog(self.auth_service, self, user)
        if dialog.exec():
            self.load_users()
            self.load_logs()
            Toast.success(self, "تم حفظ التعديلات بنجاح")

    def on_delete_user(self, user):
        if not self._can("delete"):
            Toast.error(self, "ليس لديك صلاحية لحذف المستخدمين")
            return
        current = self.auth_service.get_current_user()
        if current and current.id == user.id:
            Toast.error(self, "لا يمكنك حذف حسابك الحالي")
            return
        if user.role_name == "superadmin":
            Toast.error(self, "لا يمكن حذف مدير النظام")
            return
        if not confirm(self, f"هل تريد حذف المستخدم \"{user.username}\"؟"):
            return
        try:
            self.auth_service.delete_user(user.id)
            Toast.success(self, "تم الحذف بنجاح")
            self.load_users()
        except IntegrityError:
            Toast.error(self, "لا يمكن الحذف لارتباط المستخدم بسجلات النظام")
        except Exception as e:
            logger.error(f"Delete user failed: {e}")
            Toast.error(self, "تعذّر الحذف")
