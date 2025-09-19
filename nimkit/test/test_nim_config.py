"""Tests for NIM configuration API endpoints."""

import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from nimkit.src.main import app
from nimkit.src.api.config.nims import RedisNIMManager, NIMData, NIMDataUpdate

client = TestClient(app)


class TestNIMConfigAPI:
    """Test class for NIM configuration API endpoints."""

    def setup_method(self):
        """Set up test data."""
        self.test_nim_id = "meta/llama-3_1-8b-instruct"
        self.test_host = "localhost"
        self.test_port = 8000
        self.test_nim_type = "llm"
        self.test_nim_data = NIMData(
            nim_id=self.test_nim_id,
            host=self.test_host,
            port=self.test_port,
            nim_type=self.test_nim_type,
        )
        self.test_nim_data_update = NIMDataUpdate(
            host=self.test_host, port=self.test_port, nim_type=self.test_nim_type
        )

    def test_get_nim_data_not_found(self):
        """Test getting NIM data when it doesn't exist."""
        with patch("nimkit.src.api.config.routes.nim_manager") as mock_manager:
            mock_manager.get_nim_data.return_value = None

            response = client.get(f"/api/nims/{self.test_nim_id}")
            assert response.status_code == 404
            data = response.json()
            assert data["detail"] == f"NIM data not found for {self.test_nim_id}"

    def test_set_nim_data_success(self):
        """Test setting NIM data successfully."""
        with patch("nimkit.src.api.config.routes.nim_manager") as mock_manager:
            mock_manager.set_nim_data.return_value = True

            response = client.post(
                f"/api/nims/{self.test_nim_id}",
                json={
                    "host": self.test_host,
                    "port": self.test_port,
                    "nim_type": self.test_nim_type,
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["nim_id"] == self.test_nim_id
            assert data["host"] == self.test_host
            assert data["port"] == self.test_port
            assert data["nim_type"] == self.test_nim_type
            assert data["status"] == "success"
            assert (
                f"NIM data set successfully for {self.test_nim_id}" in data["message"]
            )

    def test_set_nim_data_failure(self):
        """Test setting NIM data when it fails."""
        with patch("nimkit.src.api.config.routes.nim_manager") as mock_manager:
            mock_manager.set_nim_data.return_value = False

            response = client.post(
                f"/api/nims/{self.test_nim_id}",
                json={
                    "host": self.test_host,
                    "port": self.test_port,
                    "nim_type": self.test_nim_type,
                },
            )

            assert response.status_code == 500
            data = response.json()
            assert f"Failed to set NIM data for {self.test_nim_id}" in data["detail"]

    def test_get_nim_data_success(self):
        """Test getting NIM data successfully."""
        with patch("nimkit.src.api.config.routes.nim_manager") as mock_manager:
            mock_manager.get_nim_data.return_value = self.test_nim_data

            response = client.get(f"/api/nims/{self.test_nim_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["nim_id"] == self.test_nim_id
            assert data["host"] == self.test_host
            assert data["port"] == self.test_port
            assert data["nim_type"] == self.test_nim_type
            assert data["status"] == "success"

    def test_update_nim_data_success(self):
        """Test updating NIM data successfully."""
        with patch("nimkit.src.api.config.routes.nim_manager") as mock_manager:
            mock_manager.get_nim_data.return_value = self.test_nim_data
            mock_manager.set_nim_data.return_value = True

            response = client.put(
                f"/api/nims/{self.test_nim_id}",
                json={"host": "new-host", "port": 9000, "nim_type": self.test_nim_type},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["nim_id"] == self.test_nim_id
            assert data["host"] == "new-host"
            assert data["port"] == 9000
            assert data["status"] == "success"
            assert (
                f"NIM data updated successfully for {self.test_nim_id}"
                in data["message"]
            )

    def test_update_nim_data_not_found(self):
        """Test updating NIM data when it doesn't exist."""
        with patch("nimkit.src.api.config.routes.nim_manager") as mock_manager:
            mock_manager.get_nim_data.return_value = None

            response = client.put(
                f"/api/nims/{self.test_nim_id}",
                json={
                    "host": self.test_host,
                    "port": self.test_port,
                    "nim_type": self.test_nim_type,
                },
            )

            assert response.status_code == 404
            data = response.json()
            assert data["detail"] == f"NIM data not found for {self.test_nim_id}"

    def test_delete_nim_data_success(self):
        """Test deleting NIM data successfully."""
        with patch("nimkit.src.api.config.routes.nim_manager") as mock_manager:
            mock_manager.delete_nim_data.return_value = True

            response = client.delete(f"/api/nims/{self.test_nim_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["nim_id"] == self.test_nim_id
            assert data["status"] == "success"
            assert (
                f"NIM data deleted successfully for {self.test_nim_id}"
                in data["message"]
            )

    def test_delete_nim_data_not_found(self):
        """Test deleting NIM data when it doesn't exist."""
        with patch("nimkit.src.api.config.routes.nim_manager") as mock_manager:
            mock_manager.delete_nim_data.return_value = False

            response = client.delete(f"/api/nims/{self.test_nim_id}")

            assert response.status_code == 404
            data = response.json()
            assert data["detail"] == f"NIM data not found for {self.test_nim_id}"

    def test_list_nims_success(self):
        """Test listing all NIMs successfully."""
        test_nim_ids = [self.test_nim_id, "another/nim-id"]

        with patch("nimkit.src.api.config.routes.nim_manager") as mock_manager:
            mock_manager.list_nim_ids.return_value = test_nim_ids

            response = client.get("/api/nims/")

            assert response.status_code == 200
            data = response.json()
            assert data["nim_ids"] == test_nim_ids
            assert data["count"] == 2
            assert data["status"] == "success"

    def test_list_nims_empty(self):
        """Test listing NIMs when none exist."""
        with patch("nimkit.src.api.config.routes.nim_manager") as mock_manager:
            mock_manager.list_nim_ids.return_value = []

            response = client.get("/api/nims/")

            assert response.status_code == 200
            data = response.json()
            assert data["nim_ids"] == []
            assert data["count"] == 0
            assert data["status"] == "success"

    def test_invalid_json_data(self):
        """Test handling invalid JSON data."""
        response = client.post(
            f"/api/nims/{self.test_nim_id}",
            json={
                "host": self.test_host,
                # Missing required 'port' and 'nim_type' fields
            },
        )

        assert response.status_code == 422  # Validation error

    def test_invalid_port_range(self):
        """Test handling invalid port range."""
        response = client.post(
            f"/api/nims/{self.test_nim_id}",
            json={
                "host": self.test_host,
                "port": 99999,
                "nim_type": self.test_nim_type,
            },  # Invalid port number
        )

        assert response.status_code == 422  # Validation error

    def test_special_characters_in_nim_id(self):
        """Test handling special characters in NIM ID."""
        special_nim_id = "meta/llama-3_1-8b-instruct"

        with patch("nimkit.src.api.config.routes.nim_manager") as mock_manager:
            mock_manager.set_nim_data.return_value = True

            response = client.post(
                f"/api/nims/{special_nim_id}",
                json={
                    "host": self.test_host,
                    "port": self.test_port,
                    "nim_type": self.test_nim_type,
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["nim_id"] == special_nim_id


class TestRedisNIMManager:
    """Test class for RedisNIMManager functionality."""

    def setup_method(self):
        """Set up test data."""
        self.test_nim_id = "meta/llama-3_1-8b-instruct"
        self.test_host = "localhost"
        self.test_port = 8000
        self.test_nim_type = "llm"

    def test_redis_manager_initialization(self):
        """Test RedisNIMManager initialization."""
        mock_redis_client = MagicMock()
        with patch("nimkit.src.api.config.nims.redis.from_url") as mock_redis_from_url:
            mock_redis_from_url.return_value = mock_redis_client

            manager = RedisNIMManager("redis://test:6379/0")

            assert manager.redis_client == mock_redis_client
            assert manager.key_prefix == "nim:"
            mock_redis_from_url.assert_called_once_with(
                "redis://test:6379/0", decode_responses=True
            )

    def test_set_nim_data_success(self):
        """Test setting NIM data successfully."""
        mock_redis_client = MagicMock()
        with patch("nimkit.src.api.config.nims.redis.from_url") as mock_redis_from_url:
            mock_redis_from_url.return_value = mock_redis_client

            manager = RedisNIMManager()
            result = manager.set_nim_data(
                self.test_nim_id, self.test_host, self.test_port, self.test_nim_type
            )

            assert result is True
            mock_redis_client.set.assert_called_once()

    def test_get_nim_data_success(self):
        """Test getting NIM data successfully."""
        mock_redis_client = MagicMock()
        test_data = {
            "nim_id": self.test_nim_id,
            "host": self.test_host,
            "port": self.test_port,
            "nim_type": self.test_nim_type,
        }
        mock_redis_client.get.return_value = json.dumps(test_data)

        with patch("nimkit.src.api.config.nims.redis.from_url") as mock_redis_from_url:
            mock_redis_from_url.return_value = mock_redis_client

            manager = RedisNIMManager()
            result = manager.get_nim_data(self.test_nim_id)

            assert result is not None
            assert isinstance(result, NIMData)
            assert result.nim_id == self.test_nim_id
            assert result.host == self.test_host
            assert result.port == self.test_port
            assert result.nim_type == self.test_nim_type

    def test_get_nim_data_not_found(self):
        """Test getting NIM data when it doesn't exist."""
        mock_redis_client = MagicMock()
        mock_redis_client.get.return_value = None

        with patch("nimkit.src.api.config.nims.redis.from_url") as mock_redis_from_url:
            mock_redis_from_url.return_value = mock_redis_client

            manager = RedisNIMManager()
            result = manager.get_nim_data(self.test_nim_id)

            assert result is None

    def test_delete_nim_data_success(self):
        """Test deleting NIM data successfully."""
        mock_redis_client = MagicMock()
        mock_redis_client.delete.return_value = 1  # Redis returns 1 when key is deleted

        with patch("nimkit.src.api.config.nims.redis.from_url") as mock_redis_from_url:
            mock_redis_from_url.return_value = mock_redis_client

            manager = RedisNIMManager()
            result = manager.delete_nim_data(self.test_nim_id)

            assert result is True
            mock_redis_client.delete.assert_called_once()

    def test_delete_nim_data_not_found(self):
        """Test deleting NIM data when it doesn't exist."""
        mock_redis_client = MagicMock()
        mock_redis_client.delete.return_value = (
            0  # Redis returns 0 when key doesn't exist
        )

        with patch("nimkit.src.api.config.nims.redis.from_url") as mock_redis_from_url:
            mock_redis_from_url.return_value = mock_redis_client

            manager = RedisNIMManager()
            result = manager.delete_nim_data(self.test_nim_id)

            assert result is False

    def test_list_nim_ids_success(self):
        """Test listing NIM IDs successfully."""
        mock_redis_client = MagicMock()
        mock_redis_client.keys.return_value = [
            f"nim:{self.test_nim_id}",
            "nim:another/nim-id",
        ]

        with patch("nimkit.src.api.config.nims.redis.from_url") as mock_redis_from_url:
            mock_redis_from_url.return_value = mock_redis_client

            manager = RedisNIMManager()
            result = manager.list_nim_ids()

            assert result == [self.test_nim_id, "another/nim-id"]

    def test_list_nim_ids_empty(self):
        """Test listing NIM IDs when none exist."""
        mock_redis_client = MagicMock()
        mock_redis_client.keys.return_value = []

        with patch("nimkit.src.api.config.nims.redis.from_url") as mock_redis_from_url:
            mock_redis_from_url.return_value = mock_redis_client

            manager = RedisNIMManager()
            result = manager.list_nim_ids()

            assert result == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
