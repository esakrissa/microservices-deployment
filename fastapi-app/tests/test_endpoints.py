"""
Test endpoints for local development.
These endpoints are only available in the local development environment.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import httpx
import os
import logging
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/test", tags=["test"])

# Get environment variables
BROKER_URL = os.getenv("BROKER_URL", "http://message-broker:8080")
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "local-project")
GCP_PUBSUB_TOPIC_ID = os.getenv("GCP_PUBSUB_TOPIC_ID", "local-messages")
GCP_PUBSUB_SUBSCRIPTION_ID = os.getenv("GCP_PUBSUB_SUBSCRIPTION_ID", "local-messages-sub")

# Models
class TestMessage(BaseModel):
    content: str
    user_id: str

class ServiceStatus(BaseModel):
    service: str
    status: str
    details: Optional[Dict[str, Any]] = None

class TestResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

@router.get("/", response_model=TestResponse)
async def test_root():
    """Test endpoint to check if the test router is working."""
    return {
        "success": True,
        "message": "Test endpoints are working",
        "data": {
            "environment": {
                "BROKER_URL": BROKER_URL,
                "GCP_PROJECT_ID": GCP_PROJECT_ID,
                "GCP_PUBSUB_TOPIC_ID": GCP_PUBSUB_TOPIC_ID,
                "GCP_PUBSUB_SUBSCRIPTION_ID": GCP_PUBSUB_SUBSCRIPTION_ID
            }
        }
    }

@router.get("/health", response_model=List[ServiceStatus])
async def test_health():
    """Test endpoint to check the health of all services."""
    services = []
    
    # Check FastAPI app
    services.append({
        "service": "fastapi-app",
        "status": "up",
        "details": {"message": "FastAPI app is running"}
    })
    
    # Check Message Broker
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{BROKER_URL}")
            if response.status_code == 200:
                services.append({
                    "service": "message-broker",
                    "status": "up",
                    "details": response.json()
                })
            else:
                services.append({
                    "service": "message-broker",
                    "status": "error",
                    "details": {"error": f"Status code: {response.status_code}"}
                })
    except Exception as e:
        services.append({
            "service": "message-broker",
            "status": "down",
            "details": {"error": str(e)}
        })
    
    # Check Telegram Bot
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://telegram-bot:8080")
            services.append({
                "service": "telegram-bot",
                "status": "up" if response.status_code != 500 else "error",
                "details": {"status_code": response.status_code}
            })
    except Exception as e:
        services.append({
            "service": "telegram-bot",
            "status": "down",
            "details": {"error": str(e)}
        })
    
    return services

@router.post("/send-message", response_model=TestResponse)
async def test_send_message(message: TestMessage):
    """Test endpoint to send a message through the system."""
    try:
        # Send message to the broker
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{BROKER_URL}/send",
                json={"content": message.content, "user_id": message.user_id, "service": "test"}
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Failed to send message to broker")
            
            return {
                "success": True,
                "message": f"Message sent successfully: {message.content}",
                "data": response.json()
            }
    except httpx.RequestError as e:
        logger.error(f"Error sending message to broker: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error sending message to broker: {str(e)}")

@router.get("/pubsub-info", response_model=TestResponse)
async def test_pubsub_info():
    """Test endpoint to get information about Pub/Sub configuration."""
    return {
        "success": True,
        "message": "Pub/Sub configuration",
        "data": {
            "project_id": GCP_PROJECT_ID,
            "topic_id": GCP_PUBSUB_TOPIC_ID,
            "subscription_id": GCP_PUBSUB_SUBSCRIPTION_ID,
            "topic_path": f"projects/{GCP_PROJECT_ID}/topics/{GCP_PUBSUB_TOPIC_ID}",
            "subscription_path": f"projects/{GCP_PROJECT_ID}/subscriptions/{GCP_PUBSUB_SUBSCRIPTION_ID}"
        }
    }