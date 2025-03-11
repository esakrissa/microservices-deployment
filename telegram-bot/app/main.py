import logging
from typing import Dict, Any
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
    logger.info(f"Received user registered event: {message}")
    # If telegram_id is in the message, send welcome message
    if "telegram_id" in message:
        await send_message(
            message["telegram_id"],
            f"Welcome to the service! Your account has been registered successfully."
        )

async def handle_user_login(message: Dict[str, Any]):
    """Handle user login event."""
    logger.info(f"Received user login event: {message}")
    # If telegram_id is in the message, send login notification
    if "telegram_id" in message:
        await send_message(
            message["telegram_id"],
            f"New login detected for your account."
        )

async def handle_user_logout(message: Dict[str, Any]):
    """Handle user logout event."""
    logger.info(f"Received user logout event: {message}")
    # If telegram_id is in the message, update session
    if "telegram_id" in message:
        await end_session(message["telegram_id"])
        await send_message(
            message["telegram_id"],
            f"You have been logged out from all sessions."
        )

async def handle_user_updated(message: Dict[str, Any]):
    """Handle user updated event."""
    logger.info(f"Received user updated event: {message}")
    # If telegram_id is in the message, send update notification
    if "telegram_id" in message:
        await send_message(
            message["telegram_id"],
            f"Your account information has been updated."
        )

async def handle_telegram_linked(message: Dict[str, Any]):
    """Handle telegram linked event."""
    logger.info(f"Received telegram linked event: {message}")
    # Send confirmation message
    if "telegram_id" in message:
        await send_message(
            message["telegram_id"],
            f"Your Telegram account has been linked successfully."
        )

# For local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)