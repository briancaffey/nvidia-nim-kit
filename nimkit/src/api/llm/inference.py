"""LLM inference API endpoints."""

import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

import httpx
from fastapi import APIRouter, HTTPException, Depends, Response, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, validator

from nimkit.src.api.llm.models import InferenceRequest
from nimkit.src.api.config.nims import nim_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/llm", tags=["llm"])


class InferenceRequestBody(BaseModel):
    """Request body for inference endpoint - matches OpenAI API spec."""

    model: str
    messages: list[Dict[str, str]]
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    stream: Optional[bool] = False
    logprobs: Optional[bool] = False
    top_logprobs: Optional[int] = None

    @validator("top_logprobs")
    def validate_top_logprobs(cls, v, values):
        if v is not None:
            if v < 1 or v > 10:
                raise ValueError("top_logprobs must be between 1 and 10")
            if not values.get("logprobs", False):
                raise ValueError("top_logprobs can only be set when logprobs is True")
        return v


class CompletionRequestBody(BaseModel):
    """Request body for completion endpoint - matches OpenAI API spec."""

    model: str
    prompt: str
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    stream: Optional[bool] = False
    logprobs: Optional[bool] = False
    top_logprobs: Optional[int] = None

    @validator("top_logprobs")
    def validate_top_logprobs(cls, v, values):
        if v is not None:
            if v < 1 or v > 10:
                raise ValueError("top_logprobs must be between 1 and 10")
            if not values.get("logprobs", False):
                raise ValueError("top_logprobs can only be set when logprobs is True")
        return v


async def get_nim_endpoint(nim_id: str) -> str:
    """Get NIM endpoint URL for the given NIM ID."""
    nim_data = nim_manager.get_nim_data(nim_id)
    if not nim_data:
        raise HTTPException(status_code=404, detail=f"NIM {nim_id} not found")
    return f"http://{nim_data.host}:{nim_data.port}"


