#!/bin/bash

# Test script for Telegram bot and auth service integration
# This script tests the integration between the Telegram bot and auth service

# Set the auth service URL
AUTH_URL=${AUTH_SERVICE_URL:-http://localhost:8001}
TELEGRAM_URL=${TELEGRAM_BOT_URL:-http://localhost:8080}

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "Testing Telegram Bot and Auth Service Integration"
echo "Auth Service URL: $AUTH_URL"
echo "Telegram Bot URL: $TELEGRAM_URL"

# Test auth service health
echo -e "\n${GREEN}Testing auth service health...${NC}"
HEALTH_RESPONSE=$(curl -s $AUTH_URL/health)
echo $HEALTH_RESPONSE

# Test Telegram bot health
echo -e "\n${GREEN}Testing Telegram bot health...${NC}"
TELEGRAM_HEALTH_RESPONSE=$(curl -s $TELEGRAM_URL/health)
echo $TELEGRAM_HEALTH_RESPONSE

# Generate a unique timestamp for the email
TIMESTAMP=$(date +%s)
EMAIL="telegram-test-${TIMESTAMP}@example.com"
USERNAME="telegramtest${TIMESTAMP}"

# Register a test user via auth service
echo -e "\n${GREEN}Registering a test user via auth service...${NC}"
REGISTER_RESPONSE=$(curl -s -X POST \
  $AUTH_URL/auth/register \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$EMAIL\",
    \"username\": \"$USERNAME\",
    \"password\": \"password123\",
    \"role\": \"user\"
  }")

echo $REGISTER_RESPONSE

# Extract user ID
USER_ID=$(echo $REGISTER_RESPONSE | grep -o '"id":"[^"]*' | cut -d'"' -f4)
echo "User ID: $USER_ID"

if [ -n "$USER_ID" ]; then
  # Login with the test user
  echo -e "\n${GREEN}Logging in with the test user...${NC}"
  LOGIN_RESPONSE=$(curl -s -X POST \
    $AUTH_URL/auth/login \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=telegram-test@example.com&password=password123")

  echo $LOGIN_RESPONSE

  # Extract the token
  TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
  echo "Token: $TOKEN"

  if [ -n "$TOKEN" ]; then
    # Link a test Telegram ID
    echo -e "\n${GREEN}Linking a test Telegram ID...${NC}"
    TELEGRAM_ID="12345678"
    LINK_RESPONSE=$(curl -s -X POST \
      $AUTH_URL/auth/link-telegram \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $TOKEN" \
      -d "{
        \"telegram_id\": \"$TELEGRAM_ID\"
      }")

    echo $LINK_RESPONSE

    # Simulate a Telegram message
    echo -e "\n${GREEN}Simulating a Telegram message...${NC}"
    MESSAGE_RESPONSE=$(curl -s -X POST \
      $TELEGRAM_URL/webhook \
      -H "Content-Type: application/json" \
      -d "{
        \"update_id\": 123456789,
        \"message\": {
          \"message_id\": 1,
          \"from\": {
            \"id\": $TELEGRAM_ID,
            \"first_name\": \"Test\",
            \"username\": \"testuser\"
          },
          \"chat\": {
            \"id\": $TELEGRAM_ID,
            \"first_name\": \"Test\",
            \"username\": \"testuser\",
            \"type\": \"private\"
          },
          \"date\": $(date +%s),
          \"text\": \"/start\"
        }
      }")

    echo $MESSAGE_RESPONSE
  else
    echo -e "\n${RED}Failed to get token${NC}"
  fi
else
  echo -e "\n${RED}Failed to register user${NC}"
fi

echo -e "\n${GREEN}Integration test completed${NC}" 