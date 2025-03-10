import os
import logging
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
import httpx
from typing import Optional, Dict, Any, List, Union
import json
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set")

# FastAPI service URL
FASTAPI_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")

app = FastAPI(title="Telegram Bot Service")

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

# Command handlers
async def handle_start_command(chat_id: str) -> Dict[str, Any]:
    """Handle the /start command"""
    message = (
        "👋 *Welcome to the Travel Bot!*\n\n"
        "I'm here to help you plan your next adventure.\n\n"
        "Use the buttons below to explore options or check your settings."
    )
    
    # Create inline keyboard with Menu and Settings buttons
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "🗺️ Travel Menu", "callback_data": "menu_main"},
                {"text": "⚙️ Settings", "callback_data": "settings_main"}
            ]
        ]
    }
    
    return {
        "text": message,
        "parse_mode": "Markdown",
        "reply_markup": keyboard
    }

async def handle_help_command(chat_id: str) -> Dict[str, Any]:
    """Handle the /help command"""
    message = (
        "🔍 *Help Information*\n\n"
        "This bot helps you explore travel options and manage your preferences.\n\n"
        "Available commands:\n"
        "• /start - Show the main menu\n"
        "• /help - Show this help information\n"
        "• /status - Check the system status\n"
        "• /menu - Show the travel menu\n"
        "• /settings - Show your settings\n\n"
        "You can also use the inline buttons for navigation."
    )
    
    return {
        "text": message,
        "parse_mode": "Markdown"
    }

async def handle_status_command(chat_id: str) -> Dict[str, Any]:
    """Handle the /status command by checking all services"""
    try:
        # Check FastAPI service
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{FASTAPI_URL}/health")
            if response.status_code == 200:
                message = "✅ *All systems operational*\n\nThe bot is functioning normally and all services are available."
            else:
                message = "⚠️ *Partial system outage*\n\nSome services may be unavailable. Please try again later."
    except Exception as e:
        logger.error(f"Error checking status: {str(e)}")
        message = "❌ *System outage*\n\nThe system is currently experiencing issues. Please try again later."
    
    return {
        "text": message,
        "parse_mode": "Markdown"
    }

async def handle_menu_command(chat_id: str) -> Dict[str, Any]:
    """Handle the /menu command"""
    try:
        # Fetch menu data from FastAPI
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{FASTAPI_URL}/api/travel/menu")
            
            if response.status_code == 200:
                menu_data = response.json()
                
                # Format the menu message
                message = "🗺️ *Travel Menu*\n\n"
                
                # Add menu items with inline buttons
                keyboard = {"inline_keyboard": []}
                
                for category in menu_data.get("categories", []):
                    message += f"*{category['name']}*\n"
                    
                    # Add category items to message
                    for item in category.get("items", []):
                        message += f"• {item['name']}: {item['description']}\n"
                    
                    message += "\n"
                    
                    # Add category button
                    keyboard["inline_keyboard"].append([
                        {"text": f"Browse {category['name']}", "callback_data": f"menu_category_{category['id']}"}
                    ])
                
                # Add back button
                keyboard["inline_keyboard"].append([
                    {"text": "🔙 Back to Main Menu", "callback_data": "back_to_main"}
                ])
                
                return {
                    "text": message,
                    "parse_mode": "Markdown",
                    "reply_markup": keyboard
                }
            else:
                return {
                    "text": "Sorry, I couldn't fetch the menu. Please try again later.",
                    "parse_mode": "Markdown"
                }
    except Exception as e:
        logger.error(f"Error fetching menu: {str(e)}")
        return {
            "text": "Sorry, there was an error fetching the menu. Please try again later.",
            "parse_mode": "Markdown"
        }

async def handle_settings_command(chat_id: str) -> Dict[str, Any]:
    """Handle the /settings command"""
    try:
        # Fetch settings data from FastAPI
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{FASTAPI_URL}/api/users/{chat_id}/settings")
            
            if response.status_code == 200:
                settings_data = response.json()
                
                # Format the settings message
                message = "⚙️ *Your Settings*\n\n"
                
                # Add settings items
                for key, value in settings_data.get("settings", {}).items():
                    message += f"*{key}*: {value}\n"
                
                # Create inline keyboard for settings options
                keyboard = {
                    "inline_keyboard": [
                        [
                            {"text": "🌍 Language", "callback_data": "settings_language"},
                            {"text": "🔔 Notifications", "callback_data": "settings_notifications"}
                        ],
                        [
                            {"text": "💰 Currency", "callback_data": "settings_currency"},
                            {"text": "🕒 Time Format", "callback_data": "settings_time_format"}
                        ],
                        [
                            {"text": "🔙 Back to Main Menu", "callback_data": "back_to_main"}
                        ]
                    ]
                }
                
                return {
                    "text": message,
                    "parse_mode": "Markdown",
                    "reply_markup": keyboard
                }
            else:
                return {
                    "text": "Sorry, I couldn't fetch your settings. Please try again later.",
                    "parse_mode": "Markdown"
                }
    except Exception as e:
        logger.error(f"Error fetching settings: {str(e)}")
        return {
            "text": "Sorry, there was an error fetching your settings. Please try again later.",
            "parse_mode": "Markdown"
        }

