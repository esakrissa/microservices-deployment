import os
import logging
import httpx
from typing import Dict, Any, Optional, List, Union

logger = logging.getLogger(__name__)

# Get Telegram bot token from environment
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    logger.warning("TELEGRAM_BOT_TOKEN environment variable is not set")

TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

async def send_telegram_message(chat_id: str, message_data: Dict[str, Any]) -> bool:
    """Send a message to a Telegram chat."""
    try:
        # Prepare the message payload
        payload = {
            "chat_id": chat_id,
            "text": message_data.get("text", ""),
            "parse_mode": message_data.get("parse_mode", "Markdown")
        }
        
        # Add reply markup if provided
        if "reply_markup" in message_data:
            payload["reply_markup"] = message_data["reply_markup"]
        
        # Send the message
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{TELEGRAM_API_URL}/sendMessage",
                json=payload
            )
            
            response.raise_for_status()
            logger.info(f"Message sent to chat {chat_id}")
            return True
    except Exception as e:
        logger.error(f"Error sending message to Telegram: {str(e)}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"Response: {e.response.text}")
        return False

async def send_message(chat_id: str, text: str, parse_mode: str = "Markdown") -> bool:
    """Send a simple text message to a Telegram chat."""
    message_data = {
        "text": text,
        "parse_mode": parse_mode
    }
    return await send_telegram_message(chat_id, message_data)

async def send_message_with_inline_buttons(
    chat_id: str,
    text: str,
    buttons: List[List[Dict[str, str]]],
    parse_mode: str = "HTML"
) -> bool:
    """
    Send a message with inline buttons.
    
    Args:
        chat_id: The chat ID to send the message to
        text: The message text
        buttons: List of button rows, where each button is a dict with 'text' and 'callback_data'
        parse_mode: Message parse mode
    """
    message_data = {
        "text": text,
        "parse_mode": parse_mode,
        "reply_markup": {
            "inline_keyboard": buttons
        }
    }
    return await send_telegram_message(chat_id, message_data)

async def answer_callback_query(callback_query_id: str, text: str = None, show_alert: bool = False) -> bool:
    """Answer a callback query to stop the loading animation."""
    try:
        # Prepare the payload
        payload = {
            "callback_query_id": callback_query_id
        }
        if text:
            payload["text"] = text
            payload["show_alert"] = show_alert
        
        # Send the answer
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{TELEGRAM_API_URL}/answerCallbackQuery",
                json=payload
            )
            
            response.raise_for_status()
            logger.info(f"Answered callback query {callback_query_id}")
            return True
    except Exception as e:
        logger.error(f"Error answering callback query: {str(e)}")
        return False

async def send_typing_action(chat_id: str) -> bool:
    """Send a typing action to a chat."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{TELEGRAM_API_URL}/sendChatAction",
                json={
                    "chat_id": chat_id,
                    "action": "typing"
                }
            )
            
            response.raise_for_status()
            return True
    except Exception as e:
        logger.error(f"Error sending typing action: {str(e)}")
        return False 