import logging
from typing import Dict, Any, Optional
from fastapi import FastAPI, Request
from .handlers.general import (
    handle_start_command,
    handle_help_command,
    handle_register_command,
    handle_login_command,
    handle_logout_command,
    handle_message,
    handle_callback_query,
    handle_profile_command,
    handle_dashboard_command,
    handle_settings_command
)
from .utils.telegram import answer_callback_query, send_message
from .utils.message_broker import MessageBrokerClient
from .states.session import end_session
import httpx
from .config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(title="Telegram Bot Service")

# Initialize message broker client
message_broker = MessageBrokerClient()

# Command handlers
COMMAND_HANDLERS = {
    "/start": handle_start_command,
    "/login": handle_login_command,
    "/register": handle_register_command,
    "/logout": handle_logout_command,
    "/help": handle_help_command,
    "/profile": handle_profile_command,
    "/dashboard": handle_dashboard_command,
    "/settings": handle_settings_command
}

@app.post("/webhook")
async def telegram_webhook(request: Request):
    """Handle Telegram webhook requests."""
    try:
        update = await request.json()
        logger.debug(f"Received update: {update}")
        
        # Handle callback query
        if "callback_query" in update:
            callback_query = update["callback_query"]
            chat_id = str(callback_query["message"]["chat"]["id"])
            callback_data = callback_query["data"]
            message_data = callback_query["message"]
            
            logger.info(f"Received callback query from {chat_id}: {callback_data}")
            
            # Handle callback data
            if callback_data == "login":
                await handle_login_command(chat_id, message_data)
            elif callback_data == "register":
                await handle_register_command(chat_id, message_data)
            elif callback_data == "profile":
                await handle_profile_command(chat_id, message_data)
            elif callback_data == "dashboard":
                await handle_dashboard_command(chat_id, message_data)
            elif callback_data == "settings":
                await handle_settings_command(chat_id, message_data)
            elif callback_data == "help":
                await handle_help_command(chat_id, message_data)
            elif callback_data == "logout":
                await handle_logout_command(chat_id, message_data)
            elif callback_data == "start":
                await handle_start_command(chat_id, message_data)
            else:
                logger.warning(f"Unknown callback data: {callback_data}")
                await send_message(chat_id, "Sorry, I don't understand that command.")
            
            # Answer callback query to stop loading animation
            await answer_callback_query(callback_query["id"])
            
            return {"status": "ok"}
        
        # Handle message
        if "message" in update:
            message = update["message"]
            
            # Check if message contains text
            if "text" not in message:
                return {"status": "ok"}
            
            chat_id = str(message["chat"]["id"])
            text = message["text"]
            message_data = message
            
            logger.info(f"Received message from {chat_id}: {text}")
            
            # Check if message is a command
            if text.startswith("/"):
                command = text.split("@")[0].lower()  # Remove bot username if present
                
                if command in COMMAND_HANDLERS:
                    await COMMAND_HANDLERS[command](chat_id, message_data)
                else:
                    await send_message(chat_id, "Sorry, I don't understand that command.")
            else:
                # Handle regular message based on session state
                await handle_message(chat_id, text, message_data)
            
            return {"status": "ok"}
        
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error handling webhook: {str(e)}")
        return {"status": "error", "message": str(e)}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    # Initialize message broker
    try:
        if message_broker.initialize():
            # Subscribe to relevant topics
            message_broker.subscribe("auth.user.registered", handle_user_registered)
            message_broker.subscribe("auth.user.login", handle_user_login)
            message_broker.subscribe("auth.user.logout", handle_user_logout)
            message_broker.subscribe("auth.user.updated", handle_user_updated)
            message_broker.subscribe("auth.telegram.linked", handle_telegram_linked)
            
            # Start listening for messages
            app.state.streaming_pull_future = message_broker.start_listening()
            logger.info("Message broker initialized and subscribed to topics")
        else:
            logger.warning("Message broker not available - bot will run with limited functionality")
    except Exception as e:
        logger.warning(f"Failed to initialize message broker: {str(e)} - bot will run with limited functionality")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    # Stop message broker
    try:
        if hasattr(app.state, "streaming_pull_future") and message_broker.is_available:
            message_broker.stop_listening(app.state.streaming_pull_future)
        if message_broker.is_available:
            message_broker.close()
            logger.info("Message broker stopped")
    except Exception as e:
        logger.warning(f"Error during shutdown of message broker: {str(e)}")

