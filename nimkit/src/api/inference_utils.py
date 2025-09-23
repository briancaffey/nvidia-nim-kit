"""Inference utility functions for different NIM types."""

import json
import logging
import os
import base64
import requests
from typing import Dict, Any, Optional
from fastapi import HTTPException, status

from .llm.models import InferenceRequest
from .utils import get_nvidia_api_headers, validate_nim_exists

logger = logging.getLogger(__name__)


async def process_glb_artifacts(response_data: Dict[str, Any], request_id: str) -> None:
    """
    Process GLB artifacts from Trellis response and save them to the media folder.

    Args:
        response_data: The response data containing artifacts
        request_id: The inference request ID to use as filename
    """
    try:
        logger.info(f"Processing GLB artifacts for request {request_id}")

        # Create media/models directory if it doesn't exist
        media_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "media"
        )
        models_dir = os.path.join(media_dir, "models")
        os.makedirs(models_dir, exist_ok=True)
        logger.debug(f"Created models directory: {models_dir}")

        artifacts = response_data.get("artifacts", [])
        if not artifacts:
            logger.warning("No artifacts found in response")
            return

        # Process the first artifact (there should only be one)
        artifact = artifacts[0]
        base64_data = artifact.get("base64")

        if not base64_data:
            logger.warning("No base64 data found in artifact")
            return

        # Log artifact info without logging the full base64 string
        logger.info(
            f"Processing artifact with finish reason: {artifact.get('finishReason', 'unknown')}"
        )
        logger.info(f"Base64 data length: {len(base64_data)} characters")

        # Decode base64 data
        logger.debug("Decoding base64 GLB data")
        try:
            glb_data = base64.b64decode(base64_data)
            logger.info(f"Successfully decoded GLB data, size: {len(glb_data)} bytes")
        except Exception as decode_error:
            logger.error(f"Failed to decode base64 data: {decode_error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to decode GLB data from base64",
            )

        # Save GLB file
        glb_filename = f"{request_id}.glb"
        glb_path = os.path.join(models_dir, glb_filename)

        logger.info(f"Saving GLB file to: {glb_path}")
        try:
            with open(glb_path, "wb") as f:
                f.write(glb_data)
            logger.info(f"Successfully saved GLB file: {glb_filename}")
        except Exception as save_error:
            logger.error(f"Failed to save GLB file: {save_error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save GLB file: {str(save_error)}",
            )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing GLB artifacts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process GLB artifacts: {str(e)}",
        )


