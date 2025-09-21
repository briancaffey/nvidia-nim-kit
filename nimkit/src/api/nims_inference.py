"""NIM inference API endpoints."""

import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel

from .llm.models import InferenceRequest
from .utils import validate_nim_exists
from .inference_utils import perform_inference

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v0/nims", tags=["nims-inference"])


class ImageGenerationRequest(BaseModel):
    """Request body for image generation."""

    prompt: str
    height: int = 1024
    width: int = 1024
    cfg_scale: float = 0
    mode: str = "base"
    image: str = None
    samples: int = 1
    seed: int = 0
    steps: int = 4


@router.post("/{publisher}/{model_name}")
async def nim_inference(
    publisher: str,
    model_name: str,
    request_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Perform inference on a specific NIM.

    Args:
        publisher: The publisher/namespace of the NIM
        model_name: The model name
        request_data: The request payload from the frontend

    Returns:
        Serialized InferenceRequest object with all related data
    """
    # Form the NIM ID from publisher and model name
    nim_id = f"{publisher}/{model_name}"

    logger.info(f"Starting inference request for NIM: {nim_id}")
    logger.info(f"Request data: {request_data}")

    try:
        logger.debug(f"Validating NIM exists for: {nim_id}")
        # Validate NIM exists
        nim_data, nim_metadata = validate_nim_exists(nim_id)
        logger.debug(f"NIM validation successful. Host: {nim_data.host}, Port: {nim_data.port}, Type: {nim_data.nim_type}")

        # Generate UUID for the request
        request_id = str(uuid.uuid4())
        logger.debug(f"Generated request ID: {request_id}")

        # Create InferenceRequest record
        logger.debug("Creating InferenceRequest record")
        inference_request = InferenceRequest(
            request_id=request_id,
            input_json="",  # Initialize as empty string
            type="IMAGE_GENERATION",
            request_type="image_generation",
            nim_id=nim_id,
            model=model_name,
            stream="false",
            status="pending",
        )

        # Set input data
        logger.debug("Setting input data and saving InferenceRequest")
        inference_request.set_input(request_data)
        try:
            inference_request.save()
            logger.debug("InferenceRequest saved successfully")
        except Exception as save_error:
            logger.error(f"Failed to save InferenceRequest: {save_error}")
            logger.error(f"Save error type: {type(save_error).__name__}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save inference request: {str(save_error)}"
            )

        logger.info(f"Created inference request {request_id} for NIM {nim_id}")

        # Perform inference
        logger.debug("Starting inference process")
        response_data = await perform_inference(nim_id, request_data, inference_request)
        logger.debug(f"Inference completed successfully. Response data keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'Not a dict'}")

        # Use the inference_request object that was updated by perform_inference
        logger.debug(f"Using updated InferenceRequest. Status: {inference_request.status}")

        # Return serialized InferenceRequest object
        logger.debug("Preparing response data")
        response_data = {
            "request_id": inference_request.request_id,
            "nim_id": inference_request.nim_id,
            "type": inference_request.type,
            "request_type": inference_request.request_type,
            "model": inference_request.model,
            "status": inference_request.status,
            "date_created": inference_request.date_created,
            "date_updated": inference_request.date_updated,
            "input": inference_request.get_input(),
            "output": inference_request.get_output(),
            "error": inference_request.get_error() if inference_request.error_json else None,
            "nim_metadata": nim_metadata,
            "nim_config": {
                "host": nim_data.host,
                "port": nim_data.port,
                "nim_type": nim_data.nim_type
            }
        }
        logger.debug(f"Response prepared successfully. Status: {response_data['status']}")
        return response_data

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error in NIM inference endpoint: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error details: {repr(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )
