"""NIM configuration and data models."""

import json
import logging
import os
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

import redis

logger = logging.getLogger(__name__)


class NIMData(BaseModel):
    """NIM data model containing host, port, and type information."""

    nim_id: str = Field(..., description="Unique identifier for the NIM")
    host: str = Field(..., description="Host address for the NIM")
    port: int = Field(
        ..., ge=1, le=65535, description="Port number for the NIM (1-65535)"
    )
    nim_type: str = Field(
        ...,
        description="Type of NIM (llm, image_gen, 3d, asr, tts, studio_voice, document)",
    )

    model_config = {
        "json_encoders": {
            # Ensure proper JSON serialization
        }
    }


class NIMDataUpdate(BaseModel):
    """Model for updating NIM data."""

    host: str = Field(..., description="Host address for the NIM")
    port: int = Field(
        ..., ge=1, le=65535, description="Port number for the NIM (1-65535)"
    )
    nim_type: str = Field(
        ...,
        description="Type of NIM (llm, image_gen, 3d, asr, tts, studio_voice, document)",
    )


class RedisNIMManager:
    """Redis-based NIM data manager."""

    def __init__(self, redis_url: str = None):
        """Initialize Redis connection."""
        if redis_url is None:
            # Use environment variable or default to localhost for development
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.key_prefix = "nim:"

    def _get_key(self, nim_id: str) -> str:
        """Generate Redis key for NIM data."""
        return f"{self.key_prefix}{nim_id}"

    def set_nim_data(self, nim_id: str, host: str, port: int, nim_type: str) -> bool:
        """Set NIM data in Redis."""
        try:
            nim_data = NIMData(nim_id=nim_id, host=host, port=port, nim_type=nim_type)
            key = self._get_key(nim_id)
            self.redis_client.set(key, nim_data.model_dump_json())
            logger.info(f"Set NIM data for {nim_id}: {host}:{port} (type: {nim_type})")
            return True
        except Exception as e:
            logger.error(f"Failed to set NIM data for {nim_id}: {e}")
            return False

    def get_nim_data(self, nim_id: str) -> Optional[NIMData]:
        """Get NIM data from Redis."""
        try:
            key = self._get_key(nim_id)
            data = self.redis_client.get(key)
            if data:
                nim_data_dict = json.loads(data)
                return NIMData(**nim_data_dict)
            return None
        except Exception as e:
            logger.error(f"Failed to get NIM data for {nim_id}: {e}")
            return None

    def delete_nim_data(self, nim_id: str) -> bool:
        """Delete NIM data from Redis."""
        try:
            key = self._get_key(nim_id)
            result = self.redis_client.delete(key)
            logger.info(f"Deleted NIM data for {nim_id}")
            return bool(result)
        except Exception as e:
            logger.error(f"Failed to delete NIM data for {nim_id}: {e}")
            return False

    def list_nim_ids(self) -> list[str]:
        """List all NIM IDs in Redis."""
        try:
            pattern = f"{self.key_prefix}*"
            keys = self.redis_client.keys(pattern)
            # Extract nim_id from keys
            nim_ids = [key.replace(self.key_prefix, "") for key in keys]
            return nim_ids
        except Exception as e:
            logger.error(f"Failed to list NIM IDs: {e}")
            return []


# Global instance for use throughout the application
nim_manager = RedisNIMManager()
