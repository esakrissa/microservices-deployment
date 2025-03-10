#!/bin/bash

# Setup script for Google Cloud Pub/Sub

echo "Setting up Google Cloud Pub/Sub..."

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "Error: gcloud CLI is not installed. Please install it first."
    exit 1
fi

# Set default values for environment variables
GCP_PROJECT_ID=${GCP_PROJECT_ID:-""}
GCP_PUBSUB_TOPIC_ID=${GCP_PUBSUB_TOPIC_ID:-"messages"}
GCP_PUBSUB_SUBSCRIPTION_ID=${GCP_PUBSUB_SUBSCRIPTION_ID:-"messages-sub"}

# Check if project ID is provided
if [ -z "$GCP_PROJECT_ID" ]; then
    echo "Error: GCP_PROJECT_ID environment variable is not set."
    echo "Please set it using: export GCP_PROJECT_ID=your-project-id"
    exit 1
fi

echo "Using the following configuration:"
echo "  Project ID: $GCP_PROJECT_ID"
echo "  Topic ID: $GCP_PUBSUB_TOPIC_ID"
echo "  Subscription ID: $GCP_PUBSUB_SUBSCRIPTION_ID"

# Check if user is authenticated with gcloud
if ! gcloud auth print-identity-token &> /dev/null; then
    echo "You are not authenticated with gcloud. Please run 'gcloud auth login' first."
    exit 1
fi

# Set the current project
echo "Setting current project to $GCP_PROJECT_ID..."
gcloud config set project $GCP_PROJECT_ID

# Check if Pub/Sub API is enabled
if ! gcloud services list --enabled | grep -q pubsub.googleapis.com; then
    echo "Enabling Pub/Sub API..."
    gcloud services enable pubsub.googleapis.com
    echo "Pub/Sub API enabled."
else
    echo "Pub/Sub API is already enabled."
fi

# Create topic if it doesn't exist
if ! gcloud pubsub topics describe $GCP_PUBSUB_TOPIC_ID &> /dev/null; then
    echo "Creating Pub/Sub topic $GCP_PUBSUB_TOPIC_ID..."
    gcloud pubsub topics create $GCP_PUBSUB_TOPIC_ID
    echo "Topic created successfully."
else
    echo "Topic $GCP_PUBSUB_TOPIC_ID already exists."
fi

# Create subscription if it doesn't exist
if ! gcloud pubsub subscriptions describe $GCP_PUBSUB_SUBSCRIPTION_ID &> /dev/null; then
    echo "Creating Pub/Sub subscription $GCP_PUBSUB_SUBSCRIPTION_ID..."
    gcloud pubsub subscriptions create $GCP_PUBSUB_SUBSCRIPTION_ID \
        --topic=$GCP_PUBSUB_TOPIC_ID \
        --ack-deadline=60
    echo "Subscription created successfully."
else
    echo "Subscription $GCP_PUBSUB_SUBSCRIPTION_ID already exists."
fi

echo "Pub/Sub setup completed successfully."
echo "You can now use the message broker service with Google Cloud Pub/Sub." 