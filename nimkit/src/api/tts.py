"""TTS (Text-to-Speech) API endpoints for Magpie TTS NIM."""

import json
import logging
import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List

import requests
from fastapi import (
    APIRouter,
    HTTPException,
    status,
    Query,
    Form,
)

from .llm.models import InferenceRequest
from .utils import validate_nim_exists, get_nvidia_api_headers
from .inference_utils import perform_tts_inference

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v0/tts", tags=["tts"])


@router.get("/{publisher}/{model_name}/voices")
async def list_voices(
    publisher: str,
    model_name: str,
    use_nvidia_api: bool = Query(
        False, description="Use NVIDIA API instead of local NIM"
    ),
) -> Dict[str, Any]:
    """
    List available voices from the TTS NIM.

    Args:
        publisher: The publisher/namespace of the NIM
        model_name: The model name
        use_nvidia_api: Whether to use NVIDIA API instead of local NIM

    Returns:
        Dictionary containing list of available voices
    """
    nim_id = f"{publisher}/{model_name}"

    logger.info(f"Fetching available voices for NIM: {nim_id}")

    try:
        # Validate NIM exists
        nim_data, nim_metadata = validate_nim_exists(nim_id)

        # Check if this is a TTS NIM
        nim_type = nim_metadata.get("type", "").lower()
        if not nim_type:
            nim_type = getattr(nim_data, "nim_type", "").lower()

        if nim_type != "tts":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"NIM {nim_id} is not a TTS NIM (type: {nim_type})",
            )

        if use_nvidia_api:
            # Use NVIDIA API endpoint
            invoke_url = nim_metadata.get("invoke_url")
            if not invoke_url:
                raise HTTPException(
                    status_code=400,
                    detail=f"NVIDIA API invoke_url not found for NIM {nim_id}",
                )

            # Replace synthesize with list_voices
            voices_url = invoke_url.replace("/synthesize", "/list_voices")
            headers = get_nvidia_api_headers()
        else:
            # Use local NIM endpoint
            base_url = f"http://{nim_data.host}:{nim_data.port}"
            voices_url = f"{base_url}/v1/audio/list_voices"
            headers = {"accept": "application/json"}

        logger.info(f"Fetching voices from: {voices_url}")
        logger.info(f"NIM config - host: {nim_data.host}, port: {nim_data.port}")

        try:
            response = requests.get(voices_url, headers=headers, timeout=30)
        except requests.exceptions.Timeout:
            error_msg = f"Timeout connecting to TTS NIM at {voices_url}. Please verify the NIM is running and accessible."
            logger.error(error_msg)
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=error_msg
            )
        except requests.exceptions.ConnectionError as e:
            error_msg = f"Cannot connect to TTS NIM at {voices_url}. Please verify the host and port are correct. If using Docker, use 'host.docker.internal' instead of 'localhost'. Error: {str(e)}"
            logger.error(error_msg)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY, detail=error_msg
            )

        if response.status_code != 200:
            error_msg = f"Failed to fetch voices: {response.status_code} - {response.text}"
            logger.error(error_msg)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY, detail=error_msg
            )

        voices_data = response.json()
        logger.info(f"Successfully fetched voices for {nim_id}")
        logger.info(f"Voices response type: {type(voices_data)}")
        logger.info(f"Voices response keys: {voices_data.keys() if isinstance(voices_data, dict) else 'N/A'}")
        logger.info(f"Voices response (first 500 chars): {str(voices_data)[:500]}")

        # The Magpie TTS NIM returns voices in a nested structure like:
        # {"en-US,es-US,...": {"voices": [...]}}
        # We need to extract and flatten all voices into a single list
        all_voices = []
        if isinstance(voices_data, dict):
            # Check if it already has a "voices" key at top level
            if "voices" in voices_data and isinstance(voices_data["voices"], list):
                all_voices = voices_data["voices"]
            else:
                # Extract voices from nested structure
                for key, value in voices_data.items():
                    if isinstance(value, dict) and "voices" in value:
                        all_voices.extend(value["voices"])

        logger.info(f"Extracted {len(all_voices)} voices for {nim_id}")
        return {"voices": all_voices}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching voices for {nim_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch voices: {str(e)}",
        )


@router.post("/{publisher}/{model_name}")
async def tts_inference(
    publisher: str,
    model_name: str,
    text: str = Form(..., description="Text to synthesize"),
    language: str = Form(..., description="Language code (e.g., en-US, es-US, fr-FR)"),
    voice: Optional[str] = Form(None, description="Voice name"),
    sample_rate_hz: int = Form(22050, description="Output sample rate in Hz"),
    use_nvidia_api: bool = Query(
        False, description="Use NVIDIA API instead of local NIM"
    ),
) -> Dict[str, Any]:
    """
    Perform TTS inference to generate speech from text.

    Args:
        publisher: The publisher/namespace of the NIM
        model_name: The model name
        text: Text to synthesize
        language: Language code (en-US, es-US, fr-FR, de-DE, zh-CN, vi-VN, it-IT)
        voice: Voice name (optional)
        sample_rate_hz: Output sample rate in Hz (default: 22050)
        use_nvidia_api: Whether to use NVIDIA API instead of local NIM

    Returns:
        Serialized InferenceRequest object with TTS results
    """
    nim_id = f"{publisher}/{model_name}"

    logger.info(f"Starting TTS inference request for NIM: {nim_id}")
    logger.info(f"Text length: {len(text)}, Language: {language}, Voice: {voice}")

    try:
        # Validate NIM exists
        nim_data, nim_metadata = validate_nim_exists(nim_id)

        # Check if this is a TTS NIM
        nim_type = nim_metadata.get("type", "").lower()
        if not nim_type:
            nim_type = getattr(nim_data, "nim_type", "").lower()

        if nim_type != "tts":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"NIM {nim_id} is not a TTS NIM (type: {nim_type})",
            )

        # Generate UUID for the request
        request_id = str(uuid.uuid4())
        logger.debug(f"Generated request ID: {request_id}")

        # Create media/tts/output directory if it doesn't exist
        media_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "media"
        )
        tts_output_dir = os.path.join(media_dir, "tts", "output")
        os.makedirs(tts_output_dir, exist_ok=True)

        # Create InferenceRequest record
        inference_request = InferenceRequest(
            request_id=request_id,
            input_json="",  # Initialize as empty string
            type="TTS",
            request_type="tts",
            nim_id=nim_id,
            model=model_name,
            stream="false",
            status="pending",
        )

        # Set input data
        request_data = {
            "text": text,
            "language": language,
            "voice": voice,
            "sample_rate_hz": sample_rate_hz,
        }

        inference_request.set_input(request_data)
        inference_request.save()

        logger.info(f"Created TTS inference request {request_id} for NIM {nim_id}")

        # Perform TTS inference
        response_data = await perform_tts_inference(
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
        raise
    except Exception as e:
        logger.error(f"Unexpected error in TTS inference endpoint: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback

        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )
