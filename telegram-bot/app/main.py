import os
import logging
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
import httpx
from typing import Optional
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Telegram Bot Token from environment variable
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN environment variable is not set")

# FastAPI service URL
FASTAPI_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")

app = FastAPI(title="Telegram Bot Service")

class TelegramUpdate(BaseModel):
    update_id: int
    message: Optional[dict] = None
    
class MessageToProcess(BaseModel):
    content: str
    user_id: str

class MessageToSend(BaseModel):
    user_id: str
    content: str

@app.post("/webhook")
async def telegram_webhook(update: TelegramUpdate):
    try:
        if not update.message or "text" not in update.message:
            return {"status": "no message text"}
        
        chat_id = str(update.message.get("chat", {}).get("id"))
        message_text = update.message.get("text", "")
        
        logger.info(f"Received message from {chat_id}: {message_text}")
        
        # Send message to FastAPI for processing
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{FASTAPI_URL}/process",
                json={"content": message_text, "user_id": chat_id}
            )
            
            if response.status_code != 200:
                logger.error(f"Error from FastAPI: {response.text}")
                return {"status": "error", "detail": "Failed to process message"}
        
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/send")
async def send_message(message: MessageToSend):
    try:
        # Send message to Telegram
        async with httpx.AsyncClient() as client:
            telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            response = await client.post(
                telegram_url,
                json={
                    "chat_id": message.user_id,
                    "text": message.content
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Error sending message to Telegram: {response.text}")
                raise HTTPException(status_code=500, detail="Failed to send message to Telegram")
        
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# For local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)