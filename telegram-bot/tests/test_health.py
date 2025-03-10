import os
import pytest
from unittest import mock
from fastapi.testclient import TestClient

# Create a fixture to mock environment variables
@pytest.fixture(scope="module", autouse=True)
def mock_env_variables():
    with mock.patch.dict(os.environ, {
        "TELEGRAM_BOT_TOKEN": "test_token",
        "FASTAPI_URL": "http://localhost:8000"
    }):
        yield

# Import app after mocking environment variables
from app.main import app

client = TestClient(app)

def test_health_check():
    """Test that the health check endpoint returns a healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"} 