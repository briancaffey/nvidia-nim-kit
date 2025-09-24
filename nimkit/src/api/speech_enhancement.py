"""Speech Enhancement API endpoints for Studio Voice NIM."""

import json
import logging
import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import (
    APIRouter,
    HTTPException,
    Depends,
    status,
    Query,
    UploadFile,
    File,
    Form,
)
from pydantic import BaseModel, field_validator

from .llm.models import InferenceRequest
from .utils import validate_nim_exists
from .inference_utils import perform_speech_enhancement_inference

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v0/speech-enhancement", tags=["speech-enhancement"])


class SpeechEnhancementRequest(BaseModel):
    """Request body for Speech Enhancement."""

    model_type: str = "48k-hq"
    audio_file_path: Optional[str] = None

    @field_validator("model_type")
    @classmethod
    def validate_model_type(cls, v):
        if v not in ["48k-hq", "48k-ll", "16k-hq"]:
            raise ValueError("Model type must be one of: '48k-hq', '48k-ll', '16k-hq'")
        return v


@router.post("/{publisher}/{model_name}")
async def speech_enhancement_inference(
    publisher: str,
    model_name: str,
    audio_file: UploadFile = File(...),
    model_type: str = Form(default="48k-hq"),
    use_nvidia_api: bool = Query(
        False, description="Use NVIDIA API instead of local NIM"
    ),
) -> Dict[str, Any]:
    """
    Perform speech enhancement inference on uploaded audio file using Studio Voice NIM.

    Args:
        publisher: The publisher/namespace of the NIM
        model_name: The model name
        audio_file: The uploaded audio file
        model_type: Studio Voice model type (48k-hq, 48k-ll, 16k-hq)
        use_nvidia_api: Whether to use NVIDIA API instead of local NIM

    Returns:
        Serialized InferenceRequest object with speech enhancement results
    """
    # Form the NIM ID from publisher and model name
    nim_id = f"{publisher}/{model_name}"

    logger.info(f"Starting speech enhancement inference request for NIM: {nim_id}")
    logger.info(
        f"Audio file: {audio_file.filename}, Content-Type: {audio_file.content_type}"
    )
    logger.info(f"Model type: {model_type}")

    try:
        # Validate NIM exists
        nim_data, nim_metadata = validate_nim_exists(nim_id)

        # Check if this is a speech enhancement NIM
        nim_type = nim_metadata.get("type", "").lower()
        if not nim_type:
            nim_type = getattr(nim_data, "nim_type", "").lower()

        if nim_type != "speech_enhancement":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"NIM {nim_id} is not a speech enhancement NIM (type: {nim_type})",
            )

        # Generate UUID for the request
        request_id = str(uuid.uuid4())
        logger.debug(f"Generated request ID: {request_id}")

        # Create media/studiovoice/input directory if it doesn't exist
        media_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "media"
        )
        studiovoice_input_dir = os.path.join(media_dir, "studiovoice", "input")
        studiovoice_output_dir = os.path.join(media_dir, "studiovoice", "output")
        os.makedirs(studiovoice_input_dir, exist_ok=True)
        os.makedirs(studiovoice_output_dir, exist_ok=True)

        # Save uploaded audio file
        audio_filename = f"{request_id}.wav"
        audio_path = os.path.join(studiovoice_input_dir, audio_filename)

        logger.info(f"Saving audio file to: {audio_path}")
        try:
            with open(audio_path, "wb") as f:
                content = await audio_file.read()
                f.write(content)
            logger.info(f"Successfully saved audio file: {audio_filename}")
        except Exception as save_error:
            logger.error(f"Failed to save audio file: {save_error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save audio file: {str(save_error)}",
            )

        # Create InferenceRequest record
        inference_request = InferenceRequest(
            request_id=request_id,
            input_json="",  # Initialize as empty string
            type="SPEECH_ENHANCEMENT",
            request_type="speech_enhancement",
            nim_id=nim_id,
            model=model_name,
            stream="false",
            status="pending",
            audio_file_path=audio_path,
        )

        # Set input data
        request_data = {
            "model_type": model_type,
            "audio_file_path": audio_path,
            "filename": audio_file.filename,
            "content_type": audio_file.content_type,
        }

        inference_request.set_input(request_data)
        inference_request.save()

        logger.info(
            f"Created speech enhancement inference request {request_id} for NIM {nim_id}"
        )

        # Perform speech enhancement inference
        response_data = await perform_speech_enhancement_inference(
            nim_id, request_data, inference_request, use_nvidia_api
        )

        # Return serialized InferenceRequest object
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

        return response_data

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error in speech enhancement inference endpoint: {str(e)}"
        )
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error details: {repr(e)}")
        import traceback

        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )
