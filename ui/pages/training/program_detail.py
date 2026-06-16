from qtpy.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, QComboBox,
    QDateEdit, QSpinBox, QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QCheckBox
)
from qtpy.QtCore import Qt, QDate
from loguru import logger

from ui.dialogs.base_dialog import BaseDialog
from ui.widgets.icon_button import IconButton
from ui.widgets.toast import Toast
from ui.widgets.confirm import confirm
from ui.widgets.cell import cell_widget


class _UnitDialog(BaseDialog):
    """Add a course or workshop to a program."""

    def __init__(self, training_service, program, is_course, parent=None):
        kind = "كورس" if is_course else "ورشة"
        super().__init__(f"إضافة {kind}", parent, min_width=440)
        self.ts = training_service
        self.program = program
        self.is_course = is_course
        self.name = self.add_field(f"اسم ال{kind}:", QLineEdit(), required=True)
        desc = QTextEdit()
        desc.setMaximumHeight(70)
        self.desc = self.add_field("الوصف:", desc)
        self.build_buttons()

    def on_save(self):
        self.name.clear_error()
        name = self.name.text().strip()
        if not name:
            self.name.set_error("الاسم مطلوب.")
            return
        try:
            desc = self.desc.text().strip() or None
            if self.is_course:
                self.ts.create_course(self.program.id, name, desc)
            else:
                self.ts.create_workshop(self.program.id, name, desc)
            self.accept()
        except Exception as e:
            logger.error(f"Create unit failed: {e}")
            Toast.error(self, "تعذّر الحفظ")


class SessionDialog(BaseDialog):
    """Create/edit a session under a course or workshop."""

    def __init__(self, training_service, program, parent=None, session=None, units=None):
        super().__init__("إضافة جلسة" if not session else "تعديل الجلسة", parent, min_width=460)
        self.ts = training_service
        self.program = program
        self.session = session

        unit_combo = QComboBox()
        for label, data in (units or []):
            unit_combo.addItem(label, data)
        self.unit = self.add_field("الوحدة (كورس/ورشة):", unit_combo, required=True)
        if session:
            self.unit.widget.setEnabled(False)

        d = QDateEdit()
        d.setCalendarPopup(True)
        d.setDate(QDate.currentDate())
        dur = QSpinBox()
        dur.setRange(1, 24)
        dur.setValue(2)
        self.date, self.duration = self.add_row(
            ("تاريخ الجلسة:", d), ("المدة (ساعات):", dur))
        self.topic = self.add_field("الموضوع:", QLineEdit())
        self.build_buttons()
        self._populate()

    def _populate(self):
        if not self.session:
            return
        self.date.widget.setDate(self.session.session_date)
        self.duration.widget.setValue(self.session.duration_hours or 1)
        self.topic.widget.setText(self.session.topic or "")

    def on_save(self):
        try:
            if self.session:
                self.ts.update_session(
                    self.session.id, self.date.widget.date().toPython(),
                    self.duration.widget.value(), self.topic.text().strip() or None)
            else:
                unit = self.unit.widget.currentData()
                if not unit:
                    self.unit.set_error("اختر كورسًا أو ورشة.")
                    return
                kind, uid = unit
                self.ts.schedule_session(
                    session_date=self.date.widget.date().toPython(),
                    duration_hours=self.duration.widget.value(),
                    topic=self.topic.text().strip() or None,
                    course_id=uid if kind == "course" else None,
                    workshop_id=uid if kind == "workshop" else None,
                )
            self.accept()
        except Exception as e:
            logger.error(f"Save session failed: {e}")
            Toast.error(self, "تعذّر حفظ الجلسة")


class TraineeDialog(BaseDialog):
    def __init__(self, training_service, parent=None):
        super().__init__("إضافة متدرب", parent, min_width=460)
        self.ts = training_service
        self.name = self.add_field("الاسم بالكامل:", QLineEdit(), required=True)
        self.org, self.phone = self.add_row(
            ("الجهة:", QLineEdit()), ("رقم الهاتف:", QLineEdit()))
        self.email = self.add_field("البريد الإلكتروني:", QLineEdit())
        self.build_buttons()

    def on_save(self):
        self.name.clear_error()
        name = self.name.text().strip()
        if not name:
            self.name.set_error("الاسم مطلوب.")
            return
        try:
            self.ts.create_trainee(
                name, self.email.text().strip() or None,
                self.phone.text().strip() or None, self.org.text().strip() or None)
            self.accept()
        except Exception as e:
            logger.error(f"Create trainee failed: {e}")
            Toast.error(self, "تعذّر حفظ المتدرب")


