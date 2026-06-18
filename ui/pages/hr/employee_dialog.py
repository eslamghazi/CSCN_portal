from qtpy.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QDateEdit, QSpinBox,
    QDoubleSpinBox, QTextEdit, QTabWidget, QWidget, QTableWidget, QTableWidgetItem,
    QHeaderView
)
from qtpy.QtCore import Qt, QDate
from loguru import logger

from ui.dialogs.base_dialog import BaseDialog, Field
from ui.widgets.icon_button import IconButton
from ui.widgets.confirm import confirm
from ui.widgets.toast import Toast
from ui.widgets.cell import cell_widget
from ui.themes.colors import Colors
from application.services.hr_service import HRService, EmployeeDTO
from application.validators.validators import is_valid_email
from domain.entities.employee import Employee


class _SubTable(QWidget):
    """A small titled table with add + per-row delete, used for an employee's
    qualifications / experience / evaluations."""

    def __init__(self, title, columns, load_fn, add_fn, delete_fn, edit_fn=None, parent=None):
        super().__init__(parent)
        self.load_fn = load_fn
        self.add_fn = add_fn
        self.delete_fn = delete_fn
        self.edit_fn = edit_fn

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        head = QHBoxLayout()
        label = QLabel(title)
        label.setStyleSheet(f"font-weight: 600; color: {Colors.PRIMARY};")
        head.addWidget(label)
        head.addStretch()
        add_btn = IconButton("إضافة", "add", variant="secondary", compact=True)
        add_btn.clicked.connect(self._on_add)
        head.addWidget(add_btn)
        layout.addLayout(head)

        self.table = QTableWidget(0, len(columns) + 1)
        self.table.setHorizontalHeaderLabels(list(columns) + ["إجراءات"])
        header = self.table.horizontalHeader()
        # Size every column to its content so headers (e.g. "المسمى الوظيفي") and
        # the action icons are never clipped; then stretch the last data column so
        # the table still fills its full width.
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        if columns:
            header.setSectionResizeMode(len(columns) - 1, QHeaderView.Stretch)
        header.setMinimumSectionSize(70)
        self.table.verticalHeader().setDefaultSectionSize(44)  # room for the buttons
        self.table.verticalHeader().hide()
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setMinimumHeight(140)
        layout.addWidget(self.table)

        self.refresh()

    def _on_add(self):
        if self.add_fn():
            self.refresh()

    def _on_delete(self, entity_id):
        if not confirm(self, "هل تريد حذف هذا العنصر؟"):
            return
        try:
            self.delete_fn(entity_id)
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            Toast.error(self, "تعذّر الحذف")
        self.refresh()

    def _on_edit(self, entity):
        if self.edit_fn(entity):
            self.refresh()

    def refresh(self):
        rows = self.load_fn()
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            values, entity_id = row[0], row[1]
            entity = row[2] if len(row) > 2 else None
            for c, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(r, c, item)
            actions = []
            if self.edit_fn is not None and entity is not None:
                edit_btn = IconButton(
                    icon_name="edit", variant="primary", tooltip="تعديل", icon_only=True)
                edit_btn.clicked.connect(lambda _=False, e=entity: self._on_edit(e))
                actions.append(edit_btn)
            del_btn = IconButton(
                icon_name="delete", variant="danger", tooltip="حذف", icon_only=True)
            del_btn.clicked.connect(lambda _=False, e=entity_id: self._on_delete(e))
            actions.append(del_btn)
            self.table.setCellWidget(r, len(values), cell_widget(*actions))


