from supabase import create_client, Client
from .config import get_settings
import logging
from fastapi import Depends
from typing import Callable, Optional

logger = logging.getLogger(__name__)
settings = get_settings()

# Supabase client instance
_supabase_client: Optional[Client] = None

def get_supabase_client() -> Client:
    """Get or create a Supabase client."""
    global _supabase_client
    if _supabase_client is None:
        try:
            _supabase_client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_KEY
            )
            logger.info("Supabase client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {str(e)}")
            raise
    return _supabase_client

def get_db():
    """Dependency for getting a Supabase client."""
    return get_supabase_client() 