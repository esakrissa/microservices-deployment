from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class UserState:
    """Class to manage user state during conversations."""
    def __init__(self):
        self.state = None
        self.data = {}
    
    def set_state(self, state: str) -> None:
        """Set the current state for the user."""
        self.state = state
        
    def get_state(self) -> Optional[str]:
        """Get the current state for the user."""
        return self.state
        
    def clear_state(self) -> None:
        """Clear the current state for the user."""
        self.state = None
        
    def set_data(self, key: str, value: Any) -> None:
        """Set a data value for the user."""
        self.data[key] = value
        
    def get_data(self, key: str, default: Any = None) -> Any:
        """Get a data value for the user."""
        return self.data.get(key, default)
        
    def clear_data(self) -> None:
        """Clear all data for the user."""
        self.data = {}

# Global state storage
user_states: Dict[str, UserState] = {}

def get_user_state(chat_id: str) -> UserState:
    """Get or create a user state for the given chat ID."""
    if chat_id not in user_states:
        user_states[chat_id] = UserState()
    return user_states[chat_id]

def set_user_state(chat_id: str, state: str) -> None:
    """Set the state for a user."""
    user_state = get_user_state(chat_id)
    user_state.set_state(state)
    logger.info(f"Set state for user {chat_id} to {state}")

def get_current_state(chat_id: str) -> Optional[str]:
    """Get the current state for a user."""
    user_state = get_user_state(chat_id)
    return user_state.get_state()

def clear_user_state(chat_id: str) -> None:
    """Clear the state for a user."""
    user_state = get_user_state(chat_id)
    user_state.clear_state()
    logger.info(f"Cleared state for user {chat_id}")

def set_user_data(chat_id: str, key: str, value: Any) -> None:
    """Set a data value for a user."""
    user_state = get_user_state(chat_id)
    user_state.set_data(key, value)

def get_user_data(chat_id: str, key: str, default: Any = None) -> Any:
    """Get a data value for a user."""
    user_state = get_user_state(chat_id)
    return user_state.get_data(key, default)

def clear_user_data(chat_id: str) -> None:
    """Clear all data for a user."""
    user_state = get_user_state(chat_id)
    user_state.clear_data()
    logger.info(f"Cleared data for user {chat_id}") 