# Command mapping
COMMAND_HANDLERS = {
    "/start": handle_start_command,
    "/help": handle_help_command,
    "/status": handle_status_command,
    "/menu": handle_menu_command,
    "/settings": handle_settings_command,
}

# Callback query handlers
async def handle_menu_callback(chat_id: str, callback_data: str) -> Dict[str, Any]:
    """Handle menu-related callback queries"""
    try:
        # Extract callback parts
        parts = callback_data.split('_')
        
        # Handle main menu request
        if len(parts) >= 2 and parts[1] == "main":
            return await handle_menu_command(chat_id)
            
        # Handle category selection
        # Format: menu_category_{category_id}
        if len(parts) < 3:
            return {"text": "Invalid menu selection. Please try again."}
        
        category_id = parts[2]
        
        # Fetch category details from FastAPI
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{FASTAPI_URL}/api/travel/categories/{category_id}")
            
            if response.status_code == 200:
                category_data = response.json()
                
                # Format the category message
                message = f"🗺️ *{category_data.get('name', 'Category')}*\n\n"
                message += f"{category_data.get('description', '')}\n\n"
                
                # Add items
                for item in category_data.get("items", []):
                    message += f"*{item['name']}*\n"
                    message += f"{item['description']}\n"
                    if 'price' in item:
                        message += f"Price: {item['price']}\n"
                    message += "\n"
                
                # Create inline keyboard for navigation
                keyboard = {
                    "inline_keyboard": [
                        [
                            {"text": "🔙 Back to Menu", "callback_data": "menu_main"}
                        ]
                    ]
                }
                
                return {
                    "text": message,
                    "parse_mode": "Markdown",
                    "reply_markup": keyboard
                }
            else:
                return {
                    "text": "Sorry, I couldn't fetch the category details. Please try again later.",
                    "parse_mode": "Markdown"
                }
    except Exception as e:
        logger.error(f"Error fetching category: {str(e)}")
        return {
            "text": "Sorry, there was an error fetching the category details. Please try again later.",
            "parse_mode": "Markdown"
        }

async def handle_settings_callback(chat_id: str, callback_data: str) -> Dict[str, Any]:
    """Handle settings-related callbacks"""
    setting_type = callback_data.split('_')[1] if len(callback_data.split('_')) > 1 else None
    
    if setting_type == "language":
        message = "*🌍 Language Settings*\n\nSelect your preferred language:"
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "English 🇬🇧", "callback_data": "set_language_en"},
                    {"text": "Español 🇪🇸", "callback_data": "set_language_es"}
                ],
                [
                    {"text": "Français 🇫🇷", "callback_data": "set_language_fr"},
                    {"text": "Deutsch 🇩🇪", "callback_data": "set_language_de"}
                ],
                [
                    {"text": "🔙 Back to Settings", "callback_data": "settings_main"}
                ]
            ]
        }
    elif setting_type == "notifications":
        message = "*🔔 Notification Settings*\n\nChoose which notifications you want to receive:"
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "Deals & Offers ✅", "callback_data": "toggle_notif_deals"}
                ],
                [
                    {"text": "Travel Updates ✅", "callback_data": "toggle_notif_updates"}
                ],
                [
                    {"text": "Tips & Recommendations ✅", "callback_data": "toggle_notif_tips"}
                ],
                [
                    {"text": "🔙 Back to Settings", "callback_data": "settings_main"}
                ]
            ]
        }
    elif setting_type == "currency":
        message = "*💰 Currency Settings*\n\nSelect your preferred currency:"
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "USD 🇺🇸", "callback_data": "set_currency_usd"},
                    {"text": "EUR 🇪🇺", "callback_data": "set_currency_eur"}
                ],
                [
                    {"text": "GBP 🇬🇧", "callback_data": "set_currency_gbp"},
                    {"text": "JPY 🇯🇵", "callback_data": "set_currency_jpy"}
                ],
                [
                    {"text": "🔙 Back to Settings", "callback_data": "settings_main"}
                ]
            ]
        }
    elif setting_type == "time_format":
        message = "*🕒 Time Format Settings*\n\nSelect your preferred time format:"
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "12-hour (AM/PM)", "callback_data": "set_time_12h"}
                ],
                [
                    {"text": "24-hour", "callback_data": "set_time_24h"}
                ],
                [
                    {"text": "🔙 Back to Settings", "callback_data": "settings_main"}
                ]
            ]
        }
    else:
        # Default to main settings
        return await handle_settings_command(chat_id)
    
    return {
        "text": message,
        "parse_mode": "Markdown",
        "reply_markup": keyboard
    }

