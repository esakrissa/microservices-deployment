from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Supabase settings
    SUPABASE_URL: str
    SUPABASE_KEY: str
    
    # JWT settings
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Message broker settings
    BROKER_URL: str = "http://message-broker:8080"
    
    # GCP settings
    GCP_PROJECT_ID: str = "local-project"
    GCP_PUBSUB_TOPIC_ID: str = "messages"
    GCP_PUBSUB_SUBSCRIPTION_ID: str = "messages-sub"
    
    class Config:
        env_file = ".env"
    
    def __hash__(self):
        return hash((self.SUPABASE_URL, self.SUPABASE_KEY, self.JWT_SECRET_KEY))

@lru_cache()
def get_settings() -> Settings:
    return Settings() 