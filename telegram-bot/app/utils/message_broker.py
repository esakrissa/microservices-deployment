import os
import json
import logging
import httpx
from typing import Dict, Any, Callable, Awaitable, Optional
from google.cloud import pubsub_v1
from ..config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class MessageBrokerClient:
    """Client for interacting with the message broker service."""
    
    def __init__(self):
        """Initialize the message broker client."""
        self.project_id = settings.GCP_PROJECT_ID
        self.topic_id = settings.GCP_PUBSUB_TOPIC_ID
        self.subscription_id = settings.GCP_PUBSUB_SUBSCRIPTION_ID
        self.publisher = None
        self.subscriber = None
        self.topic_path = None
        self.subscription_path = None
        self.handlers = {}
        self.is_available = False
        
    def initialize(self):
        """Initialize the Pub/Sub client."""
        try:
            # Initialize publisher
            self.publisher = pubsub_v1.PublisherClient()
            self.topic_path = self.publisher.topic_path(self.project_id, self.topic_id)
            
            # Initialize subscriber
            self.subscriber = pubsub_v1.SubscriberClient()
            self.subscription_path = self.subscriber.subscription_path(
                self.project_id, self.subscription_id
            )
            
            logger.info(f"Initialized message broker client for project {self.project_id}")
            self.is_available = True
            return True
        except Exception as e:
            logger.warning(f"Failed to initialize message broker client: {str(e)}")
            logger.warning("Message broker functionality will be disabled")
            self.is_available = False
            return False
            
    async def publish_message(self, topic: str, message: Dict[str, Any]) -> bool:
        """Publish a message to a topic."""
        if not self.is_available:
            # Try to initialize if not already done
            if not self.initialize():
                logger.warning(f"Message broker unavailable, skipping publish to topic {topic}")
                return False
                
        try:
            # Add topic to message
            message["topic"] = topic
            
            # Convert message to JSON
            data = json.dumps(message).encode("utf-8")
            
            # Publish message
            future = self.publisher.publish(self.topic_path, data)
            message_id = future.result()
            
            logger.info(f"Published message to topic {topic} with ID: {message_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to publish message to topic {topic}: {str(e)}")
            return False
            
    def subscribe(self, topic: str, callback: Callable[[Dict[str, Any]], Awaitable[None]]):
        """Subscribe to a topic."""
        if not self.is_available:
            # Try to initialize if not already done
            if not self.initialize():
                logger.warning(f"Message broker unavailable, skipping subscription to topic {topic}")
                return False
                
        # Store callback for this topic
        self.handlers[topic] = callback
        
        logger.info(f"Registered handler for topic {topic}")
        return True
        
    def start_listening(self):
        """Start listening for messages."""
        if not self.is_available:
            # Try to initialize if not already done
            if not self.initialize():
                logger.warning("Message broker unavailable, skipping message listening")
                return None
                
        try:
            # Define callback function
            def callback(message):
                try:
                    # Parse message data
                    data = json.loads(message.data.decode("utf-8"))
                    
                    # Get topic from message
                    topic = data.get("topic")
                    
                    if topic and topic in self.handlers:
                        # Call handler for this topic
                        import asyncio
                        asyncio.create_task(self.handlers[topic](data))
                        logger.info(f"Processed message for topic {topic}")
                    else:
                        logger.warning(f"No handler for topic {topic}")
                        
                    # Acknowledge message
                    message.ack()
                except Exception as e:
                    logger.error(f"Error processing message: {str(e)}")
                    message.nack()
            
            # Start subscriber
            streaming_pull_future = self.subscriber.subscribe(
                self.subscription_path, callback=callback
            )
            
            logger.info(f"Started listening for messages on {self.subscription_path}")
            return streaming_pull_future
        except Exception as e:
            logger.error(f"Failed to start listening: {str(e)}")
            return None
            
    def stop_listening(self, streaming_pull_future):
        """Stop listening for messages."""
        if streaming_pull_future:
            streaming_pull_future.cancel()
            logger.info("Stopped listening for messages")
            
    def close(self):
        """Close the client."""
        if self.is_available and self.subscriber:
            self.subscriber.close()
            logger.info("Closed subscriber client")
            
        logger.info("Closed message broker client") 