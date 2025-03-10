from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    """Test that the health check endpoint returns a healthy status."""
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