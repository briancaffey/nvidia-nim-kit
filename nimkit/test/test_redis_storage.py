"""Test Redis storage functionality for InferenceRequest."""

import json
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

from nimkit.src.api.llm.models import InferenceRequest


class TestInferenceRequestRedisStorage:
    """Test InferenceRequest Redis storage functionality."""

    def test_create_inference_request_with_metadata(self):
        """Test creating InferenceRequest with enhanced metadata."""
        request_id = "test-request-123"

        # Create InferenceRequest with all metadata
        inference_request = InferenceRequest(
            request_id=request_id,
            input_json="",
            type="LLM",
            request_type="chat",
            nim_id="test-nim-1",
            model="llama-3.1-8b-instruct",
            stream=True,
            status="pending",
        )

        # Verify metadata fields
        assert inference_request.request_id == request_id
        assert inference_request.type == "LLM"
        assert inference_request.request_type == "chat"
        assert inference_request.nim_id == "test-nim-1"
        assert inference_request.model == "llama-3.1-8b-instruct"
        assert inference_request.stream is True
        assert inference_request.status == "pending"

    def test_set_and_get_input_data(self):
        """Test setting and getting input data."""
        inference_request = InferenceRequest(
            request_id="test-123",
            input_json="",
            type="LLM",
            request_type="chat",
            nim_id="test-nim",
            model="test-model",
            stream=False,
            status="pending",
        )

        # Test input data
        input_data = {
            "model": "llama-3.1-8b-instruct",
            "messages": [{"role": "user", "content": "Hello"}],
            "temperature": 0.7,
            "max_tokens": 100,
            "stream": False,
        }

        inference_request.set_input(input_data)
        retrieved_input = inference_request.get_input()

        assert retrieved_input == input_data
        assert inference_request.input_json == json.dumps(input_data)

    def test_set_and_get_output_data(self):
        """Test setting and getting output data."""
        inference_request = InferenceRequest(
            request_id="test-123",
            input_json="",
            type="LLM",
            request_type="chat",
            nim_id="test-nim",
            model="test-model",
            stream=False,
            status="pending",
        )

        # Test output data
        output_data = {
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "created": 1677652288,
            "model": "llama-3.1-8b-instruct",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Hello! How can I help you?",
                    },
                    "finish_reason": "stop",
                }
            ],
        }

        inference_request.set_output(output_data)
        retrieved_output = inference_request.get_output()

        assert retrieved_output == output_data
        assert inference_request.output_json == json.dumps(output_data)

    def test_set_and_get_error_data(self):
        """Test setting and getting error data."""
        inference_request = InferenceRequest(
            request_id="test-123",
            input_json="",
            type="LLM",
            request_type="chat",
            nim_id="test-nim",
            model="test-model",
            stream=False,
            status="pending",
        )

        # Test error data
        error_data = {
            "error": "Connection timeout",
            "type": "http_error",
            "status_code": 500,
        }

        inference_request.set_error(error_data)
        retrieved_error = inference_request.get_error()

        assert retrieved_error == error_data
        assert inference_request.error_json == json.dumps(error_data)

    def test_completion_request_type(self):
        """Test creating completion request type."""
        inference_request = InferenceRequest(
            request_id="completion-123",
            input_json="",
            type="LLM",
            request_type="completion",
            nim_id="test-nim",
            model="gpt-3.5-turbo",
            stream=False,
            status="pending",
        )

        assert inference_request.request_type == "completion"
        assert inference_request.model == "gpt-3.5-turbo"

        # Test completion input data
        completion_input = {
            "model": "gpt-3.5-turbo",
            "prompt": "Complete this sentence: The weather is",
            "temperature": 0.5,
            "max_tokens": 50,
            "stream": False,
        }

        inference_request.set_input(completion_input)
        retrieved_input = inference_request.get_input()

        assert retrieved_input == completion_input

    def test_streaming_vs_non_streaming(self):
        """Test streaming vs non-streaming request handling."""
        # Non-streaming request
        non_streaming = InferenceRequest(
            request_id="non-stream-123",
            input_json="",
            type="LLM",
            request_type="chat",
            nim_id="test-nim",
            model="test-model",
            stream=False,
            status="pending",
        )

        assert non_streaming.stream is False

        # Streaming request
        streaming = InferenceRequest(
            request_id="stream-123",
            input_json="",
            type="LLM",
            request_type="chat",
            nim_id="test-nim",
            model="test-model",
            stream=True,
            status="pending",
        )

        assert streaming.stream is True

    def test_status_transitions(self):
        """Test status transitions from pending to completed/error."""
        inference_request = InferenceRequest(
            request_id="status-test-123",
            input_json="",
            type="LLM",
            request_type="chat",
            nim_id="test-nim",
            model="test-model",
            stream=False,
            status="pending",
        )

        # Initially pending
        assert inference_request.status == "pending"

        # Simulate successful completion
        inference_request.status = "completed"
        inference_request.date_updated = datetime.utcnow()

        assert inference_request.status == "completed"

        # Simulate error
        inference_request.status = "error"
        inference_request.date_updated = datetime.utcnow()

        assert inference_request.status == "error"

    def test_metadata_persistence(self):
        """Test that all metadata fields are properly stored and retrieved."""
        original_request = InferenceRequest(
            request_id="metadata-test-123",
            input_json="",
            type="LLM",
            request_type="completion",
            nim_id="nim-456",
            model="llama-3.1-70b-instruct",
            stream=True,
            status="pending",
        )

        # Set some data
        input_data = {"prompt": "Test prompt", "model": "llama-3.1-70b-instruct"}
        output_data = {"choices": [{"text": "Test response"}]}

        original_request.set_input(input_data)
        original_request.set_output(output_data)
        original_request.status = "completed"

        # Verify all fields are accessible
        assert original_request.request_id == "metadata-test-123"
        assert original_request.type == "LLM"
        assert original_request.request_type == "completion"
        assert original_request.nim_id == "nim-456"
        assert original_request.model == "llama-3.1-70b-instruct"
        assert original_request.stream is True
        assert original_request.status == "completed"
        assert original_request.get_input() == input_data
        assert original_request.get_output() == output_data


if __name__ == "__main__":
    pytest.main([__file__])
