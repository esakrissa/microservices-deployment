from fastapi import FastAPI, HTTPException
import os
import json
from pydantic import BaseModel, Field
import httpx
import logging
from typing import Optional, List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="FastAPI Service")

# Message broker configuration
BROKER_URL = os.getenv("BROKER_URL", "http://localhost:8080")

# Check if we're in a local development environment
IS_LOCAL_DEV = os.getenv("ENVIRONMENT", "production").lower() == "development"

class Message(BaseModel):
    content: str
    user_id: Optional[str] = None

# Travel-related models
class TravelItem(BaseModel):
    id: str
    name: str
    description: str
    price: Optional[str] = None

class TravelCategory(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    items: List[TravelItem]

class TravelMenu(BaseModel):
    categories: List[TravelCategory]

# User settings model
class UserSettings(BaseModel):
    user_id: str
    settings: Dict[str, str]
    
@app.get("/")
async def root():
    return {"message": "FastAPI Service v1.6 is running"}

# Travel-related endpoints
@app.get("/api/travel/menu", response_model=TravelMenu, tags=["travel"])
async def get_travel_menu():
    """Get the travel menu with all categories and items."""
    return {
        "categories": [
            {
                "id": "destinations",
                "name": "Popular Destinations",
                "description": "Explore some of the world's most iconic cities and breathtaking landscapes.",
                "items": [
                    {
                        "id": "paris",
                        "name": "Paris",
                        "description": "The City of Light"
                    },
                    {
                        "id": "tokyo",
                        "name": "Tokyo",
                        "description": "Modern meets traditional"
                    },
                    {
                        "id": "nyc",
                        "name": "New York",
                        "description": "The Big Apple"
                    }
                ]
            },
            {
                "id": "activities",
                "name": "Activities",
                "description": "Enhance your travel experience with these unforgettable activities.",
                "items": [
                    {
                        "id": "tours",
                        "name": "Guided Tours",
                        "description": "Explore with local experts"
                    },
                    {
                        "id": "adventure",
                        "name": "Adventure Sports",
                        "description": "For thrill seekers"
                    },
                    {
                        "id": "culinary",
                        "name": "Culinary Experiences",
                        "description": "Taste local flavors"
                    }
                ]
            },
            {
                "id": "accommodations",
                "name": "Accommodations",
                "description": "Find the perfect place to stay for your travel style and budget.",
                "items": [
                    {
                        "id": "hotels",
                        "name": "Hotels",
                        "description": "From budget to luxury"
                    },
                    {
                        "id": "rentals",
                        "name": "Vacation Rentals",
                        "description": "Homes away from home"
                    },
                    {
                        "id": "unique",
                        "name": "Unique Stays",
                        "description": "Treehouses, igloos, and more"
                    }
                ]
            }
        ]
    }

@app.get("/api/travel/categories/{category_id}", response_model=TravelCategory, tags=["travel"])
async def get_category_details(category_id: str):
    """Get detailed information about a specific travel category."""
    categories = {
        "destinations": {
            "id": "destinations",
            "name": "Popular Destinations",
            "description": "Explore some of the world's most iconic cities and breathtaking landscapes.",
            "items": [
                {
                    "id": "paris",
                    "name": "Paris, France",
                    "description": "Known for the Eiffel Tower, Louvre Museum, and exquisite cuisine.",
                    "price": "From $1,200 per person"
                },
                {
                    "id": "tokyo",
                    "name": "Tokyo, Japan",
                    "description": "A fascinating blend of ultramodern and traditional, from neon-lit skyscrapers to historic temples.",
                    "price": "From $1,500 per person"
                },
                {
                    "id": "nyc",
                    "name": "New York City, USA",
                    "description": "The city that never sleeps offers Broadway shows, world-class museums, and iconic landmarks.",
                    "price": "From $1,100 per person"
                },
                {
                    "id": "bali",
                    "name": "Bali, Indonesia",
                    "description": "Tropical paradise with beautiful beaches, lush rice terraces, and spiritual retreats.",
                    "price": "From $950 per person"
                }
            ]
        },
        "activities": {
            "id": "activities",
            "name": "Activities",
            "description": "Enhance your travel experience with these unforgettable activities.",
            "items": [
                {
                    "id": "tours",
                    "name": "Guided City Tours",
                    "description": "Explore with knowledgeable local guides who share insights and hidden gems.",
                    "price": "From $25 per person"
                },
                {
                    "id": "adventure",
                    "name": "Adventure Sports",
                    "description": "From zip-lining and white water rafting to scuba diving and mountain climbing.",
                    "price": "From $50 per activity"
                },
                {
                    "id": "culinary",
                    "name": "Culinary Experiences",
                    "description": "Cooking classes, food tours, and wine tastings to savor local flavors.",
                    "price": "From $40 per experience"
                },
                {
                    "id": "cultural",
                    "name": "Cultural Workshops",
                    "description": "Learn traditional crafts, dance, or music from local artisans.",
                    "price": "From $30 per workshop"
                }
            ]
        },
        "accommodations": {
            "id": "accommodations",
            "name": "Accommodations",
            "description": "Find the perfect place to stay for your travel style and budget.",
            "items": [
                {
                    "id": "luxury",
                    "name": "Luxury Hotels",
                    "description": "5-star accommodations with premium amenities and exceptional service.",
                    "price": "From $250 per night"
                },
                {
                    "id": "boutique",
                    "name": "Boutique Hotels",
                    "description": "Unique, stylish properties with personalized service and local character.",
                    "price": "From $150 per night"
                },
                {
                    "id": "rentals",
                    "name": "Vacation Rentals",
                    "description": "Apartments, villas, and homes with kitchen facilities and more space.",
                    "price": "From $100 per night"
                },
                {
                    "id": "unique",
                    "name": "Unique Stays",
                    "description": "Extraordinary accommodations like treehouses, igloos, underwater rooms, and more.",
                    "price": "From $200 per night"
                }
            ]
        }
    }
    
    if category_id not in categories:
        raise HTTPException(status_code=404, detail=f"Category {category_id} not found")
    
    return categories[category_id]

@app.get("/api/users/{user_id}/settings", response_model=UserSettings, tags=["users"])
async def get_user_settings(user_id: str):
    """Get settings for a specific user."""
    # In a real application, this would fetch from a database
    return {
        "user_id": user_id,
        "settings": {
            "Language": "English",
            "Currency": "USD",
            "Notifications": "Enabled",
            "Time Format": "12-hour",
            "Theme": "Light",
            "Email": "user@example.com"
        }
    }

# Include test endpoints only in local development environment
if IS_LOCAL_DEV:
    try:
        # Note: This is kept for backward compatibility
        # The test endpoints have been moved to the main application
        from tests.test_endpoints import router as test_router
        app.include_router(test_router)
        logger.info("Test endpoints included for local development")
    except ImportError as e:
        logger.warning(f"Test endpoints not found: {str(e)}")
        logger.info("Using main application endpoints instead")

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