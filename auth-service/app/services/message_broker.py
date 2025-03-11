import json
import logging
import httpx
from ..config import Settings

logger = logging.getLogger(__name__)

class MessageBroker:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.broker_url = settings.BROKER_URL
        self.client = None
        
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
            
    async def publish_message(self, topic: str, message: dict):
        """Publish a message to the message broker service"""
        if not self.client:
            await self.connect()
            
        try:
            # Send the message to the broker service
            response = await self.client.post("/send", json={
                "user_id": message.get("user_id", "unknown"),
                "content": json.dumps(message),
                "service": "auth"
            })
            response.raise_for_status()
            
            logger.info(f"Published message to topic {topic}")
            return response.json()
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            raise
            
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