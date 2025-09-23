"""NIM inference API endpoints."""

import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Depends, status, Query
from pydantic import BaseModel, field_validator
from typing import ClassVar

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

    # Supported dimensions for Flux models
    SUPPORTED_DIMENSIONS: ClassVar[list[int]] = [
        672,
        688,
        720,
        752,
        800,
        832,
        880,
        944,
        1024,
        1104,
        1184,
        1248,
        1328,
        1392,
        1456,
        1504,
        1568,
    ]

    @field_validator("height", "width")
    @classmethod
    def validate_dimensions(cls, v):
        if v not in cls.SUPPORTED_DIMENSIONS:
            raise ValueError(
                f"Dimension {v} is not supported. Supported dimensions are: {cls.SUPPORTED_DIMENSIONS}"
            )
        return v

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, v):
        if v not in ["base", "canny", "depth"]:
            raise ValueError("Mode must be one of: base, canny, depth")
        return v


class TrellisGenerationRequest(BaseModel):
    """Request body for Trellis 3D model generation."""

    mode: str = "text"
    prompt: str = ""
    image: str = None
    ss_cfg_scale: float = 7.5
    slat_cfg_scale: float = 3.0
    samples: int = 1
    no_texture: bool = False
    seed: int = 0
    ss_sampling_steps: int = 25
    slat_sampling_steps: int = 25
    output_format: str = "glb"

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, v):
        if v not in ["text", "image"]:
            raise ValueError("Mode must be one of: text, image")
        return v

    @field_validator("ss_cfg_scale", "slat_cfg_scale")
    @classmethod
    def validate_cfg_scale(cls, v):
        if not 2.0 <= v <= 10.0:
            raise ValueError("CFG scale must be between 2.0 and 10.0")
        return v

    @field_validator("ss_sampling_steps", "slat_sampling_steps")
    @classmethod
    def validate_sampling_steps(cls, v):
        if not 10 <= v <= 50:
            raise ValueError("Sampling steps must be between 10 and 50")
        return v

    @field_validator("seed")
    @classmethod
    def validate_seed(cls, v):
        if v < 0:
            raise ValueError("Seed must be a non-negative integer")
        return v

    @field_validator("output_format")
    @classmethod
    def validate_output_format(cls, v):
        if v not in ["glb"]:
            raise ValueError("Output format must be 'glb'")
        return v


@router.post("/{publisher}/{model_name}")
async def nim_inference(
    publisher: str,
    model_name: str,
    request_data: Dict[str, Any],
    use_nvidia_api: bool = Query(
        False, description="Use NVIDIA API instead of local NIM"
    ),
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
        logger.debug(
            f"NIM validation successful. Host: {nim_data.host}, Port: {nim_data.port}, Type: {nim_data.nim_type}"
        )

        # Generate UUID for the request
        request_id = str(uuid.uuid4())
        logger.debug(f"Generated request ID: {request_id}")

        # Determine request type based on NIM type
        # Get NIM type from metadata (YAML) first, fallback to Redis config
        nim_type = nim_metadata.get("type", "").lower()
        if not nim_type:
            # Fallback to Redis config nim_type
            nim_type = getattr(nim_data, "nim_type", "").lower()

        logger.debug(
            f"Determined NIM type: {nim_type} (from metadata: {nim_metadata.get('type', '')}, from Redis: {getattr(nim_data, 'nim_type', '')})"
        )

        if nim_type == "image":
            request_type = "IMAGE_GENERATION"
            request_type_str = "image_generation"
        elif nim_type == "3d":
            request_type = "3D_GENERATION"
            request_type_str = "3d_generation"
        else:
            request_type = "UNKNOWN"
            request_type_str = "unknown"

        # Create InferenceRequest record
        logger.debug(f"Creating InferenceRequest record for type: {request_type}")
        inference_request = InferenceRequest(
            request_id=request_id,
            input_json="",  # Initialize as empty string
            type=request_type,
            request_type=request_type_str,
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
                detail=f"Failed to save inference request: {str(save_error)}",
            )

        logger.info(f"Created inference request {request_id} for NIM {nim_id}")

        # Perform inference
        logger.debug("Starting inference process")
        response_data = await perform_inference(
            nim_id, request_data, inference_request, use_nvidia_api
        )
        logger.debug(
            f"Inference completed successfully. Response data keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'Not a dict'}"
        )

        # Use the inference_request object that was updated by perform_inference
        logger.debug(
            f"Using updated InferenceRequest. Status: {inference_request.status}"
        )

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
            "error": (
                inference_request.get_error() if inference_request.error_json else None
            ),
            "nim_metadata": nim_metadata,
            "nim_config": {
                "host": nim_data.host,
                "port": nim_data.port,
                "nim_type": nim_data.nim_type,
            },
        }
        logger.debug(
            f"Response prepared successfully. Status: {response_data['status']}"
        )
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
            detail=f"Internal server error: {str(e)}",
        )
