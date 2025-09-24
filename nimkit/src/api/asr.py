"""ASR (Automatic Speech Recognition) API endpoints."""

import json
import logging
import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Depends, status, Query, UploadFile, File, Form
from pydantic import BaseModel, field_validator

from .llm.models import InferenceRequest
from .utils import validate_nim_exists
from .inference_utils import perform_asr_inference

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v0/asr", tags=["asr"])


class AsrRequest(BaseModel):
    """Request body for ASR (Automatic Speech Recognition)."""

    mode: str = "offline"
    audio_file_path: Optional[str] = None

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, v):
        if v not in ["offline"]:
            raise ValueError("Mode must be 'offline'")
        return v


@router.post("/{publisher}/{model_name}")
async def asr_inference(
    publisher: str,
    model_name: str,
    audio_file: UploadFile = File(...),
    mode: str = Form(default="offline"),
    use_nvidia_api: bool = Query(
        False, description="Use NVIDIA API instead of local NIM"
    ),
) -> Dict[str, Any]:
    """
    Perform ASR inference on uploaded audio file.

    Args:
        publisher: The publisher/namespace of the NIM
        model_name: The model name
        audio_file: The uploaded audio file
        mode: ASR mode (currently only "offline" supported)
        use_nvidia_api: Whether to use NVIDIA API instead of local NIM

    Returns:
        Serialized InferenceRequest object with ASR results
    """
    # Form the NIM ID from publisher and model name
    nim_id = f"{publisher}/{model_name}"

    logger.info(f"Starting ASR inference request for NIM: {nim_id}")
    logger.info(f"Audio file: {audio_file.filename}, Content-Type: {audio_file.content_type}")

    try:
        # Validate NIM exists
        nim_data, nim_metadata = validate_nim_exists(nim_id)

        # Check if this is an ASR NIM
        nim_type = nim_metadata.get("type", "").lower()
        if not nim_type:
            nim_type = getattr(nim_data, "nim_type", "").lower()

        if nim_type != "asr":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"NIM {nim_id} is not an ASR NIM (type: {nim_type})"
            )

        # Generate UUID for the request
        request_id = str(uuid.uuid4())
        logger.debug(f"Generated request ID: {request_id}")

        # Create media/asr directory if it doesn't exist
        media_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "media"
        )
        asr_dir = os.path.join(media_dir, "asr")
        os.makedirs(asr_dir, exist_ok=True)

        # Save uploaded audio file
        audio_filename = f"{request_id}.wav"
        audio_path = os.path.join(asr_dir, audio_filename)

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
                detail=f"Failed to save audio file: {str(save_error)}"
            )

        # Create InferenceRequest record
        inference_request = InferenceRequest(
            request_id=request_id,
            input_json="",  # Initialize as empty string
            type="ASR",
            request_type="asr",
            nim_id=nim_id,
            model=model_name,
            stream="false",
            status="pending",
            audio_file_path=audio_path,
        )

        # Set input data
        request_data = {
            "mode": mode,
            "audio_file_path": audio_path,
            "filename": audio_file.filename,
            "content_type": audio_file.content_type,
        }

        inference_request.set_input(request_data)
        inference_request.save()

        logger.info(f"Created ASR inference request {request_id} for NIM {nim_id}")

        # Perform ASR inference
        response_data = await perform_asr_inference(
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
        logger.error(f"Unexpected error in ASR inference endpoint: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error details: {repr(e)}")
        import traceback

        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )
