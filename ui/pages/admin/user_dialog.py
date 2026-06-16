from qtpy.QtWidgets import QLineEdit, QComboBox

from ui.dialogs.base_dialog import BaseDialog
from ui.widgets.toast import Toast
from application.services.auth_service import AuthService
from application.dto.user_dto import UserDTO, UserCreateDTO
from application.validators.validators import is_valid_email

ROLE_LABELS = {
    "superadmin": "مدير نظام (Superadmin)",
    "admin": "مشرف (Admin)",
    "user": "مستخدم عادي",
}


class UserDialog(BaseDialog):
    def __init__(self, auth_service: AuthService, parent=None, user: UserDTO = None):
        super().__init__("إضافة مستخدم جديد" if not user else "تعديل المستخدم", parent)
        self.auth_service = auth_service
        self.user = user
        # name -> id, loaded from DB (no hardcoded ids).
        self.roles = {name: rid for rid, name in self.auth_service.get_all_roles()}

        self.fullname_field = self.add_field("الاسم بالكامل:", QLineEdit(), required=True)
        self.username_field = self.add_field("اسم المستخدم:", QLineEdit(), required=True)
        self.email_field, self.phone_field = self.add_row(
            ("البريد الإلكتروني:", QLineEdit()), ("رقم الهاتف:", QLineEdit()))

        role_combo = QComboBox()
        for name, rid in self.roles.items():
            role_combo.addItem(ROLE_LABELS.get(name, name), rid)
        status_combo = QComboBox()
        status_combo.addItems(["نشط", "غير نشط"])
        self.role_field, self.status_field = self.add_row(
            ("الصلاحية:", role_combo), ("الحالة:", status_combo))

        # Password: required when creating; optional when editing (blank = keep
        # the current password). Lets a superadmin reset any user's password here.
        pw = QLineEdit()
        pw.setEchoMode(QLineEdit.Password)
        if not self.user:
            self.password_field = self.add_field("كلمة المرور:", pw, required=True)
        else:
            self.password_field = self.add_field(
                "كلمة مرور جديدة (اتركها فارغة لعدم التغيير):", pw, required=False)

        self.build_buttons()
        self.populate_data()

    def populate_data(self):
        if not self.user:
            return
        self.fullname_field.widget.setText(self.user.full_name)
        self.username_field.widget.setText(self.user.username)
        self.email_field.widget.setText(self.user.email or "")
        self.phone_field.widget.setText(self.user.phone or "")
        if self.user.role_id:
            idx = self.role_field.widget.findData(self.user.role_id)
            if idx >= 0:
                self.role_field.widget.setCurrentIndex(idx)
        self.status_field.widget.setCurrentIndex(0 if self.user.is_active else 1)

    def on_save(self):
        self.fullname_field.clear_error()
        self.username_field.clear_error()
        self.email_field.clear_error()
        self.password_field.clear_error()
        fullname = self.fullname_field.text().strip()
        username = self.username_field.text().strip()
        email = self.email_field.text().strip()
        if not fullname:
            self.fullname_field.set_error("الاسم مطلوب.")
            return
        if not username:
            self.username_field.set_error("اسم المستخدم مطلوب.")
            return
        if email and not is_valid_email(email):
            self.email_field.set_error("بريد إلكتروني غير صالح.")
            return
        new_password = self.password_field.text().strip()
        if not self.user and not new_password:
            self.password_field.set_error("كلمة المرور مطلوبة للمستخدم الجديد.")
            return
        if new_password and len(new_password) < 4:
            self.password_field.set_error("كلمة المرور قصيرة جدًا.")
            return

        role_id = self.role_field.widget.currentData()
        is_active = self.status_field.widget.currentIndex() == 0

        # Only a superadmin may create/edit superadmin accounts.
        current_user = self.auth_service.get_current_user()
        superadmin_role_id = self.roles.get("superadmin")
        if current_user.role_name != "superadmin" and role_id == superadmin_role_id:
            Toast.error(self, "صلاحيات مدير النظام تقتصر على مديري النظام فقط")
            return

        if self.user:
            if current_user.role_name != "superadmin" and self.user.role_name == "superadmin":
                Toast.error(self, "لا يمكنك تعديل بيانات مدير النظام")
                return
            dto = UserDTO(
                id=self.user.id,
                username=username,
                full_name=fullname,
                email=self.email_field.text().strip() or None,
                phone=self.phone_field.text().strip() or None,
                role_id=role_id,
                is_active=is_active,
            )
            result = self.auth_service.update_user(self.user.id, dto)
            # Reset the password too, if a new one was provided.
            if result.success and new_password:
                self.auth_service.change_password(self.user.id, new_password)
        else:
            dto = UserCreateDTO(
                username=username,
                password=new_password,
                full_name=fullname,
                email=self.email_field.text().strip() or None,
                phone=self.phone_field.text().strip() or None,
                role_id=role_id,
            )
            result = self.auth_service.create_user(dto)

        if result.success:
            self.accept()
        else:
            self.username_field.set_error(result.message)
