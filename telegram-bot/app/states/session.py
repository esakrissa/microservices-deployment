import logging
import time
import httpx
import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from ..config import get_settings
from ..utils.supabase import store_session, get_session_from_supabase, delete_session_from_supabase

logger = logging.getLogger(__name__)
settings = get_settings()

# In-memory session storage (fallback if Supabase is not available)
# In a production environment, this would be backed by Redis or another distributed cache
bot_sessions: Dict[str, Dict[str, Any]] = {}

# Session timeout in seconds (30 minutes)
SESSION_TIMEOUT = 30 * 60

class BotSession:
    """Bot session class for managing user state in the bot."""
    
    def __init__(self, telegram_id: str, user_id: Optional[str] = None, auth_token: Optional[str] = None):
        self.telegram_id = telegram_id
        self.user_id = user_id
        self.auth_token = auth_token
        self.is_authenticated = auth_token is not None
        self.created_at = time.time()
        self.last_activity = time.time()
        self.state = None
        self.context = {}  # For storing conversation context
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary."""
        # Convert state to string if it's an Enum
        state = self.state
        if hasattr(state, 'to_json'):  # Check if it has to_json method
            state = state.to_json()
        elif hasattr(state, 'name'):  # Check if it's an Enum
            state = state.name
        
        # Process context to ensure it's JSON serializable
        processed_context = {}
        for key, value in self.context.items():
            if hasattr(value, 'to_json'):
                processed_context[key] = value.to_json()
            elif hasattr(value, 'name') and hasattr(value, '__class__') and value.__class__.__name__ == 'Enum':
                processed_context[key] = value.name
            elif isinstance(value, dict):
                # Process nested dictionaries
                processed_value = {}
                for k, v in value.items():
                    if hasattr(v, 'to_json'):
                        processed_value[k] = v.to_json()
                    elif hasattr(v, 'name') and hasattr(v, '__class__') and v.__class__.__name__ == 'Enum':
                        processed_value[k] = v.name
                    else:
                        processed_value[k] = v
                processed_context[key] = processed_value
            else:
                processed_context[key] = value
        
        return {
            "telegram_id": self.telegram_id,
            "user_id": self.user_id,
            "auth_token": self.auth_token,
            "is_authenticated": self.is_authenticated,
            "created_at": self.created_at,
            "last_activity": self.last_activity,
            "state": state,
            "context": processed_context
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BotSession':
        """Create session from dictionary."""
        session = cls(
            telegram_id=data["telegram_id"],
            user_id=data.get("user_id"),
            auth_token=data.get("auth_token")
        )
        session.is_authenticated = data.get("is_authenticated", False)
        session.created_at = data.get("created_at", time.time())
        session.last_activity = data.get("last_activity", time.time())
        
        # Handle state conversion
        state = data.get("state")
        if state and isinstance(state, str):
            # Try to convert string back to Enum if it's from AuthState
            try:
                from ..states.auth_state import AuthState
                session.state = AuthState.from_json(state)
            except (ImportError, AttributeError, KeyError):
                session.state = state
        else:
            session.state = state
        
        session.context = data.get("context", {})
        return session
    
    def update_activity(self) -> None:
        """Update last activity time."""
        self.last_activity = time.time()
    
    def is_expired(self) -> bool:
        """Check if session is expired."""
        elapsed = time.time() - self.last_activity
        return elapsed > SESSION_TIMEOUT

async def get_or_create_session(telegram_id: str) -> BotSession:
    """Get or create a bot session for a user."""
    # Try to get session from Supabase first
    supabase_session = await get_session_from_supabase(telegram_id)
    
    if supabase_session:
        logger.info(f"Retrieved session from Supabase for Telegram ID {telegram_id}")
        session = BotSession.from_dict(supabase_session)
        if session.is_expired():
            # Session expired, create a new one
            session = BotSession(telegram_id)
            # Store in Supabase
            await store_session(telegram_id, session.to_dict())
        else:
            # Update activity
            session.update_activity()
            # Update in Supabase
            await store_session(telegram_id, session.to_dict())
        
        # Also store in memory for faster access
        bot_sessions[telegram_id] = session.to_dict()
        return session
    
    # Fallback to in-memory storage
    if telegram_id in bot_sessions:
        session = BotSession.from_dict(bot_sessions[telegram_id])
        if session.is_expired():
            # Session expired, create a new one
            session = BotSession(telegram_id)
            bot_sessions[telegram_id] = session.to_dict()
            # Store in Supabase
            await store_session(telegram_id, session.to_dict())
        else:
            # Update activity
            session.update_activity()
            bot_sessions[telegram_id] = session.to_dict()
            # Update in Supabase
            await store_session(telegram_id, session.to_dict())
        return session
    else:
        # Create new session
        session = BotSession(telegram_id)
        bot_sessions[telegram_id] = session.to_dict()
        # Store in Supabase
        await store_session(telegram_id, session.to_dict())
        return session

async def authenticate_session(telegram_id: str, user_id: str, auth_token: str) -> bool:
    """Authenticate a bot session."""
    try:
        # Validate token with auth service
        is_valid = await validate_token(auth_token)
        if not is_valid:
            return False
            
        # Get or create session
        session = await get_or_create_session(telegram_id)
        
        # Update session with authentication info
        session.user_id = user_id
        session.auth_token = auth_token
        session.is_authenticated = True
        session.update_activity()
        
        # Save session
        bot_sessions[telegram_id] = session.to_dict()
        # Store in Supabase
        await store_session(telegram_id, session.to_dict())
        
        logger.info(f"Authenticated session for Telegram ID {telegram_id}")
        return True
    except Exception as e:
        logger.error(f"Error authenticating session: {str(e)}")
        return False

async def end_session(telegram_id: str) -> bool:
    """End a bot session."""
    if telegram_id in bot_sessions:
        # Get session
        session = BotSession.from_dict(bot_sessions[telegram_id])
        
        # If authenticated, notify auth service about logout
        if session.is_authenticated and session.auth_token:
            try:
                async with httpx.AsyncClient() as client:
                    await client.post(
                        f"{settings.AUTH_SERVICE_URL}/auth/logout",
                        headers={"Authorization": f"Bearer {session.auth_token}"}
                    )
            except Exception as e:
                logger.error(f"Error notifying auth service about logout: {str(e)}")
        
        # Remove session from memory
        del bot_sessions[telegram_id]
        # Remove from Supabase
        await delete_session_from_supabase(telegram_id)
        
        logger.info(f"Ended session for Telegram ID {telegram_id}")
        return True
    
    # Try to delete from Supabase even if not in memory
    await delete_session_from_supabase(telegram_id)
    return False

async def is_authenticated(telegram_id: str) -> bool:
    """Check if a user is authenticated."""
    # Try to get session from Supabase first
    supabase_session = await get_session_from_supabase(telegram_id)
    
    if supabase_session:
        session = BotSession.from_dict(supabase_session)
        if session.is_expired():
            # Session expired
            logger.info(f"Session expired for user {telegram_id}")
            await end_session(telegram_id)
            return False
            
        if session.is_authenticated and session.auth_token:
            # Periodically validate token (e.g., every 5 minutes)
            # This reduces load on the auth service while ensuring token validity
            token_validation_interval = 5 * 60  # 5 minutes
            current_time = time.time()
            last_validation = session.context.get("last_token_validation", 0)
            
            if current_time - last_validation > token_validation_interval:
                # Time to validate token again
                logger.info(f"Validating token for user {telegram_id}")
                is_valid = await validate_token(session.auth_token)
                session.context["last_token_validation"] = current_time
                
                # Update in memory and Supabase
                bot_sessions[telegram_id] = session.to_dict()
                await store_session(telegram_id, session.to_dict())
                
                if not is_valid:
                    # Token is invalid, end session
                    logger.info(f"Token invalid for user {telegram_id}")
                    await end_session(telegram_id)
                    return False
            
            # Update activity
            session.update_activity()
            # Update in memory and Supabase
            bot_sessions[telegram_id] = session.to_dict()
            await store_session(telegram_id, session.to_dict())
            
            logger.info(f"User {telegram_id} is authenticated")
            return True
        else:
            logger.info(f"User {telegram_id} is not authenticated (no token)")
    
    # Fallback to in-memory storage
    if telegram_id in bot_sessions:
        session = BotSession.from_dict(bot_sessions[telegram_id])
        if session.is_expired():
            # Session expired
            logger.info(f"Session expired for user {telegram_id}")
            await end_session(telegram_id)
            return False
            
        if session.is_authenticated and session.auth_token:
            # Periodically validate token (e.g., every 5 minutes)
            token_validation_interval = 5 * 60  # 5 minutes
            current_time = time.time()
            last_validation = session.context.get("last_token_validation", 0)
            
            if current_time - last_validation > token_validation_interval:
                # Time to validate token again
                logger.info(f"Validating token for user {telegram_id}")
                is_valid = await validate_token(session.auth_token)
                session.context["last_token_validation"] = current_time
                bot_sessions[telegram_id] = session.to_dict()
                
                if not is_valid:
                    # Token is invalid, end session
                    logger.info(f"Token invalid for user {telegram_id}")
                    await end_session(telegram_id)
                    return False
            
            # Update activity
            session.update_activity()
            bot_sessions[telegram_id] = session.to_dict()
            # Store in Supabase
            await store_session(telegram_id, session.to_dict())
            
            logger.info(f"User {telegram_id} is authenticated")
            return True
        else:
            logger.info(f"User {telegram_id} is not authenticated (no token)")
    else:
        logger.info(f"No session found for user {telegram_id}")
    
    return False

async def update_session_state(telegram_id: str, state: Any, context: Optional[Dict[str, Any]] = None) -> bool:
    """Update a bot session's state and context."""
    # Try to get session from Supabase first
    supabase_session = await get_session_from_supabase(telegram_id)
    
    if supabase_session:
        session = BotSession.from_dict(supabase_session)
        session.state = state
        if context:
            session.context.update(context)
        session.update_activity()
        # Update in memory and Supabase
        bot_sessions[telegram_id] = session.to_dict()
        await store_session(telegram_id, session.to_dict())
        return True
    
    # Fallback to in-memory storage
    if telegram_id in bot_sessions:
        session = BotSession.from_dict(bot_sessions[telegram_id])
        session.state = state
        if context:
            session.context.update(context)
        session.update_activity()
        bot_sessions[telegram_id] = session.to_dict()
        # Store in Supabase
        await store_session(telegram_id, session.to_dict())
        return True
    return False

