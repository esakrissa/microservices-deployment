import os
import json
import logging
from google.cloud import pubsub_v1
import httpx
import time
from concurrent.futures import TimeoutError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# GCP Pub/Sub configuration
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
SUBSCRIPTION_ID = os.getenv("GCP_PUBSUB_SUBSCRIPTION_ID", "messages-sub")
TOPIC_ID = os.getenv("GCP_PUBSUB_TOPIC_ID", "messages")

# Telegram bot service URL
TELEGRAM_BOT_URL = os.getenv("TELEGRAM_BOT_URL", "http://localhost:8080")

# Initialize Pub/Sub subscriber
subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_ID)
topic_path = subscriber.topic_path(PROJECT_ID, TOPIC_ID)

# Check if the subscription exists, if not create it
try:
    subscriber.get_subscription(request={"subscription": subscription_path})
    logger.info(f"Subscription {subscription_path} already exists")
except Exception as e:
    try:
        subscriber.create_subscription(
            request={"name": subscription_path, "topic": topic_path}
        )
        logger.info(f"Subscription {subscription_path} created successfully")
    except Exception as e:
        logger.error(f"Failed to create subscription: {str(e)}")

def process_message(message):
    """Process a message received from Pub/Sub."""
    try:
        data = json.loads(message.data.decode("utf-8"))
        logger.info(f"Received message: {data}")
        
        # Forward the message to the Telegram bot
        if "user_id" in data and "content" in data:
            try:
                # Use httpx to send the message to the Telegram bot
                with httpx.Client(timeout=10.0) as client:
                    response = client.post(
                        f"{TELEGRAM_BOT_URL}/send",
                        json={
                            "user_id": data["user_id"],
                            "content": data["content"]
                        }
                    )
                    
                    if response.status_code == 200:
                        logger.info(f"Message forwarded to Telegram bot successfully")
                    else:
                        logger.error(f"Failed to forward message to Telegram bot: {response.text}")
            except Exception as e:
                logger.error(f"Error forwarding message to Telegram bot: {str(e)}")
        
        # Acknowledge the message
        message.ack()
        
        return True
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        # Negative acknowledgement - message will be redelivered
        message.nack()
        return False

def start_subscriber():
    """Start the subscriber to listen for messages."""
    logger.info("Starting Pub/Sub subscriber...")
    
    streaming_pull_future = subscriber.subscribe(
        subscription_path, callback=process_message
    )
    
    # Keep the subscriber running
    try:
        logger.info(f"Listening for messages on {subscription_path}")
        # Result() blocks until an exception is raised
        streaming_pull_future.result()
    except TimeoutError:
        streaming_pull_future.cancel()
        logger.warning("Streaming pull future timed out, restarting...")
        start_subscriber()
    except Exception as e:
        streaming_pull_future.cancel()
        logger.error(f"Subscriber error: {str(e)}")
        # Wait a bit before restarting
        time.sleep(5)
        start_subscriber()

if __name__ == "__main__":
    start_subscriber() 