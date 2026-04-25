"""Tests for FastAPI REST endpoints."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch


@pytest.fixture
def client():
    with patch("app.memory.chroma_store.get_store"), \
         patch("app.db.connector.build_engine"), \
         patch("app.db.connector.validate_connection", return_value=True):
        from app.main import app
        return TestClient(app)


def test_health(client):
    with patch("app.api.routes.build_engine"), \
         patch("app.api.routes.validate_connection", return_value=True), \
         patch("app.api.routes.get_store") as mock_store:
        mock_store.return_value.count.return_value = 20
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"


def test_db_connect_invalid(client):
    with patch("app.api.routes.build_engine"), \
         patch("app.api.routes.validate_connection", return_value=False):
        resp = client.post("/api/db/connect", json={"database_url": "postgresql://bad:url@fake/db"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["connected"] is False


def test_db_connect_valid(client):
    with patch("app.api.routes.build_engine"), \
         patch("app.api.routes.validate_connection", return_value=True), \
         patch("app.api.routes.reflect_schema", return_value={"tables": {"orders": {}, "products": {}}}):
        resp = client.post("/api/db/connect", json={"database_url": "postgresql://user:pass@host/db"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["connected"] is True
        assert data["table_count"] == 2
