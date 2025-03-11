from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import logging
from .config import Settings
from .routers import auth, users, telegram
from .dependencies import get_settings
from .services.message_broker import MessageBroker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Auth Service")

# Load settings
settings = get_settings()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Message broker
message_broker = MessageBroker(settings)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(telegram.router, prefix="/telegram", tags=["telegram"])

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.on_event("startup")
async def startup_event():
    # Connect to message broker
    await message_broker.connect()
    logger.info("Auth service started")

@app.on_event("shutdown")
async def shutdown_event():
    # Close message broker connection
    await message_broker.close()
    logger.info("Auth service stopped") 