# Callback query mapping
CALLBACK_HANDLERS = {
    "menu": handle_menu_callback,
    "settings": handle_settings_callback,
}

async def send_typing_action(chat_id: str):
    """Send typing action to Telegram"""
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendChatAction",
                json={"chat_id": chat_id, "action": "typing"}
            )
    except Exception as e:
        logger.error(f"Error sending typing action: {str(e)}")

@app.post("/webhook")
async def telegram_webhook(update: TelegramUpdate):
    try:
        # Handle callback queries (button clicks)
        if update.callback_query:
            callback_query = update.callback_query
            callback_data = callback_query.get("data", "")
            chat_id = str(callback_query.get("message", {}).get("chat", {}).get("id", ""))
            
            logger.info(f"Received callback query from {chat_id}: {callback_data}")
            
            # Send typing indicator
            asyncio.create_task(send_typing_action(chat_id))
            
            # Acknowledge the callback query
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/answerCallbackQuery",
                    json={"callback_query_id": callback_query.get("id", "")}
                )
            
            # Handle different callback types
            if callback_data == "back_to_main":
                # Return to main menu
                response_data = await handle_start_command(chat_id)
            else:
                # Extract the callback type (menu, settings, etc.)
                callback_type = callback_data.split('_')[0] if '_' in callback_data else ""
                
                if callback_type in CALLBACK_HANDLERS:
                    response_data = await CALLBACK_HANDLERS[callback_type](chat_id, callback_data)
                else:
                    response_data = {
                        "text": "Sorry, I don't know how to handle this action.",
                        "parse_mode": "Markdown"
                    }
            
            # Edit the original message with the new content
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/editMessageText",
                    json={
                        "chat_id": chat_id,
                        "message_id": callback_query.get("message", {}).get("message_id", ""),
                        "text": response_data.get("text", ""),
                        "parse_mode": response_data.get("parse_mode", ""),
                        "reply_markup": response_data.get("reply_markup", {})
                    }
                )
            
            return {"status": "success", "callback_handled": True}
        
        # Handle regular messages
        if not update.message or "text" not in update.message:
            return {"status": "no message text"}
        
        chat_id = str(update.message.get("chat", {}).get("id"))
        message_text = update.message.get("text", "")
        
        logger.info(f"Received message from {chat_id}: {message_text}")
        
        # Send typing indicator
        asyncio.create_task(send_typing_action(chat_id))
        
        # Check if this is a command
        if message_text.startswith('/'):
            command = message_text.split()[0]  # Get the command part
            if command in COMMAND_HANDLERS:
                response_data = await COMMAND_HANDLERS[command](chat_id)
                
                # Send response directly for commands
                async with httpx.AsyncClient() as client:
                    await client.post(
                        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                        json={
                            "chat_id": chat_id,
                            "text": response_data.get("text", ""),
                            "parse_mode": response_data.get("parse_mode", ""),
                            "reply_markup": response_data.get("reply_markup", {})
                        }
                    )
                return {"status": "success", "command": command}
        
        # For regular messages, send to FastAPI for processing
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{FASTAPI_URL}/process",
                json={"content": message_text, "user_id": chat_id}
            )
            
            if response.status_code != 200:
                logger.error(f"Error from FastAPI: {response.text}")
                
                # Send error message to user
                error_message = "Sorry, I couldn't process your message. Please try again later."
                await send_message(MessageToSend(user_id=chat_id, content=error_message))
                
                return {"status": "error", "detail": "Failed to process message"}
        
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        
        # Try to send error message to user if possible
        try:
            if chat_id:
                error_message = "Sorry, an error occurred. Please try again later."
                await send_message(MessageToSend(user_id=chat_id, content=error_message))
        except:
            pass
            
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/send")
async def send_message(message: MessageToSend):
    try:
        # Send message to Telegram
        async with httpx.AsyncClient() as client:
            telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            
            # Prepare request data
            request_data = {
                "chat_id": message.user_id,
                "text": message.content
            }
            
            # Add parse_mode if provided
            if message.parse_mode:
                request_data["parse_mode"] = message.parse_mode
            
            # Add reply_markup if provided
            if message.reply_markup:
                request_data["reply_markup"] = message.reply_markup
            
            response = await client.post(
                telegram_url,
                json=request_data
            )
            
            if response.status_code != 200:
                logger.error(f"Error sending message to Telegram: {response.text}")
                raise HTTPException(status_code=500, detail="Failed to send message to Telegram")
            
            logger.info(f"Successfully sent message to user {message.user_id}")
        
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# For local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)