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
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{settings.AUTH_SERVICE_URL}/telegram/sessions",
                content=json_data,
                headers={"Content-Type": "application/json"}
            )
            
            return response.status_code in (200, 201)
    except Exception as e:
        logger.error(f"Error storing session in Supabase: {str(e)}")
        return False

async def get_session_from_supabase(telegram_id: str) -> Optional[Dict[str, Any]]:
    """Get a session from Supabase via the auth service."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{settings.AUTH_SERVICE_URL}/telegram/sessions/{telegram_id}"
            )
            
            if response.status_code == 200:
                return response.json()
            return None
    except Exception as e:
        logger.error(f"Error getting session from Supabase: {str(e)}")
        return None

async def delete_session_from_supabase(telegram_id: str) -> bool:
    """Delete a session from Supabase via the auth service."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.delete(
                f"{settings.AUTH_SERVICE_URL}/telegram/sessions/{telegram_id}"
            )
            
            return response.status_code in (200, 204)
    except Exception as e:
        logger.error(f"Error deleting session from Supabase: {str(e)}")
        return False