class AttendanceDialog(BaseDialog):
    """Record attendance for a session across all trainees."""

    def __init__(self, training_service, session, parent=None):
        super().__init__("تسجيل الحضور", parent, min_width=520)
        self.ts = training_service
        self.session = session

        self.trainees = self.ts.get_all_trainees()
        present_ids = {
            a.trainee_id for a in self.ts.get_session_attendances(session.id) if a.is_present
        }

        if not self.trainees:
            self.add_widget(QLabel("لا يوجد متدربون. أضِف متدربين أولًا من تبويب المتدربين."))
        else:
            self.table = QTableWidget(len(self.trainees), 2)
            self.table.setHorizontalHeaderLabels(["المتدرب", "حاضر"])
            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.table.verticalHeader().hide()
            self.table.setEditTriggers(QTableWidget.NoEditTriggers)
            self._checks = []
            for r, t in enumerate(self.trainees):
                self.table.setItem(r, 0, QTableWidgetItem(t.full_name))
                check = QCheckBox()
                check.setChecked(t.id in present_ids)
                self._checks.append(check)
                self.table.setCellWidget(r, 1, cell_widget(check))
            self.add_widget(self.table)
        self.build_buttons(save_text="حفظ الحضور")

    def on_save(self):
        if not self.trainees:
            self.accept()
            return
        try:
            for trainee, check in zip(self.trainees, self._checks):
                self.ts.record_attendance(
                    self.session.id, trainee.id, check.isChecked())
            Toast.success(self, "تم حفظ الحضور")
            self.accept()
        except Exception as e:
            logger.error(f"Record attendance failed: {e}")
            Toast.error(self, "تعذّر حفظ الحضور")


def _table(columns):
    table = QTableWidget(0, len(columns))
    table.setHorizontalHeaderLabels(columns)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    table.verticalHeader().hide()
    table.setEditTriggers(QTableWidget.NoEditTriggers)
    table.setMinimumHeight(220)
    return table