class _AddQualificationDialog(BaseDialog):
    def __init__(self, hr_service, employee_id, parent=None, qualification=None):
        super().__init__(
            "تعديل مؤهل علمي" if qualification else "إضافة مؤهل علمي", parent, min_width=440)
        self.hr_service = hr_service
        self.employee_id = employee_id
        self.qualification = qualification
        self.degree = self.add_field("الدرجة العلمية:", QLineEdit(), required=True)
        self.institution = self.add_field("الجهة المانحة:", QLineEdit(), required=True)
        year = QSpinBox()
        year.setRange(0, 2100)
        year.setSpecialValueText("غير محدد")
        self.year = self.add_field("سنة الحصول:", year)
        if qualification:
            self.degree.widget.setText(qualification.degree or "")
            self.institution.widget.setText(qualification.institution or "")
            year.setValue(qualification.year_obtained or 0)
        self.build_buttons()

    def on_save(self):
        self.degree.clear_error()
        self.institution.clear_error()
        degree = self.degree.text().strip()
        institution = self.institution.text().strip()
        if not degree:
            self.degree.set_error("الدرجة العلمية مطلوبة.")
            return
        if not institution:
            self.institution.set_error("الجهة المانحة مطلوبة.")
            return
        year = self.year.widget.value() or None
        try:
            if self.qualification:
                self.hr_service.update_qualification(
                    self.qualification.id, degree, institution, year)
            else:
                self.hr_service.add_qualification(
                    self.employee_id, degree, institution, year)
            self.accept()
        except Exception as e:
            logger.error(f"Save qualification failed: {e}")
            Toast.error(self, "تعذّر حفظ المؤهل")


class _AddExperienceDialog(BaseDialog):
    def __init__(self, hr_service, employee_id, parent=None, experience=None):
        super().__init__(
            "تعديل خبرة عملية" if experience else "إضافة خبرة عملية", parent, min_width=480)
        self.hr_service = hr_service
        self.employee_id = employee_id
        self.experience = experience
        self.job_title, self.company = self.add_row(
            ("المسمى الوظيفي:", QLineEdit(), True), ("جهة العمل:", QLineEdit(), True))
        start = QDateEdit()
        start.setCalendarPopup(True)
        start.setDate(QDate.currentDate().addYears(-1))
        end = QDateEdit()
        end.setCalendarPopup(True)
        end.setDate(QDate.currentDate())
        self.start, self.end = self.add_row(
            ("تاريخ البداية:", start), ("تاريخ النهاية:", end))
        notes = QTextEdit()
        notes.setMaximumHeight(70)
        self.description = self.add_field("الوصف:", notes)
        if experience:
            self.job_title.widget.setText(experience.job_title or "")
            self.company.widget.setText(experience.company or "")
            if experience.start_date:
                start.setDate(QDate(experience.start_date.year,
                                    experience.start_date.month, experience.start_date.day))
            if experience.end_date:
                end.setDate(QDate(experience.end_date.year,
                                  experience.end_date.month, experience.end_date.day))
            notes.setPlainText(experience.description or "")
        self.build_buttons()

    def on_save(self):
        self.job_title.clear_error()
        self.company.clear_error()
        job = self.job_title.text().strip()
        company = self.company.text().strip()
        if not job:
            self.job_title.set_error("المسمى الوظيفي مطلوب.")
            return
        if not company:
            self.company.set_error("جهة العمل مطلوبة.")
            return
        start_date = self.start.widget.date().toPython()
        end_date = self.end.widget.date().toPython()
        desc = self.description.text().strip() or None
        try:
            if self.experience:
                self.hr_service.update_experience(
                    self.experience.id, job, company, start_date, end_date, desc)
            else:
                self.hr_service.add_experience(
                    self.employee_id, job, company, start_date, end_date, desc)
            self.accept()
        except Exception as e:
            logger.error(f"Save experience failed: {e}")
            Toast.error(self, "تعذّر حفظ الخبرة")


