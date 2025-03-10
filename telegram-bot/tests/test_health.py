import os
import unittest.mock
from fastapi.testclient import TestClient

# Mock environment variables before importing app
with unittest.mock.patch.dict(os.environ, {"TELEGRAM_TOKEN": "test_token", "FASTAPI_URL": "http://localhost:8000"}):
    from app.main import app

client = TestClient(app)

def test_health_check():
    """Test that the health check endpoint returns a healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"} 