class ProgramDetailDialog(BaseDialog):
    """Manage a program's units (courses/workshops), sessions and trainees."""

    def __init__(self, training_service, program, parent=None):
        super().__init__(f"إدارة البرنامج: {program.name}", parent, min_width=720)
        self.ts = training_service
        self.program = program

        tabs = QTabWidget()
        tabs.addTab(self._units_tab(), "الوحدات (كورسات/ورش)")
        tabs.addTab(self._sessions_tab(), "الجلسات")
        tabs.addTab(self._trainees_tab(), "المتدربون")
        self.add_widget(tabs)

        self._root.addStretch()
        close_row = QHBoxLayout()
        close_row.addStretch()
        close = IconButton("إغلاق", "cancel", variant="secondary")
        close.clicked.connect(self.accept)
        close_row.addWidget(close)
        self._root.addLayout(close_row)

        self.refresh_units()
        self.refresh_sessions()
        self.refresh_trainees()

    # ---- units ----
    def _units_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        bar = QHBoxLayout()
        bar.addStretch()
        add_c = IconButton("إضافة كورس", "add", variant="primary")
        add_c.clicked.connect(lambda: self._add_unit(True))
        add_w = IconButton("إضافة ورشة", "add", variant="secondary")
        add_w.clicked.connect(lambda: self._add_unit(False))
        bar.addWidget(add_c)
        bar.addWidget(add_w)
        layout.addLayout(bar)
        self.units_table = _table(["النوع", "الاسم", "الوصف"])
        layout.addWidget(self.units_table)
        return tab

    def _units(self):
        """Return list of (kind, entity) for the program's courses + workshops."""
        courses = [("course", c) for c in self.ts.get_program_courses(self.program.id)]
        workshops = [("workshop", w) for w in self.ts.get_program_workshops(self.program.id)]
        return courses + workshops

    def refresh_units(self):
        units = self._units()
        self.units_table.setRowCount(len(units))
        for r, (kind, u) in enumerate(units):
            label = "كورس" if kind == "course" else "ورشة"
            for c, text in enumerate([label, u.name, u.description or "-"]):
                item = QTableWidgetItem(str(text))
                item.setTextAlignment(Qt.AlignCenter)
                self.units_table.setItem(r, c, item)

    def _add_unit(self, is_course):
        if _UnitDialog(self.ts, self.program, is_course, self).exec():
            self.refresh_units()
            Toast.success(self, "تمت الإضافة")

    # ---- sessions ----
    def _sessions_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        bar = QHBoxLayout()
        bar.addStretch()
        add_btn = IconButton("إضافة جلسة", "add", variant="primary")
        add_btn.clicked.connect(self._add_session)
        bar.addWidget(add_btn)
        layout.addLayout(bar)
        self.sessions_table = _table(
            ["التاريخ", "المدة", "الموضوع", "الوحدة", "إجراءات"])
        layout.addWidget(self.sessions_table)
        return tab

    def _unit_options(self):
        options = []
        for kind, u in self._units():
            label = ("كورس: " if kind == "course" else "ورشة: ") + u.name
            options.append((label, (kind, u.id)))
        return options

    def _unit_name_maps(self):
        courses = {c.id: c.name for c in self.ts.get_program_courses(self.program.id)}
        workshops = {w.id: w.name for w in self.ts.get_program_workshops(self.program.id)}
        return courses, workshops

    def refresh_sessions(self):
        sessions = self.ts.get_program_sessions(self.program.id)
        courses, workshops = self._unit_name_maps()
        self.sessions_table.setRowCount(len(sessions))
        for r, s in enumerate(sessions):
            unit_name = courses.get(s.course_id) or workshops.get(s.workshop_id) or "-"
            values = [
                s.session_date.isoformat() if s.session_date else "-",
                str(s.duration_hours or "-"), s.topic or "-", unit_name,
            ]
            for c, text in enumerate(values):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter)
                self.sessions_table.setItem(r, c, item)
            att = IconButton(icon_name="hr", variant="secondary",
                             tooltip="الحضور", icon_only=True)
            att.clicked.connect(lambda _c=False, sess=s: self._attendance(sess))
            edit = IconButton(icon_name="edit", variant="primary",
                              tooltip="تعديل", icon_only=True)
            edit.clicked.connect(lambda _c=False, sess=s: self._edit_session(sess))
            dele = IconButton(icon_name="delete", variant="danger",
                              tooltip="حذف", icon_only=True)
            dele.clicked.connect(lambda _c=False, sess=s: self._delete_session(sess))
            self.sessions_table.setCellWidget(r, 4, cell_widget(att, edit, dele))

    def _add_session(self):
        options = self._unit_options()
        if not options:
            Toast.error(self, "أضِف كورسًا أو ورشة أولًا")
            return
        if SessionDialog(self.ts, self.program, self, units=options).exec():
            self.refresh_sessions()

    def _edit_session(self, session):
        if SessionDialog(self.ts, self.program, self, session=session).exec():
            self.refresh_sessions()

    def _delete_session(self, session):
        if not confirm(self, "هل تريد حذف هذه الجلسة؟"):
            return
        try:
            self.ts.delete_session(session.id)
            self.refresh_sessions()
            Toast.success(self, "تم الحذف")
        except Exception as e:
            logger.error(f"Delete session failed: {e}")
            Toast.error(self, "تعذّر الحذف")

    def _attendance(self, session):
        AttendanceDialog(self.ts, session, self).exec()

    # ---- trainees ----
    def _trainees_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        bar = QHBoxLayout()
        bar.addStretch()
        add_btn = IconButton("إضافة متدرب", "add", variant="primary")
        add_btn.clicked.connect(self._add_trainee)
        bar.addWidget(add_btn)
        layout.addLayout(bar)
        self.trainees_table = _table(["الاسم", "الجهة", "رقم الهاتف", "البريد"])
        layout.addWidget(self.trainees_table)
        return tab

    def refresh_trainees(self):
        trainees = self.ts.get_all_trainees()
        self.trainees_table.setRowCount(len(trainees))
        for r, t in enumerate(trainees):
            for c, text in enumerate(
                [t.full_name, t.organization or "-", t.phone or "-", t.email or "-"]
            ):
                item = QTableWidgetItem(str(text))
                item.setTextAlignment(Qt.AlignCenter)
                self.trainees_table.setItem(r, c, item)

    def _add_trainee(self):
        if TraineeDialog(self.ts, self).exec():
            self.refresh_trainees()
            Toast.success(self, "تمت إضافة المتدرب")
