from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
import logging
import os
from typing import Optional

class Settings(BaseSettings):
    """Application settings."""
    
    # Telegram settings
    TELEGRAM_BOT_TOKEN: str
    
    # Service URLs
    API_GATEWAY_URL: str
    AUTH_SERVICE_URL: str
    
    # Supabase settings
    SUPABASE_URL: Optional[str] = None
    SUPABASE_KEY: Optional[str] = None
    
    # GCP settings
    GCP_PROJECT_ID: str
    GCP_PUBSUB_TOPIC_ID: str
    GCP_PUBSUB_SUBSCRIPTION_ID: str
    
    # Application settings
    LOG_LEVEL: str = "INFO"
    
    model_config = SettingsConfigDict(env_file=".env")
        
@lru_cache()
def get_settings() -> Settings:
    """Get application settings."""
    return Settings()
    
# Configure logging
logging.basicConfig(
    level=getattr(logging, get_settings().LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__) 