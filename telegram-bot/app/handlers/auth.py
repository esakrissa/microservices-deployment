import logging
import re
import httpx
from typing import Dict, Any
from ..config import get_settings
from ..states.user_state import set_user_state, get_user_state, set_user_data, get_user_data, clear_user_state

logger = logging.getLogger(__name__)
settings = get_settings()

async def handle_register_command(chat_id: str) -> Dict[str, Any]:
    """Handle the /register command."""
    # Initialize user state for registration
    set_user_state(chat_id, "REGISTER_EMAIL")
    
    message = (
        "📝 *Registration*\n\n"
        "Let's create your account.\n\n"
        "Please enter your email address:"
    )
    
    return {
        "text": message,
        "parse_mode": "Markdown"
    }

async def handle_login_command(chat_id: str) -> Dict[str, Any]:
    """Handle the /login command."""
    # Initialize user state for login
    set_user_state(chat_id, "LOGIN_EMAIL")
    
    message = (
        "🔐 *Login*\n\n"
        "Please enter your email address:"
    )
    
    return {
        "text": message,
        "parse_mode": "Markdown"
    }

async def handle_register_email_state(chat_id: str, message_text: str) -> Dict[str, Any]:
    """Handle the REGISTER_EMAIL state."""
    # Validate email
    if not re.match(r"[^@]+@[^@]+\.[^@]+", message_text):
        return {
            "text": "❌ Invalid email format. Please enter a valid email address:",
            "parse_mode": "Markdown"
        }
    
    # Store email and move to next state
    set_user_data(chat_id, "email", message_text)
    set_user_state(chat_id, "REGISTER_USERNAME")
    
    return {
        "text": "Great! Now please enter your desired username:",
        "parse_mode": "Markdown"
    }

async def handle_register_username_state(chat_id: str, message_text: str) -> Dict[str, Any]:
    """Handle the REGISTER_USERNAME state."""
    # Validate username
    if len(message_text) < 3:
        return {
            "text": "❌ Username must be at least 3 characters long. Please try again:",
            "parse_mode": "Markdown"
        }
    
    # Store username and move to next state
    set_user_data(chat_id, "username", message_text)
    set_user_state(chat_id, "REGISTER_PASSWORD")
    
    return {
        "text": "Now please enter your password (at least 8 characters):",
        "parse_mode": "Markdown"
    }

async def handle_register_password_state(chat_id: str, message_text: str) -> Dict[str, Any]:
    """Handle the REGISTER_PASSWORD state."""
    # Validate password
    if len(message_text) < 8:
        return {
            "text": "❌ Password must be at least 8 characters long. Please try again:",
            "parse_mode": "Markdown"
        }
    
    # Store password and complete registration
    set_user_data(chat_id, "password", message_text)
    clear_user_state(chat_id)
    
    # Register user with auth service
    try:
        email = get_user_data(chat_id, "email")
        username = get_user_data(chat_id, "username")
        password = get_user_data(chat_id, "password")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{settings.AUTH_SERVICE_URL}/auth/register",
                json={
                    "email": email,
                    "username": username,
                    "password": password,
                    "role": "user"
                }
            )
            
            if response.status_code == 201:
                # Registration successful
                return {
                    "text": "✅ *Registration successful!*\n\nYou can now use the bot with your account.",
                    "parse_mode": "Markdown"
                }
            else:
                # Registration failed
                error_detail = response.json().get("detail", "Unknown error")
                return {
                    "text": f"❌ *Registration failed*\n\nError: {error_detail}",
                    "parse_mode": "Markdown"
                }
    except Exception as e:
        logger.error(f"Error during registration: {str(e)}")
        return {
            "text": "❌ *Registration failed*\n\nThere was an error connecting to the auth service. Please try again later.",
            "parse_mode": "Markdown"
        }

async def handle_login_email_state(chat_id: str, message_text: str) -> Dict[str, Any]:
    """Handle the LOGIN_EMAIL state."""
    # Validate email
    if not re.match(r"[^@]+@[^@]+\.[^@]+", message_text):
        return {
            "text": "❌ Invalid email format. Please enter a valid email address:",
            "parse_mode": "Markdown"
        }
    
    # Store email and move to next state
    set_user_data(chat_id, "email", message_text)
    set_user_state(chat_id, "LOGIN_PASSWORD")
    
    return {
        "text": "Now please enter your password:",
        "parse_mode": "Markdown"
    }

async def handle_login_password_state(chat_id: str, message_text: str) -> Dict[str, Any]:
    """Handle the LOGIN_PASSWORD state."""
    # Store password and attempt login
    set_user_data(chat_id, "password", message_text)
    clear_user_state(chat_id)
    
    # Login with auth service
    try:
        email = get_user_data(chat_id, "email")
        password = get_user_data(chat_id, "password")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            # First, try to login
            response = await client.post(
                f"{settings.AUTH_SERVICE_URL}/auth/login",
                data={
                    "username": email,
                    "password": password
                }
            )
            
            if response.status_code == 200:
                # Login successful, now link Telegram ID if not already linked
                token_data = response.json()
                
                # Link Telegram ID
                link_response = await client.post(
                    f"{settings.AUTH_SERVICE_URL}/auth/link-telegram",
                    headers={"Authorization": f"Bearer {token_data['access_token']}"},
                    json={"telegram_id": chat_id}
                )
                
                if link_response.status_code in [200, 201]:
                    return {
                        "text": "✅ *Login successful!*\n\nYour Telegram account has been linked to your user account.",
                        "parse_mode": "Markdown"
                    }
                else:
                    return {
                        "text": "✅ *Login successful!*\n\nBut there was an issue linking your Telegram account.",
                        "parse_mode": "Markdown"
                    }
            else:
                # Login failed
                return {
                    "text": "❌ *Login failed*\n\nIncorrect email or password. Please try again.",
                    "parse_mode": "Markdown"
                }
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        return {
            "text": "❌ *Login failed*\n\nThere was an error connecting to the auth service. Please try again later.",
            "parse_mode": "Markdown"
        } 