from typing import TypeVar, Generic, List, Optional
from abc import ABC, abstractmethod

T = TypeVar('T')

class BaseRepository(Generic[T], ABC):
    """
    Abstract Base Class for all Repositories.
    Defines the standard CRUD interface.
    """
    
    @abstractmethod
    def get_by_id(self, id: int) -> Optional[T]:
        pass

    @abstractmethod
    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        pass

    @abstractmethod
    def create(self, entity: T) -> T:
        pass

    @abstractmethod
    def update(self, entity: T) -> T:
        pass

    @abstractmethod
    def delete(self, id: int) -> bool:
        pass
    
    @abstractmethod
    def count(self) -> int:
        pass
