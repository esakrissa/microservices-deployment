from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime

class TelegramSessionBase(BaseModel):
    """Base schema for Telegram sessions."""
    telegram_id: str
    session_data: Dict[str, Any]

class TelegramSessionCreate(TelegramSessionBase):
    """Schema for creating a Telegram session."""
    pass

class TelegramSessionResponse(TelegramSessionBase):
    """Schema for Telegram session response."""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        """Pydantic config."""
        from_attributes = True 