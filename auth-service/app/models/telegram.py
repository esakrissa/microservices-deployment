from typing import Dict, Any, Optional
from datetime import datetime

class TelegramSession:
    """Model for Telegram sessions in Supabase."""
    
    def __init__(
        self,
        telegram_id: str,
        session_data: Dict[str, Any],
        id: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self.id = id
        self.telegram_id = telegram_id
        self.session_data = session_data
        self.created_at = created_at
        self.updated_at = updated_at
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TelegramSession':
        """Create a TelegramSession from a dictionary."""
        return cls(
            id=data.get('id'),
            telegram_id=data.get('telegram_id'),
            session_data=data.get('session_data', {}),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert the TelegramSession to a dictionary."""
        return {
            'id': self.id,
            'telegram_id': self.telegram_id,
            'session_data': self.session_data,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        } 