@router.post("/inference")
async def inference(
    request_body: InferenceRequestBody,
    nim_id: str = Query(..., description="NIM instance ID"),
    nim_endpoint: str = Depends(get_nim_endpoint),
):
    """Proxy inference request to NIM and save response."""

    # Generate UUID for the request
    request_id = str(uuid.uuid4())

    logger.info(f"Starting inference request {request_id} for NIM {nim_id}")
    logger.info(f"NIM endpoint: {nim_endpoint}")
    logger.info(f"Request body: {request_body.model_dump()}")

    # Create InferenceRequest record with enhanced metadata
    inference_request = InferenceRequest(
        request_id=request_id,
        input_json="",  # Initialize as empty string
        type="LLM",
        request_type="chat",
        nim_id=nim_id,
        model=request_body.model,
        stream=str(request_body.stream or False).lower(),
        status="pending",
    )
    inference_request.set_input(request_body.model_dump())
    inference_request.save()

    logger.info(
        f"Saved inference request {request_id} to Redis with metadata: "
        f"nim_id={nim_id}, model={request_body.model}, stream={request_body.stream}"
    )

    try:
        # Prepare request for NIM
        nim_request_data = request_body.model_dump()

        # Fix logprobs format for NIM service
        # Chat completions expects logprobs as boolean, completions expects it as integer
        if nim_request_data.get("logprobs") is True:
            # For chat completions, keep logprobs as True and add top_logprobs
            nim_request_data["top_logprobs"] = request_body.top_logprobs or 1
        elif nim_request_data.get("logprobs") is False:
            nim_request_data.pop("logprobs", None)
            nim_request_data.pop("top_logprobs", None)

        # Ensure upstream is asked to stream if client requested it
        if request_body.stream:
            nim_request_data["stream"] = True

        logger.info(f"Sending request to NIM: {nim_request_data}")

        # Make request to NIM
        if request_body.stream:
            logger.info("Processing streaming response")

            async def stream_generator():
                all_chunks = []
                try:
                    # Optional: send an SSE comment to open the pipe quickly
                    yield ": ping\n\n"

                    # IMPORTANT: use streaming request, NOT client.post(...)
                    async with httpx.AsyncClient(timeout=None) as client:
                        async with client.stream(
                            "POST",
                            f"{nim_endpoint}/v1/chat/completions",
                            json=nim_request_data,
                            headers={
                                "Content-Type": "application/json",
                                "Accept": "text/event-stream",
                            },
                        ) as response:
                            logger.info(f"NIM response status: {response.status_code}")
                            logger.info(
                                f"NIM response headers: {dict(response.headers)}"
                            )
                            response.raise_for_status()

                            async for line in response.aiter_lines():
                                # httpx yields as soon as data arrives
                                if line is None:
                                    continue
                                if line == "":
                                    # keep-alive heartbeat; propagate to client
                                    yield "\n"
                                    continue

                                # Forward the line as-is to the client (SSE requires \n\n between events)
                                yield f"{line}\n"

                                # Save parsed chunks for DB (non-blocking parsing)
                                if line.startswith("data: "):
                                    data_content = line[6:]
                                    if data_content.strip() == "[DONE]":
                                        continue
                                    try:
                                        chunk_data = json.loads(data_content)
                                        all_chunks.append(chunk_data)
                                    except json.JSONDecodeError:
                                        logger.warning(
                                            f"Failed to parse chunk: {data_content}"
                                        )

                    # Store after stream completes
                    response_data = {
                        "chunks": all_chunks,
                        "total_chunks": len(all_chunks),
                        "streaming": True,
                    }
                    inference_request.set_output(response_data)
                    inference_request.status = "completed"
                    inference_request.update_timestamp()
                    inference_request.save()
                    logger.info(
                        f"Saved streaming response with {len(all_chunks)} chunks "
                        f"for request {request_id}"
                    )
                except Exception as e:
                    logger.error(f"Failed to process streaming response: {e}")
                    error_data = {"error": str(e), "type": "streaming_error"}
                    inference_request.set_error(error_data)
                    inference_request.status = "error"
                    inference_request.update_timestamp()
                    inference_request.save()

            # Proper SSE response & headers to prevent buffering
            return StreamingResponse(
                stream_generator(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",  # nginx
                },
            )
        else:
            # Non-streaming path
            async with httpx.AsyncClient(timeout=30.0) as client:
                logger.info("Processing non-streaming response")
                # Non-streaming path (unchanged except larger timeout)
                response = await client.post(
                    f"{nim_endpoint}/v1/chat/completions",
                    json=nim_request_data,
                    headers={"Content-Type": "application/json"},
                )
                logger.info(f"NIM response status: {response.status_code}")
                logger.info(f"NIM response headers: {dict(response.headers)}")
                response.raise_for_status()
                response_data = response.json()

                inference_request.set_output(response_data)
                inference_request.status = "completed"
                inference_request.update_timestamp()
                inference_request.save()

                logger.info(f"Inference request {request_id} completed successfully")
                return response_data

    except httpx.HTTPError as e:
        logger.error(f"HTTP error for request {request_id}: {e}")
        logger.error(
            f"Response status: {e.response.status_code if hasattr(e, 'response') else 'Unknown'}"
        )
        logger.error(
            f"Response text: {e.response.text if hasattr(e, 'response') and e.response else 'Unknown'}"
        )

        error_data = {"error": str(e), "type": "http_error"}
        inference_request.set_error(error_data)
        inference_request.status = "error"
        inference_request.update_timestamp()
        inference_request.save()

        logger.error(f"Inference request {request_id} failed with HTTP error: {e}")
        raise HTTPException(status_code=500, detail=f"NIM request failed: {str(e)}")

    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error for request {request_id}: {e}")
        logger.error(
            f"Raw response that failed to parse: {getattr(e, 'doc', 'Unknown')}"
        )

        error_data = {"error": f"JSON decode error: {str(e)}", "type": "json_error"}
        inference_request.set_error(error_data)
        inference_request.status = "error"
        inference_request.update_timestamp()
        inference_request.save()

        logger.error(
            f"Inference request {request_id} failed with JSON decode error: {e}"
        )
        raise HTTPException(status_code=500, detail=f"JSON decode error: {str(e)}")

    except Exception as e:
        logger.error(f"Unexpected error for request {request_id}: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")

        error_data = {"error": str(e), "type": "internal_error"}
        inference_request.set_error(error_data)
        inference_request.status = "error"
        inference_request.update_timestamp()
        inference_request.save()

        logger.error(f"Inference request {request_id} failed with internal error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.post("/completion")
async def completion(
    request_body: CompletionRequestBody,
    nim_id: str = Query(..., description="NIM instance ID"),
    nim_endpoint: str = Depends(get_nim_endpoint),
):
    """Proxy completion request to NIM and save response."""

    # Generate UUID for the request
    request_id = str(uuid.uuid4())

    logger.info(f"Starting completion request {request_id} for NIM {nim_id}")
    logger.info(f"NIM endpoint: {nim_endpoint}")
    logger.info(f"Request body: {request_body.model_dump()}")

    # Create InferenceRequest record with enhanced metadata
    inference_request = InferenceRequest(
        request_id=request_id,
        input_json="",  # Initialize as empty string
        type="LLM",
        request_type="completion",
        nim_id=nim_id,
        model=request_body.model,
        stream=str(request_body.stream or False).lower(),
        status="pending",
    )
    inference_request.set_input(request_body.model_dump())
    inference_request.save()

    logger.info(
        f"Saved completion request {request_id} to Redis with metadata: "
        f"nim_id={nim_id}, model={request_body.model}, stream={request_body.stream}"
    )

    try:
        # Prepare request for NIM
        nim_request_data = request_body.model_dump()

        # Fix logprobs format for NIM service
        if nim_request_data.get("logprobs") is True:
            nim_request_data["logprobs"] = request_body.top_logprobs or 1
        elif nim_request_data.get("logprobs") is False:
            nim_request_data.pop("logprobs", None)
            nim_request_data.pop("top_logprobs", None)

        # Ensure upstream is asked to stream if client requested it
        if request_body.stream:
            nim_request_data["stream"] = True

        logger.info(f"Sending completion request to NIM: {nim_request_data}")

        # Make request to NIM
        if request_body.stream:
            logger.info("Processing streaming completion response")

            async def stream_generator():
                all_chunks = []
                try:
                    # Optional: send an SSE comment to open the pipe quickly
                    yield ": ping\n\n"

                    # IMPORTANT: use streaming request, NOT client.post(...)
                    async with httpx.AsyncClient(timeout=None) as client:
                        async with client.stream(
                            "POST",
                            f"{nim_endpoint}/v1/completions",
                            json=nim_request_data,
                            headers={
                                "Content-Type": "application/json",
                                "Accept": "text/event-stream",
                            },
                        ) as response:
                            logger.info(f"NIM response status: {response.status_code}")
                            logger.info(f"NIM response headers: {dict(response.headers)}")
                            response.raise_for_status()

                            async for line in response.aiter_lines():
                                # httpx yields as soon as data arrives
                                if line is None:
                                    continue
                                if line == "":
                                    # keep-alive heartbeat; propagate to client
                                    yield "\n"
                                    continue

                                # Forward the line as-is to the client (SSE requires \n\n between events)
                                yield f"{line}\n"

                                # Save parsed chunks for DB (non-blocking parsing)
                                if line.startswith("data: "):
                                    data_content = line[6:]
                                    if data_content.strip() == "[DONE]":
                                        continue
                                    try:
                                        chunk_data = json.loads(data_content)
                                        all_chunks.append(chunk_data)
                                    except json.JSONDecodeError:
                                        logger.warning(f"Failed to parse chunk: {data_content}")

                    # Store after stream completes
                    response_data = {
                        "chunks": all_chunks,
                        "total_chunks": len(all_chunks),
                        "streaming": True,
                    }
                    inference_request.set_output(response_data)
                    inference_request.status = "completed"
                    inference_request.update_timestamp()
                    inference_request.save()
                    logger.info(
                        f"Saved streaming completion response with {len(all_chunks)} chunks "
                        f"for request {request_id}"
                    )
                except Exception as e:
                    logger.error(f"Failed to process streaming completion response: {e}")
                    error_data = {"error": str(e), "type": "streaming_error"}
                    inference_request.set_error(error_data)
                    inference_request.status = "error"
                    inference_request.update_timestamp()
                    inference_request.save()

            # Proper SSE response & headers to prevent buffering
            return StreamingResponse(
                stream_generator(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",  # nginx
                },
            )
        else:
            # Non-streaming path
            async with httpx.AsyncClient(timeout=30.0) as client:
                logger.info("Processing non-streaming completion response")
                response = await client.post(
                    f"{nim_endpoint}/v1/completions",
                    json=nim_request_data,
                    headers={"Content-Type": "application/json"},
                )
                logger.info(f"NIM response status: {response.status_code}")
                logger.info(f"NIM response headers: {dict(response.headers)}")
                response.raise_for_status()
                response_data = response.json()
                logger.info(f"Parsed completion response data: {response_data}")

                inference_request.set_output(response_data)
                inference_request.status = "completed"
                inference_request.update_timestamp()
                inference_request.save()

                logger.info(f"Completion request {request_id} completed successfully")
                return response_data

    except httpx.HTTPError as e:
        logger.error(f"HTTP error for completion request {request_id}: {e}")
        logger.error(
            f"Response status: {e.response.status_code if hasattr(e, 'response') else 'Unknown'}"
        )
        logger.error(
            f"Response text: {e.response.text if hasattr(e, 'response') and e.response else 'Unknown'}"
        )

        error_data = {"error": str(e), "type": "http_error"}
        inference_request.set_error(error_data)
        inference_request.status = "error"
        inference_request.update_timestamp()
        inference_request.save()

        logger.error(f"Completion request {request_id} failed with HTTP error: {e}")
        raise HTTPException(status_code=500, detail=f"NIM request failed: {str(e)}")

    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error for completion request {request_id}: {e}")
        logger.error(
            f"Raw response that failed to parse: {getattr(e, 'doc', 'Unknown')}"
        )

        error_data = {"error": f"JSON decode error: {str(e)}", "type": "json_error"}
        inference_request.set_error(error_data)
        inference_request.status = "error"
        inference_request.update_timestamp()
        inference_request.save()

        logger.error(
            f"Completion request {request_id} failed with JSON decode error: {e}"
        )
        raise HTTPException(status_code=500, detail=f"JSON decode error: {str(e)}")

    except Exception as e:
        logger.error(f"Unexpected error for completion request {request_id}: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")

        error_data = {"error": str(e), "type": "internal_error"}
        inference_request.set_error(error_data)
        inference_request.status = "error"
        inference_request.update_timestamp()
        inference_request.save()

        logger.error(f"Completion request {request_id} failed with internal error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/inference/{request_id}")
async def get_inference_request(request_id: str) -> Dict[str, Any]:
    """Get inference request by ID."""
    try:
        # Find the request by request_id since RedisOM uses its own pk system
        all_requests = list(InferenceRequest.all_pks())
        inference_request = None

        for pk in all_requests:
            try:
                req = InferenceRequest.get(pk)
                if req.request_id == request_id:
                    inference_request = req
                    break
            except Exception:
                continue

        if not inference_request:
            raise HTTPException(status_code=404, detail="Inference request not found")

        return {
            "id": inference_request.request_id,
            "input": inference_request.get_input(),
            "output": inference_request.get_output(),
            "error": inference_request.get_error(),
            "type": inference_request.type,
            "request_type": inference_request.request_type,
            "nim_id": inference_request.nim_id,
            "model": inference_request.model,
            "stream": inference_request.get_stream(),
            "status": inference_request.status,
            "date_created": inference_request.date_created,
            "date_updated": inference_request.date_updated,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get inference request {request_id}: {e}")
        raise HTTPException(status_code=404, detail="Inference request not found")


@router.post("/debug-streaming")
async def debug_streaming(
    nim_id: str = Query(..., description="NIM instance ID"),
    nim_endpoint: str = Depends(get_nim_endpoint),
) -> Dict[str, Any]:
    """Debug endpoint to test streaming responses directly from NIM."""
    logger.info(f"Debug streaming test for NIM {nim_id} at {nim_endpoint}")

    # Simple test request
    test_request = {
        "model": "llama-3.1-8b-instruct",
        "messages": [{"role": "user", "content": "Hello, how are you?"}],
        "stream": True,
        "max_tokens": 50,
    }

    logger.info(f"Sending test request: {test_request}")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{nim_endpoint}/v1/chat/completions",
                json=test_request,
                headers={"Content-Type": "application/json"},
            )

            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")

            response.raise_for_status()

            # Collect the streaming response
            response_text = ""
            chunk_count = 0
            async for chunk in response.aiter_text():
                chunk_count += 1
                logger.info(f"Chunk {chunk_count}: {repr(chunk)}")
                response_text += chunk

            logger.info(f"Total chunks received: {chunk_count}")
            logger.info(f"Complete response: {repr(response_text)}")

            return {
                "status": "success",
                "chunk_count": chunk_count,
                "response_text": response_text,
                "response_length": len(response_text),
            }

    except Exception as e:
        logger.error(f"Debug streaming failed: {e}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        return {"status": "error", "error": str(e), "error_type": type(e).__name__}


@router.get("/requests")
async def list_inference_requests(
    request_type: Optional[str] = None,
    nim_id: Optional[str] = None,
    status: Optional[str] = None,
    type: Optional[str] = None,
    limit: int = 100,
) -> Dict[str, Any]:
    """List inference requests with optional filtering."""
    try:
        # Get all inference requests
        all_requests = list(InferenceRequest.all_pks())

        # Apply filters and collect all valid requests
        filtered_requests = []
        for pk in all_requests:
            try:
                request = InferenceRequest.get(pk)

                # Apply filters
                if request_type and request.request_type != request_type:
                    continue
                if nim_id and request.nim_id != nim_id:
                    continue
                if status and request.status != status:
                    continue
                if type and request.type != type:
                    continue

                filtered_requests.append(
                    {
                        "id": request.request_id,
                        "request_type": request.request_type,
                        "nim_id": request.nim_id,
                        "model": request.model,
                        "stream": request.get_stream(),
                        "status": request.status,
                        "date_created": request.date_created,
                        "date_updated": request.date_updated,
                        "input": request.get_input(),
                        "output": request.get_output(),
                        "error": request.get_error(),
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to get request {pk}: {e}")
                continue

        # Sort by date_created in descending order (newest first)
        filtered_requests.sort(key=lambda x: x["date_created"], reverse=True)

        # Apply limit after sorting
        limited_requests = filtered_requests[:limit]

        return {
            "requests": limited_requests,
            "total": len(filtered_requests),  # Total before limiting
            "filters": {
                "request_type": request_type,
                "nim_id": nim_id,
                "status": status,
                "type": type,
                "limit": limit,
            },
        }
    except Exception as e:
        logger.error(f"Failed to list inference requests: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to list requests: {str(e)}"
        )


@router.delete("/inference/{request_id}")
async def delete_inference_request(request_id: str) -> Dict[str, Any]:
    """Delete inference request by ID."""
    try:
        # Find the request by request_id since RedisOM uses its own pk system
        all_requests = list(InferenceRequest.all_pks())
        inference_request = None
        request_pk = None

        for pk in all_requests:
            try:
                req = InferenceRequest.get(pk)
                if req.request_id == request_id:
                    inference_request = req
                    request_pk = pk
                    break
            except Exception:
                continue

        if not inference_request:
            raise HTTPException(status_code=404, detail="Inference request not found")

        # Delete the request from Redis
        inference_request.delete(request_pk)

        logger.info(f"Successfully deleted inference request {request_id}")

        return {
            "message": "Inference request deleted successfully",
            "request_id": request_id,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete inference request {request_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to delete request: {str(e)}"
        )


@router.get("/requests/stats")
async def get_inference_stats() -> Dict[str, Any]:
    """Get statistics about inference requests."""
    try:
        all_requests = list(InferenceRequest.all_pks())

        stats = {
            "total_requests": len(all_requests),
            "by_type": {"chat": 0, "completion": 0},
            "by_status": {"pending": 0, "completed": 0, "error": 0},
            "by_nim": {},
            "streaming_vs_non_streaming": {"streaming": 0, "non_streaming": 0},
        }

        for pk in all_requests:
            try:
                request = InferenceRequest.get(pk)

                # Count by type
                if request.request_type in stats["by_type"]:
                    stats["by_type"][request.request_type] += 1

                # Count by status
                if request.status in stats["by_status"]:
                    stats["by_status"][request.status] += 1

                # Count by NIM
                if request.nim_id:
                    if request.nim_id not in stats["by_nim"]:
                        stats["by_nim"][request.nim_id] = 0
                    stats["by_nim"][request.nim_id] += 1

                # Count streaming vs non-streaming
                if request.get_stream():
                    stats["streaming_vs_non_streaming"]["streaming"] += 1
                else:
                    stats["streaming_vs_non_streaming"]["non_streaming"] += 1

            except Exception as e:
                logger.warning(f"Failed to get request {pk} for stats: {e}")
                continue

        return stats
    except Exception as e:
        logger.error(f"Failed to get inference stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")
