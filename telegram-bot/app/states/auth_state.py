from enum import Enum, auto
from typing import Dict, Any, Optional
from datetime import datetime
import logging
import httpx
import json
from ..config import get_settings
from .session import (
    get_or_create_session,
    authenticate_session,
    end_session,
    is_authenticated,
    update_session_state,
    get_session_state,
    get_session_context
)
from ..utils.telegram import send_message

logger = logging.getLogger(__name__)
settings = get_settings()

class AuthState(Enum):
    INITIAL = auto()
    AWAITING_EMAIL = auto()
    AWAITING_USERNAME = auto()
    AWAITING_PASSWORD = auto()
    AWAITING_LOGIN_EMAIL = auto()
    AWAITING_LOGIN_PASSWORD = auto()
    
    def to_json(self):
        """Convert enum to JSON serializable format."""
        return self.name
    
    @classmethod
    def from_json(cls, name):
        """Convert JSON string back to enum."""
        if name is None:
            return None
        return cls[name]

# Add JSON encoder for AuthState
class AuthStateJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, AuthState):
            return obj.to_json()
        return super().default(obj)

# Store user state in memory (will be backed by Supabase)
user_states: Dict[str, Dict[str, Any]] = {}

async def start_registration(telegram_id: str) -> None:
    """Start the registration process for a user."""
    # Create or get session
    session = await get_or_create_session(telegram_id)
    
    # Update session state
    await update_session_state(
        telegram_id, 
        AuthState.AWAITING_EMAIL,
        {"registration_data": {}}
    )
    
    await send_message(
        telegram_id,
        "Please enter your email address to register:"
    )

async def start_login(telegram_id: str) -> None:
    """Start the login process for a user."""
    # Create or get session
    session = await get_or_create_session(telegram_id)
    
    # Update session state
    await update_session_state(
        telegram_id, 
        AuthState.AWAITING_LOGIN_EMAIL,
        {"login_data": {}}
    )
    
    await send_message(
        telegram_id,
        "Please enter your email address to login:"
    )

async def handle_auth_message(telegram_id: str, message: str) -> None:
    """Handle messages during authentication flow."""
    # Get session state
    state = await get_session_state(telegram_id)
    
    if not state:
        await send_message(
            telegram_id,
            "Please use /start to begin using the bot."
        )
        return

    if state == AuthState.AWAITING_EMAIL:
        await handle_registration_email(telegram_id, message)
    elif state == AuthState.AWAITING_USERNAME:
        await handle_registration_username(telegram_id, message)
    elif state == AuthState.AWAITING_PASSWORD:
        await handle_registration_password(telegram_id, message)
    elif state == AuthState.AWAITING_LOGIN_EMAIL:
        await handle_login_email(telegram_id, message)
    elif state == AuthState.AWAITING_LOGIN_PASSWORD:
        await handle_login_password(telegram_id, message)

async def handle_registration_email(telegram_id: str, email: str) -> None:
    """Handle email input during registration."""
    # Get session context
    context = await get_session_context(telegram_id)
    registration_data = context.get("registration_data", {})
    
    # Update registration data
    registration_data["email"] = email
    
    # Update session state
    await update_session_state(
        telegram_id, 
        AuthState.AWAITING_USERNAME,
        {"registration_data": registration_data}
    )
    
    await send_message(
        telegram_id,
        "Great! Now please enter your desired username:"
    )

async def handle_registration_username(telegram_id: str, username: str) -> None:
    """Handle username input during registration."""
    # Get session context
    context = await get_session_context(telegram_id)
    registration_data = context.get("registration_data", {})
    
    # Update registration data
    registration_data["username"] = username
    
    # Update session state
    await update_session_state(
        telegram_id, 
        AuthState.AWAITING_PASSWORD,
        {"registration_data": registration_data}
    )
    
    await send_message(
        telegram_id,
        "Perfect! Finally, please enter your password:"
    )

