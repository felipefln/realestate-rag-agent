import pytest
from fastapi.testclient import TestClient

from realestate_rag_agent.main import create_app


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())
