#!/bin/bash

# This script initializes the Pub/Sub emulator with topics and subscriptions
# It should be run after the Pub/Sub emulator is started

# Set default values if not provided
PROJECT_ID=${GCP_PROJECT_ID:-local-project}
TOPIC_ID="${GCP_PUBSUB_TOPIC_ID:-messages}-dev"
SUBSCRIPTION_ID="${GCP_PUBSUB_SUBSCRIPTION_ID:-messages-sub}-dev"
PUBSUB_EMULATOR_HOST=${PUBSUB_EMULATOR_HOST:-pubsub-emulator:8085}

echo "Initializing Pub/Sub emulator with:"
echo "  Project ID: $PROJECT_ID"
echo "  Topic ID: $TOPIC_ID"
echo "  Subscription ID: $SUBSCRIPTION_ID"
echo "  Emulator Host: $PUBSUB_EMULATOR_HOST"

# Wait for the Pub/Sub emulator to be ready
echo "Waiting for Pub/Sub emulator to be ready..."
until curl -s http://${PUBSUB_EMULATOR_HOST} > /dev/null; do
  echo "Pub/Sub emulator is not ready yet. Waiting..."
  sleep 2
done
echo "Pub/Sub emulator is ready!"

# Create the topic
echo "Creating topic: $TOPIC_ID"
curl -X PUT "http://${PUBSUB_EMULATOR_HOST}/v1/projects/${PROJECT_ID}/topics/${TOPIC_ID}" \
  -H "Content-Type: application/json" \
  -d "{}"

# Create the subscription
echo "Creating subscription: $SUBSCRIPTION_ID"
curl -X PUT "http://${PUBSUB_EMULATOR_HOST}/v1/projects/${PROJECT_ID}/subscriptions/${SUBSCRIPTION_ID}" \
  -H "Content-Type: application/json" \
  -d "{\"topic\": \"projects/${PROJECT_ID}/topics/${TOPIC_ID}\"}"

echo "Pub/Sub initialization completed successfully!" 