async def get_session_state(telegram_id: str) -> Optional[Any]:
    """Get a bot session's state."""
    # Try to get session from Supabase first
    supabase_session = await get_session_from_supabase(telegram_id)
    
    if supabase_session:
        session = BotSession.from_dict(supabase_session)
        if session.is_expired():
            await end_session(telegram_id)
            return None
        session.update_activity()
        # Update in memory and Supabase
        bot_sessions[telegram_id] = session.to_dict()
        await store_session(telegram_id, session.to_dict())
        return session.state
    
    # Fallback to in-memory storage
    if telegram_id in bot_sessions:
        session = BotSession.from_dict(bot_sessions[telegram_id])
        if session.is_expired():
            await end_session(telegram_id)
            return None
        session.update_activity()
        bot_sessions[telegram_id] = session.to_dict()
        # Store in Supabase
        await store_session(telegram_id, session.to_dict())
        return session.state
    return None

async def get_session_context(telegram_id: str) -> Dict[str, Any]:
    """Get a bot session's context."""
    # Try to get session from Supabase first
    supabase_session = await get_session_from_supabase(telegram_id)
    
    if supabase_session:
        session = BotSession.from_dict(supabase_session)
        if session.is_expired():
            await end_session(telegram_id)
            return {}
        session.update_activity()
        # Update in memory and Supabase
        bot_sessions[telegram_id] = session.to_dict()
        await store_session(telegram_id, session.to_dict())
        return session.context
    
    # Fallback to in-memory storage
    if telegram_id in bot_sessions:
        session = BotSession.from_dict(bot_sessions[telegram_id])
        if session.is_expired():
            await end_session(telegram_id)
            return {}
        session.update_activity()
        bot_sessions[telegram_id] = session.to_dict()
        # Store in Supabase
        await store_session(telegram_id, session.to_dict())
        return session.context
    return {}

