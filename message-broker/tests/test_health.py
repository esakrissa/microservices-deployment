import os
import unittest.mock
import sys
from fastapi.testclient import TestClient

# Mock the google.cloud.pubsub_v1 module
sys.modules['google.cloud.pubsub_v1'] = unittest.mock.MagicMock()

# Mock environment variables
with unittest.mock.patch.dict(os.environ, {
    "GCP_PROJECT_ID": "test-project",
    "GCP_PUBSUB_TOPIC_ID": "test-topic",
    "TELEGRAM_BOT_URL": "http://localhost:8080"
}):
    # Now import the app after mocking
    from app.main import app

client = TestClient(app)

def test_health_check():
    """Test that the health check endpoint returns a healthy status."""
    # Mock the publisher.list_topics method to avoid actual API calls
    with unittest.mock.patch('app.main.publisher.list_topics'):
        response = client.get("/health")
        assert response.status_code == 200
        assert "status" in response.json()
        assert response.json()["status"] == "healthy"

def test_root_endpoint():
    """Test that the root endpoint returns a message."""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
    assert "Message Broker Service is running" in response.json()["message"] 