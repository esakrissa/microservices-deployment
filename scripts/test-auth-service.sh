#!/bin/bash

# Test script for auth service
# This script tests the auth service endpoints

# Set the auth service URL
AUTH_URL=${AUTH_SERVICE_URL:-http://localhost:8001}

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "Testing Auth Service at $AUTH_URL"

# Test health endpoint
echo -e "\n${GREEN}Testing health endpoint...${NC}"
curl -s $AUTH_URL/health | jq

# Register a new user
echo -e "\n${GREEN}Registering a new user...${NC}"
REGISTER_RESPONSE=$(curl -s -X POST \
  $AUTH_URL/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "password123",
    "role": "user"
  }')

echo $REGISTER_RESPONSE | jq

# Login with the new user
echo -e "\n${GREEN}Logging in with the new user...${NC}"
LOGIN_RESPONSE=$(curl -s -X POST \
  $AUTH_URL/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=password123")

echo $LOGIN_RESPONSE | jq

# Extract the token
TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')

if [ "$TOKEN" != "null" ]; then
  # Get current user info
  echo -e "\n${GREEN}Getting current user info...${NC}"
  curl -s -X GET \
    $AUTH_URL/users/me \
    -H "Authorization: Bearer $TOKEN" | jq

  # Try to get all users (should fail for non-admin)
  echo -e "\n${GREEN}Trying to get all users (should fail for non-admin)...${NC}"
  curl -s -X GET \
    $AUTH_URL/users \
    -H "Authorization: Bearer $TOKEN" | jq

  # Register an admin user
  echo -e "\n${GREEN}Registering an admin user...${NC}"
  ADMIN_REGISTER_RESPONSE=$(curl -s -X POST \
    $AUTH_URL/auth/register \
    -H "Content-Type: application/json" \
    -d '{
      "email": "admin@example.com",
      "username": "adminuser",
      "password": "admin123",
      "role": "admin"
    }')

  echo $ADMIN_REGISTER_RESPONSE | jq

  # Login with the admin user
  echo -e "\n${GREEN}Logging in with the admin user...${NC}"
  ADMIN_LOGIN_RESPONSE=$(curl -s -X POST \
    $AUTH_URL/auth/login \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=admin@example.com&password=admin123")

  echo $ADMIN_LOGIN_RESPONSE | jq

  # Extract the admin token
  ADMIN_TOKEN=$(echo $ADMIN_LOGIN_RESPONSE | jq -r '.access_token')

  if [ "$ADMIN_TOKEN" != "null" ]; then
    # Get all users with admin token
    echo -e "\n${GREEN}Getting all users with admin token...${NC}"
    curl -s -X GET \
      $AUTH_URL/users \
      -H "Authorization: Bearer $ADMIN_TOKEN" | jq

    # Update the regular user
    echo -e "\n${GREEN}Updating the regular user...${NC}"
    USER_ID=$(echo $REGISTER_RESPONSE | jq -r '.id')
    curl -s -X PATCH \
      $AUTH_URL/users/$USER_ID \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $ADMIN_TOKEN" \
      -d '{
        "username": "updated_testuser"
      }' | jq
  else
    echo -e "\n${RED}Failed to get admin token${NC}"
  fi
else
  echo -e "\n${RED}Failed to get token${NC}"
fi

echo -e "\n${GREEN}Auth service test completed${NC}" 