import socket
from datetime import datetime
from typing import List

from qtpy.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox, QLabel, QLineEdit,
    QSpinBox, QFileDialog, QApplication, QTabWidget,
)
from loguru import logger

from ui.widgets.card import Card
from ui.widgets.page_header import PageHeader
from ui.widgets.icon_button import IconButton
from ui.widgets.toast import Toast
from ui.widgets.loading_overlay import LoadingOverlay
from ui.widgets.data_table import DataTable, Row
from ui.themes.colors import Colors
from application.services import peer_client, firewall
from application.services.peer_server import DEFAULT_PORT, get_token

DEFAULT_HOST = "10.25.12.124"


def local_ip_addresses() -> List[str]:
    """Best-effort list of this machine's LAN IPv4 addresses, primary first."""
    ips = []

    # The primary outbound interface (no traffic is actually sent).
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ips.append(s.getsockname()[0])
        s.close()
    except OSError:
        pass

    # Any other interfaces bound to the hostname.
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ip = info[4][0]
            if ip not in ips:
                ips.append(ip)
    except OSError:
        pass

    return [ip for ip in ips if not ip.startswith("127.")]


class RemotePortalsView(QWidget):
    """Superadmin-only. Two modes:
      * هذا الجهاز  — share this PC's connection details so another PC can pull from it.
      * الاتصال بجهاز آخر — connect to a portal on the LAN to pull all data and logs.
    """

    def __init__(self, permission=None):
        super().__init__()
        self.permission = permission
        self.setup_ui()
        self._refresh_server_info()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        main_layout.addWidget(PageHeader(
            "البوابات والإدارة عن بُعد",
            subtitle="شارك بيانات هذا الجهاز ليتم سحبها، أو اتصل بجهاز آخر على الشبكة الداخلية."))

        self.mode_tabs = QTabWidget()
        self.mode_tabs.addTab(self._build_server_tab(), "هذا الجهاز (مصدر البيانات)")
        self.mode_tabs.addTab(self._build_client_tab(), "الاتصال بجهاز آخر")
        main_layout.addWidget(self.mode_tabs, 1)  # stretch: fill the whole page

        self.overlay = LoadingOverlay(self)

    # ------------------------------------------------------------------ server
    def _build_server_tab(self) -> QWidget:
        tab = QWidget()
        outer = QVBoxLayout(tab)
        outer.setContentsMargins(2, 14, 2, 2)
        outer.setSpacing(16)

        card = Card()
        card.add(PageHeader(
            "اجعل هذا الجهاز مصدرًا للبيانات",
            subtitle="هذا الجهاز يعمل كخادم على الشبكة. أدخِل البيانات التالية في الجهاز الآخر لسحب البيانات والسجلات منه."))

        # Connection details the OTHER PC must enter (read-only, selectable).
        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(12)
        grid.setColumnStretch(1, 1)

        self.ip_value = self._readonly_field()
        self.port_value = self._readonly_field(str(DEFAULT_PORT))
        self.token_value = self._readonly_field(get_token())
        grid.addWidget(self._field_label("عنوان IP:"), 0, 0)
        grid.addWidget(self.ip_value, 0, 1)
        grid.addWidget(self._field_label("المنفذ:"), 1, 0)
        grid.addWidget(self.port_value, 1, 1)
        grid.addWidget(self._field_label("رمز الوصول:"), 2, 0)
        grid.addWidget(self.token_value, 2, 1)
        card.add_layout(grid)

        # Extra interfaces (if the machine has more than one IP).
        self.other_ips_label = QLabel("")
        self.other_ips_label.setWordWrap(True)
        self.other_ips_label.setStyleSheet(
            f"color: {Colors.TEXT_SECONDARY}; background: transparent;")
        card.add(self.other_ips_label)

        # Step-by-step instructions for the other PC.
        steps = QLabel(
            "على الجهاز الآخر:\n"
            "‎1) افتح صفحة «البوابات والإدارة عن بُعد».\n"
            "‎2) اختر تبويب «الاتصال بجهاز آخر».\n"
            "‎3) أدخِل عنوان الـ IP والمنفذ ورمز الوصول الظاهرة أعلاه.\n"
            "‎4) اضغط «اختبار الاتصال» ثم «تنزيل كل البيانات» أو «عرض السجلات».")
        steps.setWordWrap(True)
        steps.setStyleSheet(
            f"color: {Colors.TEXT}; background: {Colors.SURFACE_ALT};"
            f" border: 1px solid {Colors.BORDER}; border-radius: 8px; padding: 12px;")
        card.add(steps)

        # Actions: copy details, allow through firewall, refresh.
        actions = QHBoxLayout()
        copy_btn = IconButton("نسخ بيانات الاتصال", "browse", variant="secondary")
        copy_btn.clicked.connect(self.on_copy_connection)
        fw_btn = IconButton("السماح عبر جدار الحماية", "admin", variant="primary")
        fw_btn.clicked.connect(self.on_allow_firewall)
        refresh_btn = IconButton("تحديث", "refresh", variant="secondary")
        refresh_btn.clicked.connect(self._refresh_server_info)
        actions.addWidget(copy_btn)
        actions.addWidget(fw_btn)
        actions.addWidget(refresh_btn)
        actions.addStretch()
        card.add_layout(actions)

        outer.addWidget(card)
        outer.addStretch()
        return tab

    def _readonly_field(self, text: str = "") -> QLineEdit:
        field = QLineEdit(text)
        field.setReadOnly(True)
        field.setMinimumHeight(38)
        field.setStyleSheet("font-size: 15px; font-weight: 600;")
        return field

    @staticmethod
    def _field_label(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("background: transparent; font-weight: 600;")
        return lbl

    def _refresh_server_info(self):
        ips = local_ip_addresses()
        primary = ips[0] if ips else "غير متاح"
        self.ip_value.setText(primary)
        self.port_value.setText(str(DEFAULT_PORT))
        self.token_value.setText(get_token())
        if len(ips) > 1:
            self.other_ips_label.setText("عناوين أخرى لهذا الجهاز: " + "، ".join(ips[1:]))
        else:
            self.other_ips_label.setText("")

    def on_copy_connection(self):
        text = (f"IP: {self.ip_value.text()} | المنفذ: {self.port_value.text()} | "
                f"رمز الوصول: {self.token_value.text()}")
        QApplication.clipboard().setText(text)
        Toast.success(self, "تم نسخ بيانات الاتصال")

    def on_allow_firewall(self):
        if not firewall.is_windows():
            Toast.error(self, "هذه الميزة متاحة على نظام ويندوز فقط")
            return
        if firewall.allow_port(DEFAULT_PORT):
            Toast.success(
                self, "تم إرسال طلب السماح. وافق على نافذة صلاحيات المدير إن ظهرت.")
        else:
            Toast.error(self, "تعذّر إضافة قاعدة جدار الحماية (رُفضت الصلاحية)")

    # ------------------------------------------------------------------ client
    def _build_client_tab(self) -> QWidget:
        tab = QWidget()
        outer = QVBoxLayout(tab)
        outer.setContentsMargins(2, 14, 2, 2)
        outer.setSpacing(16)

        card = Card()
        card.add(PageHeader(
            "الاتصال بجهاز آخر",
            subtitle="اتصل ببوابة المركز على الشبكة الداخلية لتنزيل كل البيانات وعرض السجلات."))

        # Connection settings
        conn = QGroupBox("بيانات الاتصال")
        form = QHBoxLayout()
        self.host_input = QLineEdit(DEFAULT_HOST)
        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(DEFAULT_PORT)
        self.token_input = QLineEdit(get_token())
        form.addWidget(QLabel("عنوان IP:"))
        form.addWidget(self.host_input)
        form.addWidget(QLabel("المنفذ:"))
        form.addWidget(self.port_input)
        form.addWidget(QLabel("رمز الوصول:"))
        form.addWidget(self.token_input)
        conn.setLayout(form)
        card.add(conn)

        # Actions
        actions = QHBoxLayout()
        self.ping_btn = IconButton("اختبار الاتصال", "remote", variant="secondary")
        self.ping_btn.clicked.connect(self.on_ping)
        self.logs_btn = IconButton("عرض السجلات", "view", variant="secondary")
        self.logs_btn.clicked.connect(self.on_fetch_logs)
        self.download_btn = IconButton("تنزيل كل البيانات", "download", variant="primary")
        self.download_btn.clicked.connect(self.on_download)
        actions.addWidget(self.ping_btn)
        actions.addWidget(self.logs_btn)
        actions.addWidget(self.download_btn)
        actions.addStretch()
        self.status_label = QLabel("")
        self.status_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; background: transparent;")
        actions.addWidget(self.status_label)
        card.add_layout(actions)

        # Remote logs table — stretches to fill the rest of the page.
        self.table = DataTable(["التاريخ", "المستخدم", "الوحدة", "الإجراء", "الكيان"])
        card.add(self.table)
        card.body.setStretchFactor(self.table, 1)

        outer.addWidget(card, 1)
        return tab

    def _conn(self):
        return self.host_input.text().strip(), self.port_input.value(), self.token_input.text().strip()

    def on_ping(self):
        host, port, _ = self._conn()
        self.overlay.start("جارٍ الاتصال...")
        QApplication.processEvents()
        try:
            info = peer_client.ping(host, port)
            self.status_label.setText(f"متصل ✓ ({info.get('app', '')})")
            Toast.success(self, "البوابة متصلة")
        except Exception as e:
            logger.error(f"Ping failed: {e}")
            self.status_label.setText("غير متصل ✗")
            Toast.error(self, "تعذّر الاتصال بالبوابة")
        finally:
            self.overlay.stop()

    def on_fetch_logs(self):
        host, port, token = self._conn()
        self.overlay.start("جارٍ جلب السجلات...")
        QApplication.processEvents()
        try:
            logs = peer_client.fetch_logs(host, port, token)
            rows = [
                Row(cells=[lg["timestamp"], lg["user"], lg["module"], lg["action"], lg["entity"]],
                    search=f"{lg['user']} {lg['module']} {lg['action']}",
                    sort=[lg["timestamp"], lg["user"], lg["module"], lg["action"], lg["entity"]])
                for lg in logs
            ]
            self.table.set_records(rows)
            Toast.success(self, f"تم جلب {len(rows)} سجل")
        except Exception as e:
            logger.error(f"Fetch logs failed: {e}")
            Toast.error(self, "تعذّر جلب السجلات")
        finally:
            self.overlay.stop()

    def on_download(self):
        host, port, token = self._conn()
        default = f"CSCN_remote_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        dest, _ = QFileDialog.getSaveFileName(self, "حفظ نسخة البيانات", default, "ZIP (*.zip)")
        if not dest:
            return
        self.overlay.start("جارٍ تنزيل البيانات...")
        QApplication.processEvents()
        try:
            peer_client.download_export(host, port, token, dest)
            Toast.success(self, "تم تنزيل كل البيانات بنجاح")
        except Exception as e:
            logger.error(f"Remote download failed: {e}")
            Toast.error(self, "تعذّر تنزيل البيانات")
        finally:
            self.overlay.stop()