class _AddEvaluationDialog(BaseDialog):
    def __init__(self, hr_service, employee_id, parent=None, evaluation=None):
        super().__init__(
            "تعديل تقييم" if evaluation else "إضافة تقييم", parent, min_width=460)
        self.hr_service = hr_service
        self.employee_id = employee_id
        self.evaluation = evaluation
        eval_date = QDateEdit()
        eval_date.setCalendarPopup(True)
        eval_date.setDate(QDate.currentDate())
        score = QDoubleSpinBox()
        score.setRange(0, 100)
        score.setDecimals(1)
        self.date, self.score = self.add_row(
            ("تاريخ التقييم:", eval_date), ("الدرجة (من 100):", score))
        notes = QTextEdit()
        notes.setMaximumHeight(80)
        self.notes = self.add_field("ملاحظات:", notes)
        if evaluation:
            if evaluation.evaluation_date:
                eval_date.setDate(QDate(evaluation.evaluation_date.year,
                                        evaluation.evaluation_date.month,
                                        evaluation.evaluation_date.day))
            score.setValue(evaluation.score or 0)
            notes.setPlainText(evaluation.notes or "")
        self.build_buttons()

    def on_save(self):
        try:
            eval_date = self.date.widget.date().toPython()
            score = self.score.widget.value()
            notes = self.notes.text().strip() or None
            if self.evaluation:
                self.hr_service.update_evaluation(
                    self.evaluation.id, eval_date, score, notes)
            else:
                self.hr_service.add_evaluation(
                    self.employee_id, eval_date, score, notes)
            self.accept()
        except Exception as e:
            logger.error(f"Save evaluation failed: {e}")
            Toast.error(self, "تعذّر حفظ التقييم")


