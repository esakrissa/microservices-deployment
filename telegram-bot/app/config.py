from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
import logging
import os
from typing import Optional

class Settings(BaseSettings):
    """Application settings."""
    
    # Telegram settings
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_WEBHOOK_URL: str
    
    # Service URLs
    API_GATEWAY_URL: str = "http://api-gateway:8000"
    AUTH_SERVICE_URL: str = "http://auth-service:8000"
    
    # Supabase settings
    SUPABASE_URL: Optional[str] = None
    SUPABASE_KEY: Optional[str] = None
    
    # GCP settings
    GCP_PROJECT_ID: str = "local-project"
    GCP_PUBSUB_TOPIC_ID: str = "messages-dev"
    GCP_PUBSUB_SUBSCRIPTION_ID: str = "messages-sub-dev"
    
    # Application settings
    LOG_LEVEL: str = "INFO"
    
    # API key for internal service communication
    API_KEY: str = "your-internal-api-key"
    
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