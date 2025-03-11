import logging
from typing import Dict, Any
import httpx
from ..config import get_settings
from ..utils.telegram import send_message, send_message_with_inline_buttons
from ..states.auth_state import (
    start_registration,
    start_login,
    handle_auth_message,
    handle_logout,
    check_auth,
    AuthState
)
from ..states.session import (
    get_or_create_session,
    get_session_state,
    update_session_state,
    get_session,
    end_session
)

logger = logging.getLogger(__name__)
settings = get_settings()

async def handle_start_command(chat_id: str, message_data: dict) -> None:
    """Handle /start command."""
    logger.info(f"Handling start command for chat_id: {chat_id}")
    
    # Check if user is authenticated
    is_authenticated = await check_auth(chat_id)
    logger.info(f"User {chat_id} authentication status: {is_authenticated}")
    
    if is_authenticated:
        # User is authenticated, show main menu
        welcome_message = (
            "Welcome to the Bot! 👋\n\n"
            "What would you like to do today?"
        )
        
        buttons = [
            [
                {"text": "👤 Profile", "callback_data": "profile"},
                {"text": "📊 Dashboard", "callback_data": "dashboard"}
            ],
            [
                {"text": "⚙️ Settings", "callback_data": "settings"},
                {"text": "❓ Help", "callback_data": "help"}
            ],
            [
                {"text": "🔒 Logout", "callback_data": "logout"}
            ]
        ]
        
        await send_message_with_inline_buttons(chat_id, welcome_message, buttons)
    else:
        # User is not authenticated, show login/register options
        welcome_message = (
            "Welcome to the Bot! 👋\n\n"
            "Please login or register to continue."
        )
        
        buttons = [
            [
                {"text": "🔑 Login", "callback_data": "login"},
                {"text": "📝 Register", "callback_data": "register"}
            ],
            [
                {"text": "❓ Help", "callback_data": "help"}
            ]
        ]
        
        await send_message_with_inline_buttons(chat_id, welcome_message, buttons)

async def handle_register_command(chat_id: str, message_data: Dict[str, Any]) -> None:
    """Handle the /register command."""
    await start_registration(chat_id)

async def handle_login_command(chat_id: str, message_data: Dict[str, Any]) -> None:
    """Handle the /login command."""
    await start_login(chat_id)

async def handle_logout_command(chat_id: str, message_data: Dict[str, Any]) -> None:
    """Handle the /logout command."""
    # Check if user is authenticated
    is_authenticated = await check_auth(chat_id)
    
    if not is_authenticated:
        await send_message(chat_id, "You are not logged in.")
        await handle_start_command(chat_id, message_data)
        return
    
    try:
        # Get session data
        session_data = await get_session(chat_id)
        token = session_data.get("token")
        
        # Call auth service logout endpoint
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{settings.AUTH_SERVICE_URL}/auth/logout",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 200:
                logger.info(f"User {chat_id} logged out via auth service")
            else:
                logger.warning(f"Failed to call auth service logout: {response.status_code}")
    except Exception as e:
        logger.error(f"Error calling auth service logout: {str(e)}")
    
    # End the user's session locally
    await end_session(chat_id)
    
    # Send confirmation message
    await send_message(chat_id, "You have been logged out successfully.")
    
    # Show the start menu again
    await handle_start_command(chat_id, message_data)

async def handle_help_command(chat_id: str, message_data: Dict[str, Any]) -> None:
    """Handle the /help command."""
    help_text = (
        "🤖 <b>Bot Help</b>\n\n"
        "Here are the available commands:\n\n"
        "/start - Start the bot and show the main menu\n"
        "/login - Login to your account\n"
        "/register - Create a new account\n"
        "/profile - View your profile\n"
        "/dashboard - View your dashboard\n"
        "/settings - Adjust your settings\n"
        "/help - Show this help message\n"
        "/logout - Logout from your account\n\n"
        "If you need further assistance, please contact support."
    )
    
    await send_message(chat_id, help_text, parse_mode="HTML")

async def handle_message(chat_id: str, text: str, message_data: Dict[str, Any]) -> None:
    """Handle regular messages based on session state."""
    # Get current session state
    state = await get_session_state(chat_id)
    
    if state is None:
        # No active state, just acknowledge the message
        await send_message(chat_id, "I'm not sure what you want to do. Please use the menu or commands.")
        return
    
    # If state is INITIAL, show the start menu
    if state == AuthState.INITIAL:
        await handle_start_command(chat_id, message_data)
        return
    
    # Handle message based on state
    await handle_auth_message(chat_id, text)

async def handle_status_command(chat_id: str) -> Dict[str, Any]:
    """Handle the /status command by checking all services."""
    try:
        # Check API Gateway service
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.API_GATEWAY_URL}/health")
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
    """Handle the /menu command."""
    from ..callbacks.menu import handle_menu_main_callback
    return await handle_menu_main_callback(chat_id, "menu_main")

