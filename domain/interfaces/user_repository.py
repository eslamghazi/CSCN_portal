from typing import Optional
from domain.interfaces.base_repository import BaseRepository
from domain.entities.user import User

class UserRepository(BaseRepository[User]):
    """
    Interface for User repository.
    """
    
    def get_by_username(self, username: str) -> Optional[User]:
        """Fetch a user by their username."""
        pass
    
    def has_admin_user(self) -> bool:
        """Check if at least one admin user exists."""
        pass
