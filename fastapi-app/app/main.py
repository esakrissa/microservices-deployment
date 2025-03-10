from fastapi import FastAPI, HTTPException
import os
import json
from pydantic import BaseModel
import httpx
import logging
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="FastAPI Service")

# Message broker configuration
BROKER_URL = os.getenv("BROKER_URL", "http://localhost:8080")

class Message(BaseModel):
    content: str
    user_id: Optional[str] = None
    
@app.get("/")
async def root():
    return {"message": "FastAPI Service v1.6 is running"}

@app.post("/process")
async def process_message(message: Message):
    try:
        logger.info(f"Processing message: {message.content}")
        
        # Process the message (add your logic here)
        processed_content = f"Processed: {message.content}"
        
        # Send the processed message to the Telegram bot via message broker
        if message.user_id:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{BROKER_URL}/send",
                    json={
                        "user_id": message.user_id,
                        "content": processed_content,
                        "service": "fastapi"
                    }
                )
                if response.status_code != 200:
                    logger.error(f"Failed to send message to broker: {response.text}")
                    raise HTTPException(status_code=500, detail="Failed to send message to broker")
        
        return {"processed": processed_content}
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}