class EmployeeDialog(BaseDialog):
    def __init__(self, hr_service: HRService, parent=None, employee: Employee = None):
        super().__init__(
            "إضافة موظف جديد" if not employee else "تعديل الموظف", parent, min_width=580)
        self.hr_service = hr_service
        self.employee = employee
        self.positions = self.hr_service.get_all_positions()

        tabs = QTabWidget()
        tabs.addTab(self._build_info_tab(), "البيانات الأساسية")
        tabs.addTab(self._build_records_tab(), "المؤهلات والخبرات")
        tabs.addTab(self._build_evaluations_tab(), "التقييمات")
        self.add_widget(tabs)

        self.build_buttons()
        self.populate_data()

    # ---------- info tab ----------
    def _build_info_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)

        name_label = QLabel(f"الاسم بالكامل: <span style='color:{Colors.DANGER}'>*</span>")
        name_label.setTextFormat(Qt.RichText)
        layout.addWidget(name_label)
        self.name_input = QLineEdit()
        layout.addWidget(self.name_input)
        self.name_error = QLabel("")
        self.name_error.setObjectName("fieldError")
        self.name_error.hide()
        layout.addWidget(self.name_error)
        self.name_field = Field(self.name_input, self.name_error)

        row1 = QHBoxLayout()
        email_col = QVBoxLayout()
        email_col.addWidget(QLabel("البريد الإلكتروني:"))
        self.email_input = QLineEdit()
        email_col.addWidget(self.email_input)
        phone_col = QVBoxLayout()
        phone_col.addWidget(QLabel("رقم الهاتف:"))
        self.phone_input = QLineEdit()
        phone_col.addWidget(self.phone_input)
        row1.addLayout(email_col)
        row1.addLayout(phone_col)
        layout.addLayout(row1)

        row2 = QHBoxLayout()
        pos_col = QVBoxLayout()
        pos_col.addWidget(QLabel("المنصب:"))
        self.position_combo = QComboBox()
        self.position_combo.addItem("غير محدد", None)
        for pos in self.positions:
            self.position_combo.addItem(pos.title, pos.id)
        pos_col.addWidget(self.position_combo)
        date_col = QVBoxLayout()
        date_col.addWidget(QLabel("تاريخ التعيين:"))
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        date_col.addWidget(self.date_input)
        row2.addLayout(pos_col)
        row2.addLayout(date_col)
        layout.addLayout(row2)

        layout.addWidget(QLabel("الحالة:"))
        self.status_combo = QComboBox()
        self.status_combo.addItems(["نشط", "غير نشط"])
        layout.addWidget(self.status_combo)
        layout.addStretch()
        return tab

    # ---------- qualifications + experience tab ----------
    def _build_records_tab(self) -> QWidget:
        if not self.employee:
            return self._hint("احفظ الموظف أولاً لإدارة المؤهلات والخبرات.")
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(14)
        eid = self.employee.id

        layout.addWidget(_SubTable(
            "المؤهلات العلمية",
            ["الدرجة", "الجهة المانحة", "سنة الحصول"],
            lambda: [
                ([q.degree, q.institution, q.year_obtained or "-"], q.id, q)
                for q in self.hr_service.get_qualifications(eid)
            ],
            lambda: _AddQualificationDialog(self.hr_service, eid, self).exec(),
            self.hr_service.delete_qualification,
            edit_fn=lambda q: _AddQualificationDialog(self.hr_service, eid, self, q).exec(),
        ))
        layout.addWidget(_SubTable(
            "الخبرات العملية",
            ["المسمى الوظيفي", "جهة العمل", "من", "إلى"],
            lambda: [
                ([
                    x.job_title, x.company,
                    x.start_date.isoformat() if x.start_date else "-",
                    x.end_date.isoformat() if x.end_date else "-",
                ], x.id, x)
                for x in self.hr_service.get_experience(eid)
            ],
            lambda: _AddExperienceDialog(self.hr_service, eid, self).exec(),
            self.hr_service.delete_experience,
            edit_fn=lambda x: _AddExperienceDialog(self.hr_service, eid, self, x).exec(),
        ))
        return tab

    # ---------- evaluations tab ----------
    def _build_evaluations_tab(self) -> QWidget:
        if not self.employee:
            return self._hint("احفظ الموظف أولاً لإدارة التقييمات.")
        eid = self.employee.id
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.addWidget(_SubTable(
            "تقييمات الأداء",
            ["تاريخ التقييم", "الدرجة", "ملاحظات"],
            lambda: [
                ([
                    ev.evaluation_date.isoformat() if ev.evaluation_date else "-",
                    ev.score if ev.score is not None else "-",
                    ev.notes or "-",
                ], ev.id, ev)
                for ev in self.hr_service.get_evaluations(eid)
            ],
            lambda: _AddEvaluationDialog(self.hr_service, eid, self).exec(),
            self.hr_service.delete_evaluation,
            edit_fn=lambda ev: _AddEvaluationDialog(self.hr_service, eid, self, ev).exec(),
        ))
        return tab

    def _hint(self, text: str) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        label = QLabel(text)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet(f"color: {Colors.TEXT_MUTED};")
        layout.addWidget(label)
        return tab

    def populate_data(self):
        if not self.employee:
            return
        self.name_input.setText(self.employee.full_name)
        self.email_input.setText(self.employee.email or "")
        self.phone_input.setText(self.employee.phone or "")
        if self.employee.position_id:
            idx = self.position_combo.findData(self.employee.position_id)
            if idx >= 0:
                self.position_combo.setCurrentIndex(idx)
        if self.employee.hire_date:
            self.date_input.setDate(self.employee.hire_date)
        self.status_combo.setCurrentIndex(0 if self.employee.status == "active" else 1)

    def on_save(self):
        self.name_field.clear_error()
        name = self.name_input.text().strip()
        if not name:
            self.name_field.set_error("اسم الموظف مطلوب.")
            return

        email = self.email_input.text().strip()
        if email and not is_valid_email(email):
            Toast.error(self, "بريد إلكتروني غير صالح")
            return

        dto = EmployeeDTO(
            full_name=name,
            email=self.email_input.text().strip() or None,
            phone=self.phone_input.text().strip() or None,
            position_id=self.position_combo.currentData(),
            hire_date=self.date_input.date().toPython(),
            status="active" if self.status_combo.currentIndex() == 0 else "inactive",
        )
        try:
            if self.employee:
                dto.id = self.employee.id
                self.hr_service.update_employee(dto)
            else:
                self.hr_service.add_employee(dto)
            self.accept()
        except Exception as e:
            logger.error(f"Save employee failed: {e}")
            Toast.error(self, "تعذّر حفظ بيانات الموظف")