# Message broker event handlers
async def handle_user_registered(message: Dict[str, Any]):
    """Handle user registered event."""
    try:
        logger.info(f"Received user registered event with ID: {message.get('id', 'unknown')}")
        
        # Extract payload from standardized message format
        payload = message.get("payload", message)
        
        # Get user information
        user_id = payload.get("user_id")
        username = payload.get("username")
        email = payload.get("email")
        
        # Get telegram_id from database if available
        telegram_id = await get_telegram_id_for_user(user_id)
        
        if telegram_id:
            # Send welcome message
            await send_message(
                telegram_id,
                f"Welcome to the service, {username}! Your account has been registered successfully."
            )
            logger.info(f"Sent welcome message to user {username} (Telegram ID: {telegram_id})")
        else:
            logger.info(f"No Telegram ID found for user {user_id}, skipping welcome message")
    except Exception as e:
        logger.error(f"Error handling user registered event: {str(e)}")

async def handle_user_login(message: Dict[str, Any]):
    """Handle user login event."""
    try:
        logger.info(f"Received user login event with ID: {message.get('id', 'unknown')}")
        
        # Extract payload from standardized message format
        payload = message.get("payload", message)
        
        # Get user information
        user_id = payload.get("user_id")
        timestamp = payload.get("timestamp", "unknown time")
        
        # Get telegram_id from database if available
        telegram_id = await get_telegram_id_for_user(user_id)
        
        if telegram_id:
            # Send login notification
            await send_message(
                telegram_id,
                f"New login detected for your account at {timestamp}."
            )
            logger.info(f"Sent login notification to user with Telegram ID: {telegram_id}")
        else:
            logger.info(f"No Telegram ID found for user {user_id}, skipping login notification")
    except Exception as e:
        logger.error(f"Error handling user login event: {str(e)}")

async def handle_user_logout(message: Dict[str, Any]):
    """Handle user logout event."""
    try:
        logger.info(f"Received user logout event with ID: {message.get('id', 'unknown')}")
        
        # Extract payload from standardized message format
        payload = message.get("payload", message)
        
        # Get user information
        user_id = payload.get("user_id")
        
        # Get telegram_id from database if available
        telegram_id = await get_telegram_id_for_user(user_id)
        
        if telegram_id:
            # End session and notify user
            await end_session(telegram_id)
            await send_message(
                telegram_id,
                "You have been logged out from all sessions."
            )
            logger.info(f"Ended session and sent logout notification to user with Telegram ID: {telegram_id}")
        else:
            logger.info(f"No Telegram ID found for user {user_id}, skipping logout notification")
    except Exception as e:
        logger.error(f"Error handling user logout event: {str(e)}")

async def handle_user_updated(message: Dict[str, Any]):
    """Handle user updated event."""
    try:
        logger.info(f"Received user updated event with ID: {message.get('id', 'unknown')}")
        
        # Extract payload from standardized message format
        payload = message.get("payload", message)
        
        # Get user information
        user_id = payload.get("user_id")
        
        # Get telegram_id from database if available
        telegram_id = await get_telegram_id_for_user(user_id)
        
        if telegram_id:
            # Notify user about profile update
            await send_message(
                telegram_id,
                "Your profile has been updated."
            )
            logger.info(f"Sent profile update notification to user with Telegram ID: {telegram_id}")
        else:
            logger.info(f"No Telegram ID found for user {user_id}, skipping profile update notification")
    except Exception as e:
        logger.error(f"Error handling user updated event: {str(e)}")

async def handle_telegram_linked(message: Dict[str, Any]):
    """Handle telegram linked event."""
    try:
        logger.info(f"Received telegram linked event with ID: {message.get('id', 'unknown')}")
        
        # Extract payload from standardized message format
        payload = message.get("payload", message)
        
        # Get telegram_id
        telegram_id = payload.get("telegram_id")
        
        if telegram_id:
            # Send welcome message
            await send_message(
                telegram_id,
                "Your Telegram account has been successfully linked to your user account!"
            )
            logger.info(f"Sent telegram linked notification to user with Telegram ID: {telegram_id}")
        else:
            logger.warning(f"No Telegram ID found in telegram linked event")
    except Exception as e:
        logger.error(f"Error handling telegram linked event: {str(e)}")

async def get_telegram_id_for_user(user_id: str) -> Optional[str]:
    """Get Telegram ID for a user from the database."""
    if not user_id:
        return None
        
    try:
        # Check if we have a direct mapping in the session
        # This is a placeholder - in a real implementation, you would query your database
        # or make an API call to the auth service to get the telegram_id for a user_id
        
        # For now, we'll make a call to the auth service
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{settings.AUTH_SERVICE_URL}/users/{user_id}/telegram",
                headers={"X-API-Key": settings.API_KEY}
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("telegram_id")
            else:
                logger.warning(f"Failed to get Telegram ID for user {user_id}: {response.status_code}")
                return None
    except Exception as e:
        logger.error(f"Error getting Telegram ID for user {user_id}: {str(e)}")
        return None

# For local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)