async def perform_image_generation_inference(
    nim_id: str,
    request_data: Dict[str, Any],
    inference_request: InferenceRequest,
    use_nvidia_api: bool = False,
) -> Dict[str, Any]:
    """
    Perform image generation inference for a NIM.

    Args:
        nim_id: The NIM ID in format 'publisher/model_name'
        request_data: The request payload from the frontend
        inference_request: The InferenceRequest object to update

    Returns:
        The response data from the NIM

    Raises:
        HTTPException: If inference fails
    """
    try:
        # Validate NIM exists and get configuration
        nim_data, nim_metadata = validate_nim_exists(nim_id)

        if use_nvidia_api:
            # Use NVIDIA API endpoint
            invoke_url = nim_metadata.get("invoke_url")
            if not invoke_url:
                raise HTTPException(
                    status_code=400,
                    detail=f"NVIDIA API invoke_url not found for NIM {nim_id}",
                )

            # For NVIDIA API, the invoke_url is already the complete endpoint
            # No need to append additional paths

            headers = get_nvidia_api_headers()
        else:
            # Use the local NIM endpoint from Redis configuration
            base_url = f"http://{nim_data.host}:{nim_data.port}"
            invoke_url = f"{base_url}/v1/infer"

            # Prepare headers for local NIM
            headers = {"accept": "application/json", "content-type": "application/json"}

        logger.info(f"Performing image generation inference for {nim_id}")
        logger.debug(f"NIM type: {nim_data.nim_type}")
        logger.debug(f"NIM metadata: {nim_metadata}")
        logger.info(f"Invoke URL: {invoke_url}")
        logger.debug(f"Request data: {request_data}")
        logger.debug(f"Request headers: {headers}")

        # Make the request to the NIM
        logger.debug("Making POST request to NIM")
        response = requests.post(
            invoke_url,
            json=request_data,
            headers=headers,
            timeout=300,  # 5 minute timeout for image generation (NVIDIA API can be slow)
        )
        logger.debug(
            f"Response received. Status: {response.status_code}, Content-Type: {response.headers.get('content-type', 'unknown')}"
        )

        # Check if request was successful
        if response.status_code != 200:
            error_msg = f"NIM inference failed with status {response.status_code}: {response.text}"
            logger.error(error_msg)

            # Update inference request with error
            inference_request.status = "error"
            inference_request.set_error(
                {
                    "status_code": response.status_code,
                    "error": response.text,
                    "nim_id": nim_id,
                    "invoke_url": invoke_url,
                }
            )
            inference_request.update_timestamp()
            inference_request.save()

            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY, detail=error_msg
            )

        # Parse response
        logger.debug("Parsing response JSON")
        response_data = response.json()
        logger.debug(
            f"Response data keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'Not a dict'}"
        )
        logger.info(f"Image generation inference successful for {nim_id}")

        # Update inference request with success
        logger.debug("Updating InferenceRequest with success status")
        inference_request.status = "completed"
        inference_request.set_output(response_data)
        inference_request.update_timestamp()
        try:
            inference_request.save()
            logger.debug("InferenceRequest updated and saved successfully")
        except Exception as save_error:
            logger.error(f"Failed to save updated InferenceRequest: {save_error}")
            logger.error(f"Save error type: {type(save_error).__name__}")
            # Don't raise here, just log the error

        return response_data

    except requests.exceptions.Timeout:
        error_msg = f"NIM inference timeout for {nim_id}"
        logger.error(error_msg)

        # Update inference request with timeout error
        inference_request.status = "error"
        inference_request.set_error(
            {"error": "Request timeout", "nim_id": nim_id, "timeout_seconds": 300}
        )
        inference_request.update_timestamp()
        inference_request.save()

        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=error_msg
        )

    except requests.exceptions.RequestException as e:
        error_msg = f"NIM inference request failed for {nim_id}: {str(e)}"
        logger.error(error_msg)

        # Update inference request with request error
        inference_request.status = "error"
        inference_request.set_error(
            {"error": str(e), "nim_id": nim_id, "error_type": "RequestException"}
        )
        inference_request.update_timestamp()
        inference_request.save()

        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=error_msg)

    except Exception as e:
        error_msg = f"Unexpected error during inference for {nim_id}: {str(e)}"
        logger.error(error_msg)

        # Update inference request with unexpected error
        inference_request.status = "error"
        inference_request.set_error(
            {"error": str(e), "nim_id": nim_id, "error_type": "UnexpectedError"}
        )
        inference_request.update_timestamp()
        inference_request.save()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_msg
        )


