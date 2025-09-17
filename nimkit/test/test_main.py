"""Tests for the main FastAPI application."""

import pytest
from fastapi.testclient import TestClient

from nimkit.src.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to NVIDIA NIM Kit API"}


def test_health_endpoint():
    """Test the health check endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "0.1.0"
    assert data["service"] == "nvidia-nim-kit"
    assert "timestamp" in data


def test_openapi_docs():
    """Test that OpenAPI documentation is available."""
    response = client.get("/docs")
    assert response.status_code == 200

    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert "openapi" in response.json()
