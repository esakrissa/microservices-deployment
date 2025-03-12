import json
import logging
import httpx
import asyncio
from typing import Dict, Any
from ..config import Settings

logger = logging.getLogger(__name__)

class MessageBroker:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.broker_url = settings.BROKER_URL
        self.client = None
        self.max_retries = 3
        self.retry_delay = 1.0  # seconds
        
    async def connect(self):
        """Initialize HTTP client for message broker"""
        try:
            self.client = httpx.AsyncClient(base_url=self.broker_url, timeout=10.0)
            logger.info(f"Initialized HTTP client for message broker at {self.broker_url}")
        except Exception as e:
            logger.error(f"Failed to initialize HTTP client: {e}")
            raise
            
    async def close(self):
        """Close the HTTP client"""
        if self.client:
            await self.client.aclose()
            logger.info("Closed HTTP client for message broker")
            
    async def publish_message(self, topic: str, message: dict, retry_count: int = 0):
        """Publish a message to the message broker service with retry logic"""
        if not self.client:
            await self.connect()
            
        try:
            # Standardize message format
            standardized_message = self._standardize_message(topic, message)
            
            # Send the message to the broker service
            response = await self.client.post("/send", json={
                "user_id": standardized_message.get("user_id", "unknown"),
                "content": json.dumps(standardized_message),
                "service": "auth"
            })
            response.raise_for_status()
            
            logger.info(f"Published message to topic {topic} with ID: {standardized_message.get('id', 'unknown')}")
            return response.json()
        except Exception as e:
            logger.error(f"Failed to publish message to topic {topic}: {e}")
            
            # Implement retry logic
            if retry_count < self.max_retries:
                retry_count += 1
                wait_time = self.retry_delay * (2 ** (retry_count - 1))  # Exponential backoff
                logger.info(f"Retrying publish to topic {topic} in {wait_time} seconds (attempt {retry_count}/{self.max_retries})")
                await asyncio.sleep(wait_time)
                return await self.publish_message(topic, message, retry_count)
            else:
                logger.error(f"Max retries reached for publishing to topic {topic}")
                raise
    
    def _standardize_message(self, topic: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """Standardize message format for consistency across services"""
        # Generate a unique ID if not provided
        if "id" not in message:
            import uuid
            message["id"] = str(uuid.uuid4())
            
        # Add metadata
        standardized = {
            "id": message["id"],
            "topic": topic,
            "version": "1.0",
            "timestamp": message.get("timestamp", self._get_iso_timestamp()),
            "service": "auth-service",
            "payload": message
        }
        
        # Extract user_id for routing if available
        if "user_id" in message:
            standardized["user_id"] = message["user_id"]
        
        return standardized
    
    def _get_iso_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.utcnow().isoformat()
            
    async def subscribe(self, exchange_name: str, queue_name: str, routing_key: str, callback):
        """Subscribe to messages from RabbitMQ"""
        if not self.channel:
            await self.connect()
            
        try:
            # Declare exchange
            exchange = await self.channel.declare_exchange(
                exchange_name,
                aio_pika.ExchangeType.TOPIC,
                durable=True
            )
            
            # Declare queue
            queue = await self.channel.declare_queue(
                queue_name,
                durable=True
            )
            
            # Bind queue to exchange
            await queue.bind(exchange, routing_key)
            
            # Start consuming
            await queue.consume(callback)
            logger.info(f"Subscribed to {exchange_name} with routing key {routing_key}")
        except Exception as e:
            logger.error(f"Failed to subscribe: {e}")
            raise 