from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any, List, Union

class UserState:
    def __init__(self):
        self.state = None
        self.data = {}

class TelegramUpdate(BaseModel):
    update_id: int
    message: Optional[dict] = None
    callback_query: Optional[dict] = None
    
class MessageToProcess(BaseModel):
    content: str
    user_id: str

class MessageToSend(BaseModel):
    user_id: str
    content: str
    parse_mode: Optional[str] = None
    reply_markup: Optional[Dict[str, Any]] = None

class InlineKeyboardButton(BaseModel):
    text: str
    callback_data: Optional[str] = None
    url: Optional[str] = None

class InlineKeyboardMarkup(BaseModel):
    inline_keyboard: List[List[InlineKeyboardButton]] 