async def perform_3d_generation_inference(
    nim_id: str,
    request_data: Dict[str, Any],
    inference_request: InferenceRequest,
    use_nvidia_api: bool = False,
) -> Dict[str, Any]:
    """
    Perform 3D model generation inference for a NIM (e.g., Trellis).

    Args:
        nim_id: The NIM ID in format 'publisher/model_name'
        request_data: The request payload from the frontend
        inference_request: The InferenceRequest object to update
        use_nvidia_api: Whether to use NVIDIA API instead of local NIM

    Returns:
        The response data from the NIM

    Raises:
        HTTPException: If inference fails
    """
    try:
        # Validate NIM exists and get configuration
        nim_data, nim_metadata = validate_nim_exists(nim_id)

        if use_nvidia_api:
            # Use NVIDIA API endpoint
            invoke_url = nim_metadata.get("invoke_url")
            if not invoke_url:
                raise HTTPException(
                    status_code=400,
                    detail=f"NVIDIA API invoke_url not found for NIM {nim_id}",
                )

            headers = get_nvidia_api_headers()
        else:
            # Use the local NIM endpoint from Redis configuration
            base_url = f"http://{nim_data.host}:{nim_data.port}"
            invoke_url = f"{base_url}/v1/infer"

            # Prepare headers for local NIM
            headers = {"accept": "application/json", "content-type": "application/json"}

        logger.info(f"Performing 3D model generation inference for {nim_id}")
        logger.debug(f"NIM type: {nim_data.nim_type}")
        logger.debug(f"NIM metadata: {nim_metadata}")
        logger.info(f"Invoke URL: {invoke_url}")
        logger.debug(f"Request data keys: {list(request_data.keys())}")
        logger.debug(f"Request data values: {request_data}")
        logger.debug(f"Request headers: {headers}")

        # Log the exact payload being sent
        logger.info(
            f"Sending payload to Trellis NIM: {json.dumps(request_data, indent=2)}"
        )

        # Make the request to the NIM
        logger.debug("Making POST request to NIM")
        response = requests.post(
            invoke_url,
            json=request_data,
            headers=headers,
            timeout=600,  # 10 minute timeout for 3D generation (can be slow)
        )
        logger.debug(
            f"Response received. Status: {response.status_code}, Content-Type: {response.headers.get('content-type', 'unknown')}"
        )

        # Check if request was successful
        if response.status_code != 200:
            error_msg = f"NIM inference failed with status {response.status_code}: {response.text}"
            logger.error(error_msg)

            # Update inference request with error
            inference_request.status = "error"
            inference_request.set_error(
                {
                    "status_code": response.status_code,
                    "error": response.text,
                    "nim_id": nim_id,
                    "invoke_url": invoke_url,
                }
            )
            inference_request.update_timestamp()
            inference_request.save()

            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY, detail=error_msg
            )

        # Parse response
        logger.debug("Parsing response JSON")
        response_data = response.json()
        logger.debug(
            f"Response data keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'Not a dict'}"
        )
        logger.info(f"3D model generation inference successful for {nim_id}")

        # Process GLB file if present in artifacts
        if "artifacts" in response_data and response_data["artifacts"]:
            logger.info("Processing GLB artifacts from response")
            await process_glb_artifacts(response_data, inference_request.request_id)

        # Update inference request with success
        logger.debug("Updating InferenceRequest with success status")
        inference_request.status = "completed"
        inference_request.set_output(response_data)
        inference_request.update_timestamp()
        try:
            inference_request.save()
            logger.debug("InferenceRequest updated and saved successfully")
        except Exception as save_error:
            logger.error(f"Failed to save updated InferenceRequest: {save_error}")
            logger.error(f"Save error type: {type(save_error).__name__}")
            # Don't raise here, just log the error

        return response_data

    except requests.exceptions.Timeout:
        error_msg = f"NIM inference timeout for {nim_id}"
        logger.error(error_msg)

        # Update inference request with timeout error
        inference_request.status = "error"
        inference_request.set_error(
            {"error": "Request timeout", "nim_id": nim_id, "timeout_seconds": 600}
        )
        inference_request.update_timestamp()
        inference_request.save()

        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=error_msg
        )

    except requests.exceptions.RequestException as e:
        error_msg = f"NIM inference request failed for {nim_id}: {str(e)}"
        logger.error(error_msg)

        # Update inference request with request error
        inference_request.status = "error"
        inference_request.set_error(
            {"error": str(e), "nim_id": nim_id, "error_type": "RequestException"}
        )
        inference_request.update_timestamp()
        inference_request.save()

        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=error_msg)

    except Exception as e:
        error_msg = f"Unexpected error during inference for {nim_id}: {str(e)}"
        logger.error(error_msg)

        # Update inference request with unexpected error
        inference_request.status = "error"
        inference_request.set_error(
            {"error": str(e), "nim_id": nim_id, "error_type": "UnexpectedError"}
        )
        inference_request.update_timestamp()
        inference_request.save()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_msg
        )


async def perform_inference(
    nim_id: str,
    request_data: Dict[str, Any],
    inference_request: InferenceRequest,
    use_nvidia_api: bool = False,
) -> Dict[str, Any]:
    """
    Generic inference function that routes to appropriate handler based on NIM type.

    Args:
        nim_id: The NIM ID in format 'publisher/model_name'
        request_data: The request payload from the frontend
        inference_request: The InferenceRequest object to update

    Returns:
        The response data from the NIM
    """
    # Get NIM metadata to determine type
    nim_data, nim_metadata = validate_nim_exists(nim_id)

    # Get NIM type from metadata (YAML) first, fallback to Redis config
    nim_type = nim_metadata.get("type", "").lower()
    if not nim_type:
        # Fallback to Redis config nim_type
        nim_type = getattr(nim_data, "nim_type", "").lower()

    logger.debug(
        f"Determined NIM type: {nim_type} (from metadata: {nim_metadata.get('type', '')}, from Redis: {getattr(nim_data, 'nim_type', '')})"
    )

    # Route to appropriate handler based on NIM type
    if nim_type == "image":
        return await perform_image_generation_inference(
            nim_id, request_data, inference_request, use_nvidia_api
        )
    elif nim_type == "3d":
        return await perform_3d_generation_inference(
            nim_id, request_data, inference_request, use_nvidia_api
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"NIM type '{nim_type}' is not supported for inference",
        )