async def get_session(telegram_id: str) -> Optional[Dict[str, Any]]:
    """Get a bot session's data."""
    # Try to get session from Supabase first
    supabase_session = await get_session_from_supabase(telegram_id)
    
    if supabase_session:
        session = BotSession.from_dict(supabase_session)
        if session.is_expired():
            await end_session(telegram_id)
            return None
        session.update_activity()
        # Update in memory and Supabase
        bot_sessions[telegram_id] = session.to_dict()
        await store_session(telegram_id, session.to_dict())
        return {
            "user_id": session.user_id,
            "token": session.auth_token,
            "last_activity": session.last_activity
        }
    
    # Fallback to in-memory storage
    if telegram_id in bot_sessions:
        session = BotSession.from_dict(bot_sessions[telegram_id])
        if session.is_expired():
            await end_session(telegram_id)
            return None
        session.update_activity()
        bot_sessions[telegram_id] = session.to_dict()
        # Store in Supabase
        await store_session(telegram_id, session.to_dict())
        return {
            "user_id": session.user_id,
            "token": session.auth_token,
            "last_activity": session.last_activity
        }
    return None

async def update_session_activity(telegram_id: str) -> bool:
    """Update a bot session's last activity time."""
    # Try to get session from Supabase first
    supabase_session = await get_session_from_supabase(telegram_id)
    
    if supabase_session:
        session = BotSession.from_dict(supabase_session)
        session.update_activity()
        # Update in memory and Supabase
        bot_sessions[telegram_id] = session.to_dict()
        await store_session(telegram_id, session.to_dict())
        return True
    
    # Fallback to in-memory storage
    if telegram_id in bot_sessions:
        session = BotSession.from_dict(bot_sessions[telegram_id])
        session.update_activity()
        bot_sessions[telegram_id] = session.to_dict()
        # Store in Supabase
        await store_session(telegram_id, session.to_dict())
        return True
    return False

