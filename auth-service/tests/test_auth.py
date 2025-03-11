import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app
from app.services.auth import AuthService
from app.schemas.auth import UserCreate, UserResponse, Token

client = TestClient(app)

@pytest.fixture
def mock_auth_service():
    with patch('app.dependencies.get_auth_service') as mock:
        auth_service = MagicMock(spec=AuthService)
        mock.return_value = auth_service
        yield auth_service

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_register_user(mock_auth_service):
    # Mock the register_user method
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "password123",
        "role": "user"
    }
    
    mock_auth_service.register_user.return_value = UserResponse(
        id="123",
        email="test@example.com",
        username="testuser",
        is_active=True,
        role="user",
        permissions=["read:own_profile"]
    )
    
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 201
    assert response.json()["email"] == "test@example.com"
    assert response.json()["username"] == "testuser"
    assert "password" not in response.json()
    
    # Verify the auth service was called with the correct data
    mock_auth_service.register_user.assert_called_once()

def test_login_user(mock_auth_service):
    # Mock the authenticate_user method
    mock_auth_service.authenticate_user.return_value = Token(
        access_token="test_token",
        token_type="bearer"
    )
    
    form_data = {
        "username": "test@example.com",
        "password": "password123"
    }
    
    response = client.post("/auth/login", data=form_data)
    assert response.status_code == 200
    assert response.json()["access_token"] == "test_token"
    assert response.json()["token_type"] == "bearer"
    
    # Verify the auth service was called with the correct data
    mock_auth_service.authenticate_user.assert_called_once_with(
        "test@example.com", "password123"
    ) 