"""Headless (offscreen) UI smoke tests.

Builds the full MainWindow and every dialog to catch import errors, broken
stylesheet generation, icon failures, and page/dialog construction crashes.
Widgets are registered with qtbot so Qt tears them down cleanly (avoids
interpreter-exit segfaults under the offscreen platform).
"""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("qtpy")


def test_stylesheet_builds():
    from ui.themes.stylesheet import build_stylesheet
    css = build_stylesheet()
    assert "QPushButton" in css and len(css) > 1000


def test_mainwindow_builds_all_pages(qtbot, db_session):
    """Construct MainWindow and (as superadmin) build every page; must not raise."""
    from qtpy.QtWidgets import QApplication
    from ui.themes.stylesheet import build_stylesheet
    import main as app_main
    from ui.main_window import MainWindow
    from application.services.auth_service import AuthService
    from application.dto.user_dto import UserDTO
    from domain.entities.user import Role

    QApplication.instance().setStyleSheet(build_stylesheet())
    app_main.seed_initial_data(db_session)
    app_main.reconcile_permissions(db_session)
    services = app_main.build_services(db_session)

    sa = db_session.query(Role).filter(Role.name == "superadmin").one()
    AuthService._current_user = UserDTO(
        id=1, username="superadmin", full_name="SA",
        role_id=sa.id, role_name="superadmin", is_active=True)

    window = MainWindow(services)
    qtbot.addWidget(window)
    window.on_login_success()  # builds the dashboard for the logged-in user
    qtbot.wait(10)
    assert window.dashboard_page is not None and window.dashboard_page.modules
    window.close()


def test_all_dialogs_construct(qtbot, db_session):
    """Every migrated dialog must build without error."""
    import main as app_main

    app_main.seed_initial_data(db_session)
    s = app_main.build_services(db_session)

    from ui.pages.standards.standard_dialog import StandardDialog
    from ui.pages.documents.document_dialog import DocumentDialog
    from ui.pages.records.record_dialog import RecordDialog
    from ui.pages.training.training_dialog import TrainingDialog
    from ui.pages.financial.transaction_dialog import TransactionDialog
    from ui.pages.admin.user_dialog import UserDialog
    from ui.pages.admin.profile_dialog import ProfileDialog
    from ui.pages.hr.employee_dialog import EmployeeDialog
    from ui.pages.partnerships.partnership_dialog import (
        PartnershipDialog, PartnerDetailsDialog, AgreementsDialog, AddAgreementDialog,
    )
    from ui.pages.standards.indicator_dialog import IndicatorsDialog, IndicatorDialog
    from ui.pages.training.program_detail import (
        ProgramDetailDialog, SessionDialog, TraineeDialog,
    )
    from ui.pages.financial.budget_management import FiscalYearDialog, BudgetItemDialog
    from application.services.partnership_service import PartnershipDTO
    from application.services.hr_service import EmployeeDTO
    from application.services.quality_service import StandardDTO
    from application.services.training_service import TrainingProgramDTO
    from application.services.financial_service import FiscalYearDTO
    from datetime import date

    partner = s["partnership"].add_partner(PartnershipDTO(name="جهة اختبار"))
    emp = s["hr"].add_employee(EmployeeDTO(full_name="موظف اختبار"))
    standard = s["quality"].create_standard(StandardDTO(code="C1", name="معيار"))
    program = s["training"].create_program(TrainingProgramDTO(name="برنامج", program_type="course"))
    fy = s["financial"].create_fiscal_year(FiscalYearDTO(
        name="2026", start_date=date(2026, 1, 1), end_date=date(2026, 12, 31)))

    dialogs = [
        StandardDialog(s["quality"]),
        DocumentDialog(s["document"]),
        RecordDialog(s["record"]),
        TrainingDialog(s["training"]),
        TransactionDialog(s["financial"]),
        UserDialog(s["auth"]),
        ProfileDialog(s["auth"]),
        EmployeeDialog(s["hr"]),
        EmployeeDialog(s["hr"], None, emp),  # edit mode -> sub-tables
        PartnershipDialog(s["partnership"]),
        PartnerDetailsDialog(partner),
        AgreementsDialog(s["partnership"], partner),
        AddAgreementDialog(s["partnership"], partner),
        IndicatorsDialog(s["quality"], standard),
        IndicatorDialog(s["quality"], standard),
        ProgramDetailDialog(s["training"], program),
        SessionDialog(s["training"], program, units=[("كورس: x", ("course", 1))]),
        TraineeDialog(s["training"]),
        FiscalYearDialog(s["financial"]),
        BudgetItemDialog(s["financial"], fy.id),
    ]
    for dlg in dialogs:
        qtbot.addWidget(dlg)
    qtbot.wait(10)
    assert len(dialogs) == 20
