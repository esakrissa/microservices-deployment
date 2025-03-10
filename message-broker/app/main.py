from fastapi import FastAPI, HTTPException
import os
import redis
import json
import logging
from pydantic import BaseModel
import httpx
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Message Broker Service")

# Redis configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")

# Telegram bot service URL
TELEGRAM_BOT_URL = os.getenv("TELEGRAM_BOT_URL", "http://localhost:8080")

# Initialize Redis client
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    decode_responses=True
)

class Message(BaseModel):
    user_id: str
    content: str
    service: Optional[str] = None

@app.get("/")
async def root():
    return {"message": "Message Broker Service is running"}

@app.post("/send")
async def send_message(message: Message):
    try:
        # Store message in Redis
        message_id = redis_client.incr("message_id")
        message_data = {
            "id": message_id,
            "user_id": message.user_id,
            "content": message.content,
            "service": message.service or "unknown"
        }
        
        redis_client.hset(f"message:{message_id}", mapping=message_data)
        redis_client.lpush("message_queue", message_id)
        
        logger.info(f"Message queued: {message_data}")
        
        # Forward to Telegram bot service
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{TELEGRAM_BOT_URL}/send",
                json={
                    "user_id": message.user_id,
                    "content": message.content
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Error forwarding to Telegram bot: {response.text}")
                return {"status": "queued", "detail": "Failed to forward to Telegram bot"}
        
        return {"status": "sent", "message_id": message_id}
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    try:
        # Check Redis connection
        redis_client.ping()
        return {"status": "healthy"}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail=str(e))