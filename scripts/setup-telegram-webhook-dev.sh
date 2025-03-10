#!/bin/bash

# This script sets up a local development environment for the Telegram bot webhook
# It uses a manually provided ngrok URL from the .env file

# Load environment variables from .env file if not already loaded
if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ -z "$NGROK_URL" ]; then
    if [ -f .env ]; then
        echo "Loading environment variables from .env file..."
        export $(grep -v '^#' .env | xargs)
    fi
fi

# Check if TELEGRAM_BOT_TOKEN is set
if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ "$TELEGRAM_BOT_TOKEN" = "your_telegram_bot_token" ]; then
    echo "Error: TELEGRAM_BOT_TOKEN is not set or is using the default value."
    echo "Please set a valid TELEGRAM_BOT_TOKEN in your .env file."
    exit 1
fi

# Check if NGROK_URL is set
if [ -z "$NGROK_URL" ]; then
    echo "Error: NGROK_URL is not set in your .env file."
    echo "Please start ngrok manually with: ngrok http 8080"
    echo "Then add the URL to your .env file as NGROK_URL=<your-ngrok-url>"
    echo "Example: NGROK_URL=https://a1b2c3d4.ngrok.io"
    exit 1
fi

# Set up the Telegram webhook
echo "Setting up the Telegram webhook using the provided ngrok URL..."
webhook_url="${NGROK_URL}/webhook"
echo "Webhook URL: $webhook_url"

response=$(curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/setWebhook" \
    -H "Content-Type: application/json" \
    -d "{\"url\": \"$webhook_url\"}")

echo "Telegram API response: $response"

# Check if the webhook was set up successfully
if echo "$response" | grep -q '"ok":true'; then
    echo "Webhook set up successfully!"
    echo "Your Telegram bot is now connected to your local development environment."
    echo "You can send messages to your bot and they will be processed by your local service."
    echo ""
    echo "To disconnect the webhook, run:"
    echo "curl -s -X POST 'https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/deleteWebhook'"
else
    echo "Error: Failed to set up webhook. Please check your TELEGRAM_BOT_TOKEN and NGROK_URL and try again."
    exit 1
fi 