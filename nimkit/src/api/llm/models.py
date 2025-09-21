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
    # TODO: add field for inference duration in ms
    # TODO: add field for generated image file path
    # TODO: add field for generated 3D model file path
    # TODO: add field for generated audio file path

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
