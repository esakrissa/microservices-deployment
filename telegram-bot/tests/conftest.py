import os
import pytest
from unittest import mock

# Mock environment variables before any imports
os.environ["TELEGRAM_BOT_TOKEN"] = "test_token"
os.environ["FASTAPI_URL"] = "http://localhost:8000"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close() 