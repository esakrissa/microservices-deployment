#!/bin/bash

# Check if .env file exists
if [ ! -f .env ]; then
  echo "No .env file found. Creating one from .env.example..."
  if [ -f .env.example ]; then
    cp .env.example .env
    echo "Created .env file from .env.example. Please edit it with your actual values."
    echo "You may need to restart the setup after editing the .env file."
  else
    echo "Error: .env.example file not found. Please create a .env file manually."
    exit 1
  fi
fi

# Load environment variables from .env file
echo "Loading environment variables from .env file..."
export $(grep -v '^#' .env | xargs)

# Set default values for environment variables if not set in .env
export GCP_PROJECT_ID=${GCP_PROJECT_ID:-local-project}
export GCP_PUBSUB_TOPIC_ID=${GCP_PUBSUB_TOPIC_ID:-messages}
export GCP_PUBSUB_SUBSCRIPTION_ID=${GCP_PUBSUB_SUBSCRIPTION_ID:-messages-sub}

# Check if TELEGRAM_BOT_TOKEN is set
if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ "$TELEGRAM_BOT_TOKEN" = "your_telegram_bot_token" ]; then
  echo "Warning: TELEGRAM_BOT_TOKEN is not set or is using the default value."
  echo "The Telegram bot will not function properly."
  echo "Please edit your .env file and set a valid TELEGRAM_BOT_TOKEN."
  echo "Continuing with a dummy token for now..."
  export TELEGRAM_BOT_TOKEN="dummy_token_for_local_testing"
fi

echo "Starting development environment..."
echo "Using the following configuration:"
echo "  GCP_PROJECT_ID: $GCP_PROJECT_ID"
echo "  GCP_PUBSUB_TOPIC_ID: $GCP_PUBSUB_TOPIC_ID"
echo "  GCP_PUBSUB_SUBSCRIPTION_ID: $GCP_PUBSUB_SUBSCRIPTION_ID"
echo "  TELEGRAM_BOT_TOKEN: ${TELEGRAM_BOT_TOKEN:0:3}...${TELEGRAM_BOT_TOKEN: -3}"

# Build and start the services
docker-compose up --build -d

echo ""
echo "Development environment is starting up..."
echo "Services will be available at:"
echo "  FastAPI App: http://localhost:8000"
echo "  Telegram Bot: http://localhost:8080"
echo "  Message Broker: http://localhost:8081"
echo ""
echo "Test endpoints available at:"
echo "  Health Check: http://localhost:8000/test/health"
echo "  Send Test Message: http://localhost:8000/test/send-message (POST)"
echo "  Pub/Sub Info: http://localhost:8000/test/pubsub-info"
echo ""
echo "To set up the Telegram bot webhook for development:"
echo "  1. Install ngrok: https://ngrok.com/download"
echo "  2. Run ngrok manually: ngrok http 8080"
echo "  3. Copy the HTTPS URL to your .env file as NGROK_URL=<your-ngrok-url>"
echo "  4. Run: ./scripts/setup-telegram-webhook-dev.sh"
echo ""
echo "To view logs, run: docker-compose logs -f"
echo "To stop the environment, run: docker-compose down" 