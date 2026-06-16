from pydantic import BaseModel, ConfigDict
from typing import Optional

class UserDTO(BaseModel):
    id: Optional[int] = None
    username: str
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    role_id: Optional[int] = None
    role_name: Optional[str] = None
    is_active: bool = True
    
    model_config = ConfigDict(from_attributes=True)

class UserCreateDTO(BaseModel):
    username: str
    password: str
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    role_id: Optional[int] = None
    role_name: Optional[str] = None

class LoginResultDTO(BaseModel):
    success: bool
    message: str
    user: Optional[UserDTO] = None
