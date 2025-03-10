import pytest
from fastapi.testclient import TestClient

# Import app after environment variables are set in conftest.py
from app.main import app

client = TestClient(app)

def test_health_check():
    """Test that the health check endpoint returns a healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"} 