async def handle_settings_command(chat_id: str, message_data: Dict[str, Any]) -> None:
    """Handle the /settings command."""
    # Check if user is authenticated
    is_authenticated = await check_auth(chat_id)
    
    if not is_authenticated:
        await send_message(chat_id, "You need to be logged in to access settings.")
        await handle_start_command(chat_id, message_data)
        return
    
    # Display settings options
    settings_text = (
        "⚙️ <b>Settings</b>\n\n"
        "Here you can adjust your preferences and account settings.\n\n"
        "<i>Settings options coming soon!</i>"
    )
    
    # Add settings options and back button
    buttons = [
        [
            {"text": "🔔 Notifications", "callback_data": "settings_notifications"},
            {"text": "🔑 Change Password", "callback_data": "settings_password"}
        ],
        [{"text": "◀️ Back to Menu", "callback_data": "start"}]
    ]
    
    await send_message_with_inline_buttons(chat_id, settings_text, buttons, parse_mode="HTML")

async def handle_callback_query(chat_id: str, callback_data: str, message_data: Dict[str, Any]) -> None:
    """Handle callback queries from inline buttons."""
    # Ensure session exists
    await get_or_create_session(chat_id)
    
    if callback_data == "register":
        await handle_register_command(chat_id, message_data)
    elif callback_data == "login":
        await handle_login_command(chat_id, message_data)
    elif callback_data == "logout":
        await handle_logout_command(chat_id, message_data)
    elif callback_data == "help":
        await handle_help_command(chat_id, message_data)
    elif callback_data in ["profile", "dashboard", "settings"]:
        if await check_auth(chat_id):
            await send_message(
                chat_id,
                f"You selected: {callback_data.title()}\nThis feature is coming soon!"
            )
        else:
            await send_message(
                chat_id,
                "Please login first to access this feature."
            )

async def handle_profile_command(chat_id: str, message_data: Dict[str, Any]) -> None:
    """Handle the /profile command."""
    # Check if user is authenticated
    is_authenticated = await check_auth(chat_id)
    
    if not is_authenticated:
        await send_message(chat_id, "You need to be logged in to view your profile.")
        await handle_start_command(chat_id, message_data)
        return
    
    try:
        # Get session data
        session_data = await get_session(chat_id)
        token = session_data.get("token")
        
        # Get user profile from auth service
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{settings.AUTH_SERVICE_URL}/users/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 200:
                user_data = response.json()
                
                # Format profile information
                profile_text = (
                    "👤 <b>Your Profile</b>\n\n"
                    f"<b>Name:</b> {user_data.get('name', 'Not set')}\n"
                    f"<b>Email:</b> {user_data.get('email', 'Not set')}\n"
                    f"<b>Account created:</b> {user_data.get('created_at', 'Unknown')}\n"
                )
                
                # Add back button
                buttons = [
                    [{"text": "◀️ Back to Menu", "callback_data": "start"}]
                ]
                
                await send_message_with_inline_buttons(chat_id, profile_text, buttons, parse_mode="HTML")
            else:
                logger.error(f"Failed to get user profile: {response.text}")
                await send_message(chat_id, "Failed to retrieve your profile. Please try again later.")
    except Exception as e:
        logger.error(f"Error retrieving profile for user {chat_id}: {str(e)}")
        await send_message(chat_id, "An error occurred while retrieving your profile. Please try again later.")

async def handle_dashboard_command(chat_id: str, message_data: Dict[str, Any]) -> None:
    """Handle the /dashboard command."""
    # Check if user is authenticated
    is_authenticated = await check_auth(chat_id)
    
    if not is_authenticated:
        await send_message(chat_id, "You need to be logged in to view your dashboard.")
        await handle_start_command(chat_id, message_data)
        return
    
    # Display dashboard information
    dashboard_text = (
        "📊 <b>Your Dashboard</b>\n\n"
        "This is your personal dashboard. Here you can see your activity and statistics.\n\n"
        "<i>Dashboard features coming soon!</i>"
    )
    
    # Add back button
    buttons = [
        [{"text": "◀️ Back to Menu", "callback_data": "start"}]
    ]
    
    await send_message_with_inline_buttons(chat_id, dashboard_text, buttons, parse_mode="HTML")

async def handle_health_command(chat_id: str, message_data: Dict[str, Any]) -> None:
    """Handle the health command."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{settings.API_GATEWAY_URL}/health")
            
            if response.status_code == 200:
                await send_message(chat_id, "All systems operational! 🟢")
            else:
                await send_message(chat_id, f"API returned status code: {response.status_code} 🔴")
    except Exception as e:
        logger.error(f"Error checking health: {str(e)}")
        await send_message(chat_id, f"Error checking health: {str(e)} 🔴") 