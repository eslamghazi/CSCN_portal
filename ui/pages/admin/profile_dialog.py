from qtpy.QtWidgets import QLineEdit

from ui.dialogs.base_dialog import BaseDialog
from ui.widgets.toast import Toast
from application.services.auth_service import AuthService


class ProfileDialog(BaseDialog):
    def __init__(self, auth_service: AuthService, parent=None):
        super().__init__("إعدادات الحساب", parent, min_width=420)
        self.auth_service = auth_service
        self.current_user = self.auth_service.get_current_user()

        # Normal users may not change their password here (admins/superadmin do).
        self.can_change_password = bool(
            self.current_user and self.current_user.role_name != "user")

        self.username_field = self.add_field("اسم المستخدم:", QLineEdit(), required=True)

        if self.can_change_password:
            pw = QLineEdit()
            pw.setPlaceholderText("اتركها فارغة إذا لم ترد تغييرها")
            pw.setEchoMode(QLineEdit.Password)
            self.password_field = self.add_field("كلمة المرور الجديدة (اختياري):", pw)

            confirm = QLineEdit()
            confirm.setEchoMode(QLineEdit.Password)
            self.confirm_field = self.add_field("تأكيد كلمة المرور الجديدة:", confirm)
        else:
            self.password_field = None
            self.confirm_field = None

        self.build_buttons(save_text="حفظ التعديلات")
        self.populate_data()

    def populate_data(self):
        if self.current_user:
            self.username_field.widget.setText(self.current_user.username)

    def on_save(self):
        self.username_field.clear_error()
        username = self.username_field.text().strip()

        if not username:
            self.username_field.set_error("اسم المستخدم مطلوب.")
            return

        password = None
        if self.can_change_password:
            self.confirm_field.clear_error()
            password = self.password_field.text()
            confirm = self.confirm_field.text()
            if password and password != confirm:
                self.confirm_field.set_error("كلمات المرور غير متطابقة.")
                return

        result = self.auth_service.update_own_profile(
            self.current_user.id,
            new_username=username,
            new_password=password if password else None,
        )
        if result.success:
            Toast.success(self, result.message)
            self.accept()
        else:
            self.username_field.set_error(result.message)