async def handle_registration_password(telegram_id: str, password: str) -> None:
    """Handle password input during registration."""
    # Get session context
    context = await get_session_context(telegram_id)
    registration_data = context.get("registration_data", {})
    
    # Update registration data
    registration_data["password"] = password
    registration_data["telegram_id"] = telegram_id

    try:
        # Register user with auth service
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{settings.AUTH_SERVICE_URL}/auth/register",
                json=registration_data
            )

            # Check if response is successful
            if response.status_code == 201:
                try:
                    # Parse response data
                    user_data = response.json()
                    user_id = user_data.get("id")
                    
                    # Get token for the new user
                    token_response = await client.post(
                        f"{settings.AUTH_SERVICE_URL}/auth/login/json",
                        json={
                            "email": registration_data["email"],
                            "password": registration_data["password"]
                        }
                    )
                    
                    if token_response.status_code == 200:
                        token_data = token_response.json()
                        token = token_data.get("access_token")
                        
                        # Authenticate session
                        success = await authenticate_session(telegram_id, user_id, token)
                        
                        if success:
                            logger.info(f"Successfully authenticated session for user {telegram_id}")
                        else:
                            logger.error(f"Failed to authenticate session for user {telegram_id}")
                    else:
                        logger.error(f"Failed to get token for new user: {token_response.text}")
                    
                    # Reset session state
                    await update_session_state(telegram_id, AuthState.INITIAL)
                    
                    # Send success message
                    await send_message(
                        telegram_id,
                        "Registration successful! You are now logged in."
                    )
                except Exception as e:
                    logger.error(f"Error processing successful registration response: {str(e)}")
                    await send_message(
                        telegram_id,
                        "Registration was successful, but there was an error logging you in. Please use /login to log in."
                    )
            else:
                # Registration failed
                try:
                    error_data = response.json()
                    error_message = error_data.get("detail", "Registration failed. Please try again.")
                except Exception as e:
                    logger.error(f"Error parsing error response: {str(e)}")
                    error_message = "Registration failed. Please try again."
                
                # Reset session state
                await update_session_state(telegram_id, None)
                
                await send_message(
                    telegram_id,
                    f"Error: {error_message}"
                )
    except Exception as e:
        logger.error(f"Error during registration: {str(e)}")
        
        # Reset session state
        await update_session_state(telegram_id, None)
        
        await send_message(
            telegram_id,
            "An error occurred during registration. Please try again later."
        )

async def handle_login_email(telegram_id: str, email: str) -> None:
    """Handle email input during login."""
    # Get session context
    context = await get_session_context(telegram_id)
    login_data = context.get("login_data", {})
    
    # Update login data
    login_data["email"] = email
    
    # Update session state
    await update_session_state(
        telegram_id, 
        AuthState.AWAITING_LOGIN_PASSWORD,
        {"login_data": login_data}
    )
    
    await send_message(
        telegram_id,
        "Please enter your password:"
    )

async def handle_login_password(telegram_id: str, password: str) -> None:
    """Handle password input during login."""
    # Get session context
    context = await get_session_context(telegram_id)
    login_data = context.get("login_data", {})
    
    # Update login data
    login_data["password"] = password
    
    try:
        # Login user with auth service
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{settings.AUTH_SERVICE_URL}/auth/login/json",
                json={
                    "email": login_data["email"],
                    "password": password
                }
            )
            
            # Check if response is successful
            if response.status_code == 200:
                try:
                    # Parse response data
                    token_data = response.json()
                    token = token_data.get("access_token")
                    
                    # Get user info
                    user_response = await client.get(
                        f"{settings.AUTH_SERVICE_URL}/users/me",
                        headers={"Authorization": f"Bearer {token}"}
                    )
                    
                    if user_response.status_code == 200:
                        user_data = user_response.json()
                        user_id = user_data.get("id")
                        
                        # Authenticate session
                        success = await authenticate_session(telegram_id, user_id, token)
                        
                        if success:
                            logger.info(f"Successfully authenticated session for user {telegram_id}")
                            
                            # Reset session state to trigger main menu
                            await update_session_state(telegram_id, AuthState.INITIAL)
                            
                            # Send success message
                            await send_message(
                                telegram_id,
                                "Login successful! You are now logged in."
                            )
                        else:
                            logger.error(f"Failed to authenticate session for user {telegram_id}")
                            await send_message(
                                telegram_id,
                                "Login was successful, but there was an error with your session. Please try again."
                            )
                    else:
                        logger.error(f"Failed to get user info: {user_response.text}")
                        await send_message(
                            telegram_id,
                            "Login was successful, but there was an error retrieving your user information. Please try again."
                        )
                except Exception as e:
                    logger.error(f"Error processing successful login response: {str(e)}")
                    await send_message(
                        telegram_id,
                        "Login was successful, but there was an error with your session. Please try again."
                    )
            else:
                # Login failed
                try:
                    error_data = response.json()
                    error_message = error_data.get("detail", "Incorrect email or password.")
                except Exception as e:
                    logger.error(f"Error parsing error response: {str(e)}")
                    error_message = "Login failed. Please try again."
                
                # Reset session state
                await update_session_state(telegram_id, None)
                
                await send_message(
                    telegram_id,
                    f"Error: {error_message}"
                )
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        
        # Reset session state
        await update_session_state(telegram_id, None)
        
        await send_message(
            telegram_id,
            "An error occurred during login. Please try again later."
        )

async def handle_logout(telegram_id: str) -> None:
    """Handle user logout."""
    # End session
    await end_session(telegram_id)
    
    await send_message(
        telegram_id,
        "You have been logged out successfully."
    )

async def check_auth(telegram_id: str) -> bool:
    """Check if a user is authenticated."""
    return await is_authenticated(telegram_id) 