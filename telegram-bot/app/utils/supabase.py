import logging
import httpx
import json
from typing import Dict, Any, Optional
from ..config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle special types."""
    def default(self, obj):
        # Handle Enum objects
        if hasattr(obj, 'name') and hasattr(obj, '__class__') and hasattr(obj.__class__, '__members__'):
            return obj.name
        # Let the base class handle other types or raise TypeError
        return super().default(obj)

async def store_session(telegram_id: str, session_data: Dict[str, Any]) -> bool:
    """Store a session in Supabase via the auth service."""
    try:
        # Convert session data to JSON using custom encoder
        json_data = json.dumps({
            "telegram_id": telegram_id,
            "session_data": session_data
        }, cls=CustomJSONEncoder)
        
        logger.info(f"Storing session for telegram_id {telegram_id} at {settings.AUTH_SERVICE_URL}/telegram/sessions")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{settings.AUTH_SERVICE_URL}/telegram/sessions",
                content=json_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code in (200, 201):
                logger.info(f"Successfully stored session for telegram_id {telegram_id}")
                return True
            else:
                logger.error(f"Failed to store session for telegram_id {telegram_id}: {response.status_code} - {response.text}")
                return False
    except Exception as e:
        logger.error(f"Error storing session in Supabase: {str(e)}")
        return False

async def get_session_from_supabase(telegram_id: str) -> Optional[Dict[str, Any]]:
    """Get a session from Supabase via the auth service."""
    try:
        logger.info(f"Getting session for telegram_id {telegram_id} from {settings.AUTH_SERVICE_URL}/telegram/sessions/{telegram_id}")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{settings.AUTH_SERVICE_URL}/telegram/sessions/{telegram_id}"
            )
            
            if response.status_code == 200:
                logger.info(f"Successfully retrieved session for telegram_id {telegram_id}")
                return response.json()
            elif response.status_code == 404:
                # Session not found, return None
                logger.info(f"No session found for telegram_id {telegram_id}")
                return None
            else:
                # Log other errors
                logger.error(f"Error getting session from Supabase: {response.status_code} - {response.text}")
                return None
    except Exception as e:
        logger.error(f"Error getting session from Supabase: {str(e)}")
        return None

async def delete_session_from_supabase(telegram_id: str) -> bool:
    """Delete a session from Supabase via the auth service."""
    try:
        logger.info(f"Deleting session for telegram_id {telegram_id} from {settings.AUTH_SERVICE_URL}/telegram/sessions/{telegram_id}")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.delete(
                f"{settings.AUTH_SERVICE_URL}/telegram/sessions/{telegram_id}"
            )
            
            if response.status_code in (200, 204):
                logger.info(f"Successfully deleted session for telegram_id {telegram_id}")
                return True
            else:
                logger.error(f"Failed to delete session for telegram_id {telegram_id}: {response.status_code} - {response.text}")
                return False
    except Exception as e:
        logger.error(f"Error deleting session from Supabase: {str(e)}")
        return False