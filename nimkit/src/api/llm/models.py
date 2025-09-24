"""LLM inference data models."""

import json
import os
from datetime import datetime
from typing import Optional, Dict, Any
from redis_om import HashModel, Field
import redis


class InferenceRequest(HashModel):
    """Inference request data model using RedisOM."""

    request_id: str = Field(..., description="Request ID (UUID)")
    input_json: str = Field(..., description="Input request data as JSON string")
    output_json: Optional[str] = Field(
        default=None, description="Output response data as JSON string"
    )
    error_json: Optional[str] = Field(
        default=None, description="Error data as JSON string"
    )
    type: str = Field(default="LLM", description="Request type")
    request_type: str = Field(
        default="chat", description="Request type: chat, completion"
    )
    nim_id: str = Field(default="", description="NIM ID used for this request")
    # deprecate
    model: str = Field(default="", description="Model name used")
    # deprecate
    stream: str = Field(
        default="false", description="Whether this was a streaming request"
    )
    date_created: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="Creation timestamp",
    )
    date_updated: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="Last update timestamp",
    )
    status: str = Field(
        default="pending", description="Request status: pending, completed, error"
    )
    audio_file_path: Optional[str] = Field(
        default=None, description="Path to uploaded audio file for ASR requests"
    )
    output_audio_path: Optional[str] = Field(
        default=None,
        description="Path to generated output audio file for speech enhancement requests",
    )
    # TODO: add field for inference duration in ms
    # TODO: add field for generated image file path
    # TODO: add field for generated 3D model file path

    class Meta:
        database = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))

    def set_input(self, data: Dict[str, Any]) -> None:
        """Set input data as JSON string."""
        self.input_json = json.dumps(data)

    def set_output(self, data: Dict[str, Any]) -> None:
        """Set output data as JSON string."""
        self.output_json = json.dumps(data)

    def set_error(self, data: Dict[str, Any]) -> None:
        """Set error data as JSON string."""
        self.error_json = json.dumps(data)

    def get_input(self) -> Dict[str, Any]:
        """Get input data as dict."""
        return json.loads(self.input_json) if self.input_json else {}

    def get_output(self) -> Dict[str, Any]:
        """Get output data as dict."""
        return json.loads(self.output_json) if self.output_json else {}

    def get_error(self) -> Dict[str, Any]:
        """Get error data as dict."""
        return json.loads(self.error_json) if self.error_json else {}

    def get_date_created(self) -> datetime:
        """Get date_created as datetime object."""
        return datetime.fromisoformat(self.date_created)

    def get_date_updated(self) -> datetime:
        """Get date_updated as datetime object."""
        return datetime.fromisoformat(self.date_updated)

    def update_timestamp(self) -> None:
        """Update the date_updated timestamp."""
        self.date_updated = datetime.utcnow().isoformat()

    def get_stream(self) -> bool:
        """Get stream as boolean."""
        return self.stream.lower() == "true"

    def set_stream(self, value: bool) -> None:
        """Set stream from boolean."""
        self.stream = str(value).lower()

    @classmethod
    def delete_by_request_id(cls, request_id: str) -> bool:
        """
        Delete an InferenceRequest by its request_id.

        Args:
            request_id: The request ID to delete

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        try:
            # Use direct Redis query since RedisOM find() seems to have issues
            # This is more reliable than the find() method
            redis_client = cls.Meta.database

            # Get all InferenceRequest keys
            pattern = ":nimkit.src.api.llm.models.InferenceRequest:*"
            keys = redis_client.keys(pattern)
            # Filter out the index key - handle both bytes and string keys
            filtered_keys = []
            for key in keys:
                if isinstance(key, bytes):
                    if not key.endswith(b":index:hash"):
                        filtered_keys.append(key)
                else:
                    if not key.endswith(":index:hash"):
                        filtered_keys.append(key)
            keys = filtered_keys

            # Find the key with matching request_id
            target_key = None
            for key in keys:
                try:
                    # Get the request_id field from the hash
                    stored_request_id = redis_client.hget(key, "request_id")
                    if (
                        stored_request_id
                        and stored_request_id.decode("utf-8") == request_id
                    ):
                        target_key = key
                        break
                except Exception:
                    continue

            if not target_key:
                return False

            # Delete the key from Redis
            result = redis_client.delete(target_key)
            return bool(result)

        except Exception as e:
            # Log the error for debugging
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"Failed to delete InferenceRequest {request_id}: {e}")
            return False
