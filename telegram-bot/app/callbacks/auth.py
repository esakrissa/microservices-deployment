import logging
from typing import Dict, Any
from ..handlers.auth import handle_register_command, handle_login_command

logger = logging.getLogger(__name__)

async def handle_auth_register_callback(chat_id: int, callback_data: str) -> dict:
    """Handle the registration callback."""
    return await handle_register_command(str(chat_id))

async def handle_auth_login_callback(chat_id: int, callback_data: str) -> dict:
    """Handle the login callback."""
    return await handle_login_command(str(chat_id)) 