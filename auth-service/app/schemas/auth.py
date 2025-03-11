from pydantic import BaseModel, EmailStr
from typing import Optional, List

class UserBase(BaseModel):
    email: EmailStr
    username: str

class UserCreate(UserBase):
    password: str
    role: Optional[str] = "user"
    telegram_id: Optional[str] = None
    telegram_username: Optional[str] = None

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    telegram_id: Optional[str] = None
    telegram_username: Optional[str] = None

class UserResponse(UserBase):
    id: str
    is_active: bool
    role: str
    permissions: List[str] = []
    is_admin: bool = False
    telegram_id: Optional[str] = None
    telegram_username: Optional[str] = None

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    username: Optional[str] = None
    permissions: List[str] = []

class TelegramLink(BaseModel):
    telegram_id: str
    telegram_username: Optional[str] = None 