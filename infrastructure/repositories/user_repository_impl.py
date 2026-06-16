from typing import Optional
from sqlalchemy.orm import Session
from infrastructure.repositories.base_repository_impl import SQLAlchemyRepository
from domain.interfaces.user_repository import UserRepository
from domain.entities.user import User

class UserRepositoryImpl(SQLAlchemyRepository[User], UserRepository):
    """
    SQLAlchemy implementation of the UserRepository interface.
    """
    
    def __init__(self, session: Session):
        super().__init__(session, User)

    def get_by_username(self, username: str) -> Optional[User]:
        return self.session.query(User).filter(User.username == username).first()

    def has_admin_user(self) -> bool:
        """
        Check if any user exists.
        In a real scenario, this might check for a specific role.
        For now, if there are no users, the system has no admin.
        """
        return self.session.query(User).count() > 0
