"""Inference utility functions for different NIM types."""

import json
import logging
import requests
from typing import Dict, Any, Optional
from fastapi import HTTPException, status

from .llm.models import InferenceRequest
from .utils import validate_nim_exists

logger = logging.getLogger(__name__)


async def perform_image_generation_inference(
    nim_id: str,
    request_data: Dict[str, Any],
    inference_request: InferenceRequest
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

        # Use the local NIM endpoint from Redis configuration
        # Check if there's a specific endpoint in metadata, otherwise use default
        base_url = f"http://{nim_data.host}:{nim_data.port}"

        # Use the correct endpoint for local NIM instances
        invoke_url = f"{base_url}/v1/infer"

        logger.info(f"Performing image generation inference for {nim_id}")
        logger.debug(f"NIM type: {nim_data.nim_type}")
        logger.debug(f"NIM metadata: {nim_metadata}")
        logger.info(f"Invoke URL: {invoke_url}")
        logger.debug(f"Request data: {request_data}")

        # Prepare headers
        headers = {
            "accept": "application/json",
            "content-type": "application/json"
        }
        logger.debug(f"Request headers: {headers}")

        # Make the request to the NIM
        logger.debug("Making POST request to NIM")
        response = requests.post(
            invoke_url,
            json=request_data,
            headers=headers,
            timeout=60  # 60 second timeout for image generation
        )
        logger.debug(f"Response received. Status: {response.status_code}, Content-Type: {response.headers.get('content-type', 'unknown')}")

        # Check if request was successful
        if response.status_code != 200:
            error_msg = f"NIM inference failed with status {response.status_code}: {response.text}"
            logger.error(error_msg)

            # Update inference request with error
            inference_request.status = "error"
            inference_request.set_error({
                "status_code": response.status_code,
                "error": response.text,
                "nim_id": nim_id,
                "invoke_url": invoke_url
            })
            inference_request.update_timestamp()
            inference_request.save()

            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=error_msg
            )

        # Parse response
        logger.debug("Parsing response JSON")
        response_data = response.json()
        logger.debug(f"Response data keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'Not a dict'}")
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
        inference_request.set_error({
            "error": "Request timeout",
            "nim_id": nim_id,
            "timeout_seconds": 60
        })
        inference_request.update_timestamp()
        inference_request.save()

        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=error_msg
        )

    except requests.exceptions.RequestException as e:
        error_msg = f"NIM inference request failed for {nim_id}: {str(e)}"
        logger.error(error_msg)

        # Update inference request with request error
        inference_request.status = "error"
        inference_request.set_error({
            "error": str(e),
            "nim_id": nim_id,
            "error_type": "RequestException"
        })
        inference_request.update_timestamp()
        inference_request.save()

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=error_msg
        )

    except Exception as e:
        error_msg = f"Unexpected error during inference for {nim_id}: {str(e)}"
        logger.error(error_msg)

        # Update inference request with unexpected error
        inference_request.status = "error"
        inference_request.set_error({
            "error": str(e),
            "nim_id": nim_id,
            "error_type": "UnexpectedError"
        })
        inference_request.update_timestamp()
        inference_request.save()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )


async def perform_inference(
    nim_id: str,
    request_data: Dict[str, Any],
    inference_request: InferenceRequest
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
    _, nim_metadata = validate_nim_exists(nim_id)
    nim_type = nim_metadata.get('type', '').lower()

    # Route to appropriate handler based on NIM type
    if nim_type == 'image':
        return await perform_image_generation_inference(nim_id, request_data, inference_request)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"NIM type '{nim_type}' is not supported for inference"
        )
