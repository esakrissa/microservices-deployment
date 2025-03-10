from fastapi import FastAPI, HTTPException
import os
import logging
from pydantic import BaseModel
import httpx
from typing import Optional
from google.cloud import pubsub_v1
import json
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Message Broker Service")

# GCP Pub/Sub configuration
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
TOPIC_ID = os.getenv("GCP_PUBSUB_TOPIC_ID", "messages")

# Telegram bot service URL
TELEGRAM_BOT_URL = os.getenv("TELEGRAM_BOT_URL", "http://localhost:8080")

# Initialize Pub/Sub publisher
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)

# Check if the topic exists, if not create it
try:
    publisher.get_topic(request={"topic": topic_path})
    logger.info(f"Topic {topic_path} already exists")
except Exception as e:
    try:
        publisher.create_topic(request={"name": topic_path})
        logger.info(f"Topic {topic_path} created successfully")
    except Exception as e:
        logger.error(f"Failed to create topic: {str(e)}")

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
        # Create a unique message ID
        message_id = str(uuid.uuid4())
        
        # Prepare message data
        message_data = {
            "id": message_id,
            "user_id": message.user_id,
            "content": message.content,
            "service": message.service or "unknown"
        }
        
        # Publish message to Pub/Sub
        data = json.dumps(message_data).encode("utf-8")
        future = publisher.publish(topic_path, data)
        pub_id = future.result()
        
        logger.info(f"Message published to Pub/Sub with ID: {pub_id}")
        
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
        # Check Pub/Sub connection by listing topics
        publisher.list_topics(request={"project": f"projects/{PROJECT_ID}"})
        return {"status": "healthy"}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail=str(e))