async def validate_token(token: str) -> bool:
    """Validate a token with the auth service."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{settings.AUTH_SERVICE_URL}/auth/validate",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            return response.status_code == 200
    except Exception as e:
        logger.error(f"Error validating token: {str(e)}")
        return False

# Compatibility functions for existing code
async def check_auth(telegram_id: str) -> bool:
    """Check if user is authenticated."""
    try:
        # Get session data
        session_data = await get_session(telegram_id)
        
        if not session_data:
            logger.info(f"No session found for user {telegram_id}")
            return False
        
        # Check if session has user_id and token
        if not session_data.get("user_id") or not session_data.get("token"):
            logger.info(f"Session for user {telegram_id} is missing user_id or token")
            return False
        
        # Check if session is expired
        last_activity = session_data.get("last_activity", 0)
        if time.time() - last_activity > SESSION_TIMEOUT:
            logger.info(f"Session expired for user {telegram_id}")
            await end_session(telegram_id)
            return False
        
        # Validate token with auth service (do this periodically to reduce load)
        if time.time() - last_activity > 300:  # Check every 5 minutes
            token = session_data.get("token")
            
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(
                        f"{settings.AUTH_SERVICE_URL}/users/me",
                        headers={"Authorization": f"Bearer {token}"}
                    )
                    
                    if response.status_code != 200:
                        logger.info(f"Token validation failed for user {telegram_id}: {response.status_code}")
                        await end_session(telegram_id)
                        return False
            except Exception as e:
                logger.error(f"Error validating token for user {telegram_id}: {str(e)}")
                # Don't end session on connection errors, just log
                
        # Update last activity
        await update_session_activity(telegram_id)
        
        logger.info(f"User {telegram_id} is authenticated")
        return True
    except Exception as e:
        logger.error(f"Error checking authentication for user {telegram_id}: {str(e)}")
        return False 