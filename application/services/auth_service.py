import bcrypt
from typing import List, Optional, Tuple
from domain.interfaces.user_repository import UserRepository
from domain.entities.user import User
from application.dto.user_dto import UserDTO, UserCreateDTO, LoginResultDTO
from application.context import set_current_user, get_current_user_ctx, clear_current_user

class AuthService:
    """
    Service responsible for Authentication and Authorization logic.
    """

    # The "currently logged in user" is stored in a per-request/per-context
    # contextvar (see application.context) so it is isolated between concurrent
    # web requests. The desktop app shares the same mechanism.

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def hash_password(self, password: str) -> str:
        """Hash a plaintext password using bcrypt."""
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify a plaintext password against a stored hash."""
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

    def login(self, username: str, password: str) -> LoginResultDTO:
        """Authenticate a user and create a session."""
        user = self.user_repository.get_by_username(username)
        
        if not user:
            return LoginResultDTO(success=False, message="اسم المستخدم أو كلمة المرور غير صحيحة.")
            
        if not user.is_active:
            return LoginResultDTO(success=False, message="هذا الحساب غير مفعل.")
            
        if self.verify_password(password, user.password_hash):
            user_dict = {
                "id": user.id,
                "username": user.username,
                "full_name": user.full_name,
                "email": user.email,
                "phone": user.phone,
                "role_id": user.role_id,
                "role_name": user.role.name if user.role else None,
                "is_active": user.is_active
            }
            user_dto = UserDTO(**user_dict)
            set_current_user(user_dto)
            return LoginResultDTO(success=True, message="تم تسجيل الدخول بنجاح.", user=user_dto)
            
        return LoginResultDTO(success=False, message="اسم المستخدم أو كلمة المرور غير صحيحة.")

    def restore_session(self, user_id: int) -> Optional[UserDTO]:
        """Restore a saved session by user id (no password) for the
        'stay signed in' / auto-login feature. Returns the user DTO, or None if
        the account is missing or deactivated."""
        user = self.user_repository.get_by_id(user_id)
        if not user or not user.is_active:
            return None
        user_dto = UserDTO(
            id=user.id,
            username=user.username,
            full_name=user.full_name,
            email=user.email,
            phone=user.phone,
            role_id=user.role_id,
            role_name=user.role.name if user.role else None,
            is_active=user.is_active,
        )
        set_current_user(user_dto)
        return user_dto

    def logout(self) -> None:
        """Clear the current user session."""
        clear_current_user()

    @staticmethod
    def get_current_user() -> Optional[UserDTO]:
        """Get the currently logged in user (per-request contextvar)."""
        return get_current_user_ctx()

    @staticmethod
    def is_authenticated() -> bool:
        """Check if a user is logged in."""
        return get_current_user_ctx() is not None

    def get_all_roles(self) -> List[Tuple[int, str]]:
        """Return (id, name) for every role, for populating UI selectors
        instead of relying on hardcoded role ids."""
        from domain.entities.user import Role
        roles = self.user_repository.session.query(Role).order_by(Role.id).all()
        return [(r.id, r.name) for r in roles]

    def get_all_users(self) -> List[UserDTO]:
        users = self.user_repository.get_all()
        dtos = []
        for u in users:
            user_dict = {
                "id": u.id,
                "username": u.username,
                "full_name": u.full_name,
                "email": u.email,
                "phone": u.phone,
                "role_id": u.role_id,
                "role_name": u.role.name if u.role else None,
                "is_active": u.is_active
            }
            dtos.append(UserDTO(**user_dict))
        return dtos

    def delete_user(self, user_id: int) -> bool:
        """Delete a user account. Raises on FK constraints (e.g. audit logs)."""
        return self.user_repository.delete(user_id)

    def create_user(self, data: UserCreateDTO) -> LoginResultDTO:
        if self.user_repository.get_by_username(data.username):
            return LoginResultDTO(success=False, message="اسم المستخدم موجود مسبقاً.")
            
        new_user = User(
            username=data.username,
            password_hash=self.hash_password(data.password),
            full_name=data.full_name,
            email=data.email,
            phone=data.phone,
            role_id=data.role_id,
            is_active=True
        )
        
        created = self.user_repository.create(new_user)
        user_dict = {
            "id": created.id,
            "username": created.username,
            "full_name": created.full_name,
            "email": created.email,
            "phone": created.phone,
            "role_id": created.role_id,
            "role_name": created.role.name if created.role else None,
            "is_active": created.is_active
        }
        user_dto = UserDTO(**user_dict)
        return LoginResultDTO(success=True, message="تم إنشاء الحساب بنجاح.", user=user_dto)
        
    def update_user(self, user_id: int, data: UserDTO) -> LoginResultDTO:
        user = self.user_repository.get_by_id(user_id)
        if not user:
            return LoginResultDTO(success=False, message="المستخدم غير موجود.")
            
        # Check if username is changing to an existing one
        if user.username != data.username:
            existing = self.user_repository.get_by_username(data.username)
            if existing:
                return LoginResultDTO(success=False, message="اسم المستخدم مستخدم بالفعل.")
                
        user.username = data.username
        user.full_name = data.full_name
        user.email = data.email
        user.phone = data.phone
        user.role_id = data.role_id
        user.is_active = data.is_active
        
        updated = self.user_repository.update(user)
        user_dict = {
            "id": updated.id,
            "username": updated.username,
            "full_name": updated.full_name,
            "email": updated.email,
            "phone": updated.phone,
            "role_id": updated.role_id,
            "role_name": updated.role.name if updated.role else None,
            "is_active": updated.is_active
        }
        return LoginResultDTO(success=True, message="تم تحديث بيانات المستخدم.", user=UserDTO(**user_dict))

    def change_password(self, user_id: int, new_password: str) -> bool:
        user = self.user_repository.get_by_id(user_id)
        if not user:
            return False
            
        user.password_hash = self.hash_password(new_password)
        self.user_repository.update(user)
        return True

    def update_own_profile(self, user_id: int, new_username: str, new_password: Optional[str]) -> LoginResultDTO:
        user = self.user_repository.get_by_id(user_id)
        if not user:
            return LoginResultDTO(success=False, message="المستخدم غير موجود.")
            
        if user.username != new_username:
            existing = self.user_repository.get_by_username(new_username)
            if existing:
                return LoginResultDTO(success=False, message="اسم المستخدم مسجل مسبقاً.")
                
        user.username = new_username
        if new_password:
            user.password_hash = self.hash_password(new_password)
            
        updated = self.user_repository.update(user)
        
        user_dict = {
            "id": updated.id,
            "username": updated.username,
            "full_name": updated.full_name,
            "email": updated.email,
            "phone": updated.phone,
            "role_id": updated.role_id,
            "role_name": updated.role.name if updated.role else None,
            "is_active": updated.is_active
        }
        user_dto = UserDTO(**user_dict)
        set_current_user(user_dto)
        return LoginResultDTO(success=True, message="تم تحديث بيانات حسابك بنجاح.", user=user_dto)
