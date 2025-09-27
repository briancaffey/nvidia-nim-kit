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


async def perform_asr_inference(
    nim_id: str,
    request_data: Dict[str, Any],
    inference_request: InferenceRequest,
    use_nvidia_api: bool = False,
) -> Dict[str, Any]:
    """
    Perform ASR (Automatic Speech Recognition) inference for a NIM using RIVA client.

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

        # Get audio file path from request data
        audio_file_path = request_data.get("audio_file_path")
        if not audio_file_path or not os.path.exists(audio_file_path):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Audio file not found or path not provided",
            )

        logger.info(f"Performing ASR inference for {nim_id}")
        logger.debug(f"NIM type: {nim_data.nim_type}")
        logger.debug(f"NIM metadata: {nim_metadata}")
        logger.debug(f"Audio file path: {audio_file_path}")

        # Use RIVA client for ASR inference (following the working example)
        try:
            import riva.client
            import grpc
        except ImportError as import_error:
            logger.error(f"Failed to import RIVA client: {import_error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="RIVA client library not available",
            )

        # Handle NVIDIA API vs Local NIM differently
        if use_nvidia_api:
            # Use NVIDIA API gRPC endpoint (following the exact pattern from the example)
            try:
                import riva.client
                import grpc
            except ImportError as import_error:
                logger.error(f"Failed to import RIVA client: {import_error}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="RIVA client library not available",
                )

            # Get NVIDIA API key
            from nimkit.src.api.utils import get_nvidia_api_key

            api_key = get_nvidia_api_key()

            if not api_key:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="NVIDIA API key not configured. Please set your API key in the NVIDIA Config page.",
                )

            # Configure RIVA client for NVIDIA API (following the exact pattern)
            riva_uri = "grpc.nvcf.nvidia.com:443"

            # Create auth with exact metadata format from the example
            auth = riva.client.Auth(
                uri=riva_uri,
                use_ssl=True,
                metadata_args=[
                    ("function-id", "d8dd4e9b-fbf5-4fb0-9dba-8cf436c8d965"),
                    ("authorization", f"Bearer {api_key}"),
                ],
            )

            logger.info(f"Connecting to NVIDIA API RIVA service at: {riva_uri}")

            # Create RIVA client
            try:
                asr_service = riva.client.ASRService(auth)
                logger.debug("NVIDIA API RIVA ASR client created successfully")

                # Try to list available models to debug the connection
                try:
                    logger.debug("Attempting to list available ASR models...")
                    config_response = asr_service.stub.GetRivaSpeechRecognitionConfig(
                        riva.client.proto.riva_asr_pb2.RivaSpeechRecognitionConfigRequest()
                    )
                    logger.debug(
                        f"Available models: {len(config_response.model_config)} models found"
                    )
                    for i, model_config in enumerate(config_response.model_config):
                        logger.debug(
                            f"Model {i}: {model_config.model_name}, type: {model_config.parameters.get('type', 'unknown')}"
                        )
                except Exception as model_error:
                    logger.warning(f"Could not list models: {model_error}")

            except Exception as client_error:
                logger.error(f"Failed to create NVIDIA API RIVA client: {client_error}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Failed to connect to NVIDIA API RIVA service: {str(client_error)}",
                )

            # Read audio file (following the working example - much simpler!)
            try:
                with open(audio_file_path, "rb") as fh:
                    audio_data = fh.read()
                logger.debug(f"Read audio file: {len(audio_data)} bytes")

                # Additional debugging - check if it's a valid WAV file
                if audio_data.startswith(b"RIFF") and b"WAVE" in audio_data[:12]:
                    logger.debug("Audio file appears to be a valid WAV file")

                    # Try to read WAV header for debugging
                    try:
                        import wave
                        import io

                        with wave.open(io.BytesIO(audio_data), "rb") as wav_file:
                            channels = wav_file.getnchannels()
                            sample_width = wav_file.getsampwidth()
                            framerate = wav_file.getframerate()
                            n_frames = wav_file.getnframes()
                            duration = n_frames / framerate

                            logger.debug(
                                f"WAV file info: channels={channels}, sample_width={sample_width}, framerate={framerate}, n_frames={n_frames}, duration={duration:.2f}s"
                            )

                            # Check if it meets RIVA requirements (16-bit mono)
                            if sample_width == 2 and channels == 1:
                                logger.debug(
                                    "Audio format meets RIVA requirements (16-bit mono)"
                                )

                                # Check audio levels (simple check for silence)
                                try:
                                    import numpy as np

                                    audio_array = np.frombuffer(
                                        audio_data[44:], dtype=np.int16
                                    )  # Skip WAV header
                                    max_level = np.max(np.abs(audio_array))
                                    rms_level = np.sqrt(
                                        np.mean(audio_array.astype(np.float32) ** 2)
                                    )

                                    logger.debug(
                                        f"Audio levels: max={max_level}, rms={rms_level:.1f}"
                                    )

                                    if max_level < 100:
                                        logger.warning(
                                            "Audio appears to be very quiet (max level < 100)"
                                        )
                                    elif max_level < 1000:
                                        logger.warning(
                                            "Audio appears to be quiet (max level < 1000)"
                                        )
                                    else:
                                        logger.debug("Audio levels appear normal")

                                except Exception as level_error:
                                    logger.warning(
                                        f"Could not check audio levels: {level_error}"
                                    )
                            else:
                                logger.warning(
                                    f"Audio format may not be optimal for RIVA: {sample_width*8}-bit, {channels} channel(s)"
                                )

                    except Exception as wav_error:
                        logger.warning(f"Could not parse WAV header: {wav_error}")
                else:
                    logger.warning("Audio file does not appear to be a valid WAV file")
                    logger.debug(f"First 20 bytes: {audio_data[:20]}")

            except Exception as file_error:
                logger.error(f"Failed to read audio file: {file_error}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to read audio file: {str(file_error)}",
                )

            # Create recognition config (following the working example)
            try:
                config = riva.client.RecognitionConfig(
                    language_code="en-US",
                    enable_automatic_punctuation=True,
                    enable_word_time_offsets=True,
                    max_alternatives=1,
                    profanity_filter=False,
                    verbatim_transcripts=True,
                )
                logger.debug(
                    f"Recognition config created: language=en-US, automatic_punctuation=True, word_time_offsets=True, max_alternatives=1, profanity_filter=False, verbatim_transcripts=True"
                )
            except Exception as config_error:
                logger.error(f"Failed to create recognition config: {config_error}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to create recognition config: {str(config_error)}",
                )

            # Perform ASR inference (following the working example)
            try:
                logger.debug("Starting ASR inference with NVIDIA API RIVA client")
                response = asr_service.offline_recognize(audio_data, config)
                logger.info(f"ASR inference successful for {nim_id}")
            except grpc.RpcError as e:
                logger.error(f"ASR inference failed with gRPC error: {e.details()}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"ASR inference failed: {e.details()}",
                )
            except Exception as asr_error:
                logger.error(f"ASR inference failed: {asr_error}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"ASR inference failed: {str(asr_error)}",
                )

            # Process gRPC response (same as local NIM)
            response_data = {"text": "", "words": [], "confidence": 0.0}

            # Extract results from response
            logger.debug(f"RIVA response type: {type(response)}")
            logger.debug(f"RIVA response attributes: {dir(response)}")

            if hasattr(response, "results") and response.results:
                logger.debug(f"Number of results: {len(response.results)}")
                for i, result in enumerate(response.results):
                    logger.debug(f"Result {i} type: {type(result)}")
                    logger.debug(
                        f"Result {i} has alternatives: {hasattr(result, 'alternatives')}"
                    )
                    if hasattr(result, "alternatives"):
                        logger.debug(f"Result {i} alternatives: {result.alternatives}")
                        logger.debug(
                            f"Result {i} alternatives length: {len(result.alternatives) if result.alternatives else 0}"
                        )

                    if hasattr(result, "alternatives") and result.alternatives:
                        logger.debug(
                            f"Number of alternatives: {len(result.alternatives)}"
                        )
                        alternative = result.alternatives[0]
                        logger.debug(
                            f"Alternative transcript: '{alternative.transcript}'"
                        )
                        logger.debug(
                            f"Alternative confidence: {alternative.confidence}"
                        )

                        response_data["text"] += alternative.transcript
                        response_data["confidence"] = alternative.confidence

                        # Extract word-level timestamps if available
                        if hasattr(alternative, "words") and alternative.words:
                            logger.debug(f"Number of words: {len(alternative.words)}")
                            for word in alternative.words:
                                response_data["words"].append(
                                    {
                                        "word": word.word,
                                        "start_time": word.start_time,
                                        "end_time": word.end_time,
                                        "confidence": word.confidence,
                                    }
                                )
                    else:
                        logger.warning(
                            f"Result {i} has no alternatives or empty alternatives"
                        )
                        logger.debug(f"Result {i} content: {result}")
            else:
                logger.warning("No results found in RIVA response")
                logger.debug(f"Response content: {response}")

            logger.debug(f"Processed ASR response: {response_data}")

        else:
            # Use local NIM with gRPC (RIVA client)
            try:
                import riva.client
                import grpc
            except ImportError as import_error:
                logger.error(f"Failed to import RIVA client: {import_error}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="RIVA client library not available",
                )

            # Configure RIVA client for local NIM
            riva_uri = f"{nim_data.host}:50051"  # gRPC port
            auth = riva.client.Auth(uri=riva_uri, use_ssl=False)

            logger.info(f"Connecting to local RIVA service at: {riva_uri}")

            # Create RIVA client
            try:
                asr_service = riva.client.ASRService(auth)
                logger.debug("Local RIVA ASR client created successfully")

                # Try to list available models to debug the connection
                try:
                    logger.debug("Attempting to list available local ASR models...")
                    config_response = asr_service.stub.GetRivaSpeechRecognitionConfig(
                        riva.client.proto.riva_asr_pb2.RivaSpeechRecognitionConfigRequest()
                    )
                    logger.debug(
                        f"Available local models: {len(config_response.model_config)} models found"
                    )
                    for i, model_config in enumerate(config_response.model_config):
                        logger.debug(
                            f"Local Model {i}: {model_config.model_name}, type: {model_config.parameters.get('type', 'unknown')}"
                        )
                except Exception as model_error:
                    logger.warning(f"Could not list local models: {model_error}")

            except Exception as client_error:
                logger.error(f"Failed to create local RIVA client: {client_error}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Failed to connect to local RIVA service: {str(client_error)}",
                )

            # Read audio file
            try:
                with open(audio_file_path, "rb") as fh:
                    audio_data = fh.read()
                logger.debug(f"Read audio file: {len(audio_data)} bytes")

                # Additional debugging - check if it's a valid WAV file
                if audio_data.startswith(b"RIFF") and b"WAVE" in audio_data[:12]:
                    logger.debug("Audio file appears to be a valid WAV file")

                    # Try to read WAV header for debugging
                    try:
                        import wave
                        import io

                        with wave.open(io.BytesIO(audio_data), "rb") as wav_file:
                            channels = wav_file.getnchannels()
                            sample_width = wav_file.getsampwidth()
                            framerate = wav_file.getframerate()
                            n_frames = wav_file.getnframes()
                            duration = n_frames / framerate

                            logger.debug(
                                f"Local WAV file info: channels={channels}, sample_width={sample_width}, framerate={framerate}, n_frames={n_frames}, duration={duration:.2f}s"
                            )

                            # Check if it meets RIVA requirements (16-bit mono)
                            if sample_width == 2 and channels == 1:
                                logger.debug(
                                    "Audio format meets RIVA requirements (16-bit mono)"
                                )

                                # Check audio levels (simple check for silence)
                                try:
                                    import numpy as np

                                    audio_array = np.frombuffer(
                                        audio_data[44:], dtype=np.int16
                                    )  # Skip WAV header
                                    max_level = np.max(np.abs(audio_array))
                                    rms_level = np.sqrt(
                                        np.mean(audio_array.astype(np.float32) ** 2)
                                    )

                                    logger.debug(
                                        f"Local audio levels: max={max_level}, rms={rms_level:.1f}"
                                    )

                                    if max_level < 100:
                                        logger.warning(
                                            "Local audio appears to be very quiet (max level < 100)"
                                        )
                                    elif max_level < 1000:
                                        logger.warning(
                                            "Local audio appears to be quiet (max level < 1000)"
                                        )
                                    else:
                                        logger.debug("Local audio levels appear normal")

                                except Exception as level_error:
                                    logger.warning(
                                        f"Could not check local audio levels: {level_error}"
                                    )
                            else:
                                logger.warning(
                                    f"Local audio format may not be optimal for RIVA: {sample_width*8}-bit, {channels} channel(s)"
                                )

                    except Exception as wav_error:
                        logger.warning(f"Could not parse local WAV header: {wav_error}")
                else:
                    logger.warning(
                        "Local audio file does not appear to be a valid WAV file"
                    )
                    logger.debug(f"First 20 bytes: {audio_data[:20]}")

            except Exception as file_error:
                logger.error(f"Failed to read audio file: {file_error}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to read audio file: {str(file_error)}",
                )

            # Create recognition config (matching NVIDIA API config)
            try:
                config = riva.client.RecognitionConfig(
                    language_code="en-US",
                    enable_automatic_punctuation=True,
                    enable_word_time_offsets=True,
                    max_alternatives=1,
                    profanity_filter=False,
                    verbatim_transcripts=True,
                )
                logger.debug(
                    f"Recognition config created: language=en-US, automatic_punctuation=True, word_time_offsets=True, max_alternatives=1, profanity_filter=False, verbatim_transcripts=True"
                )
            except Exception as config_error:
                logger.error(f"Failed to create recognition config: {config_error}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to create recognition config: {str(config_error)}",
                )

            # Perform ASR inference
            try:
                logger.debug("Starting ASR inference with RIVA client")
                response = asr_service.offline_recognize(audio_data, config)
                logger.info(f"ASR inference successful for {nim_id}")
            except grpc.RpcError as e:
                logger.error(f"ASR inference failed with gRPC error: {e.details()}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"ASR inference failed: {e.details()}",
                )
            except Exception as asr_error:
                logger.error(f"ASR inference failed: {asr_error}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"ASR inference failed: {str(asr_error)}",
                )

            # Process gRPC response (existing code)
            response_data = {"text": "", "words": [], "confidence": 0.0}

            # Extract results from response
            logger.debug(f"RIVA response type: {type(response)}")
            logger.debug(f"RIVA response attributes: {dir(response)}")

            if hasattr(response, "results") and response.results:
                logger.debug(f"Number of results: {len(response.results)}")
                for i, result in enumerate(response.results):
                    logger.debug(f"Result {i} type: {type(result)}")
                    logger.debug(
                        f"Result {i} has alternatives: {hasattr(result, 'alternatives')}"
                    )
                    if hasattr(result, "alternatives"):
                        logger.debug(f"Result {i} alternatives: {result.alternatives}")
                        logger.debug(
                            f"Result {i} alternatives length: {len(result.alternatives) if result.alternatives else 0}"
                        )

                    if hasattr(result, "alternatives") and result.alternatives:
                        logger.debug(
                            f"Number of alternatives: {len(result.alternatives)}"
                        )
                        alternative = result.alternatives[0]
                        logger.debug(
                            f"Alternative transcript: '{alternative.transcript}'"
                        )
                        logger.debug(
                            f"Alternative confidence: {alternative.confidence}"
                        )

                        response_data["text"] += alternative.transcript
                        response_data["confidence"] = alternative.confidence

                        # Extract word-level timestamps if available
                        if hasattr(alternative, "words") and alternative.words:
                            logger.debug(f"Number of words: {len(alternative.words)}")
                            for word in alternative.words:
                                response_data["words"].append(
                                    {
                                        "word": word.word,
                                        "start_time": word.start_time,
                                        "end_time": word.end_time,
                                        "confidence": word.confidence,
                                    }
                                )
                    else:
                        logger.warning(
                            f"Result {i} has no alternatives or empty alternatives"
                        )
                        logger.debug(f"Result {i} content: {result}")
            else:
                logger.warning("No results found in RIVA response")
                logger.debug(f"Response content: {response}")

            logger.debug(f"Processed ASR response: {response_data}")

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

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        error_msg = f"Unexpected error during ASR inference for {nim_id}: {str(e)}"
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


async def perform_speech_enhancement_inference(
    nim_id: str,
    request_data: Dict[str, Any],
    inference_request: InferenceRequest,
    use_nvidia_api: bool = False,
) -> Dict[str, Any]:
    """
    Perform speech enhancement inference for Studio Voice NIM using gRPC client.

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
    import os  # Import os at the top of the function

    try:
        # Validate NIM exists and get configuration
        nim_data, nim_metadata = validate_nim_exists(nim_id)

        # Get audio file path from request data
        audio_file_path = request_data.get("audio_file_path")
        if not audio_file_path or not os.path.exists(audio_file_path):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Audio file not found or path not provided",
            )

        logger.info(f"Performing speech enhancement inference for {nim_id}")
        logger.debug(f"NIM type: {nim_data.nim_type}")
        logger.debug(f"NIM metadata: {nim_metadata}")
        logger.debug(f"Audio file path: {audio_file_path}")

        # Import Studio Voice client modules
        try:
            import sys

            studio_voice_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "studio-voice",
                "interfaces",
                "studio_voice",
            )
            sys.path.append(studio_voice_path)

            import studiovoice_pb2
            import studiovoice_pb2_grpc
            import grpc
            import soundfile as sf
            import numpy as np
            import time
        except ImportError as import_error:
            logger.error(f"Failed to import Studio Voice client: {import_error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Studio Voice client library not available",
            )

        # Get model type from request data
        model_type = request_data.get("model_type", "48k-hq")
        logger.info(f"Using Studio Voice model type: {model_type}")

        # Determine sample rate based on model type
        sample_rate = 48000
        if model_type == "16k-hq":
            sample_rate = 16000
        logger.info(f"Using sample rate: {sample_rate}")

        # Check input audio sample rate
        try:
            input_info = sf.info(audio_file_path)
            input_sample_rate = input_info.samplerate
            logger.info(f"Input file sample rate: {input_sample_rate}")

            if input_sample_rate != sample_rate:
                logger.warning(
                    f"Sample rate mismatch: expected {sample_rate}, got {input_sample_rate}"
                )
                # For now, we'll proceed but this might cause issues
        except Exception as e:
            logger.warning(f"Could not read audio file info: {e}")

        # Create output file path
        request_id = inference_request.request_id
        media_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "media"
        )
        studiovoice_output_dir = os.path.join(media_dir, "studiovoice", "output")
        os.makedirs(studiovoice_output_dir, exist_ok=True)

        output_filename = f"{request_id}.wav"
        output_path = os.path.join(studiovoice_output_dir, output_filename)

        logger.info(f"Output file will be saved to: {output_path}")

        # Update inference request with output path
        inference_request.output_audio_path = output_path
        inference_request.update_timestamp()
        inference_request.save()

        # Handle NVIDIA API vs Local NIM differently
        if use_nvidia_api:
            logger.info("Using NVIDIA API for speech enhancement")

            # Use NVIDIA Cloud Function gRPC endpoint
            target = "grpc.nvcf.nvidia.com:443"
            logger.info(f"Connecting to NVIDIA Cloud Function at: {target}")

            # Create gRPC channel with SSL credentials for NVIDIA Cloud
            try:
                credentials = grpc.ssl_channel_credentials()

                # Get NVIDIA API key from environment
                nvidia_api_key = os.getenv("NVIDIA_API_KEY")
                if not nvidia_api_key:
                    logger.error("NVIDIA_API_KEY environment variable not set")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="NVIDIA API key not configured",
                    )

                # Create metadata with authorization and function ID
                metadata = [
                    ("authorization", f"Bearer {nvidia_api_key}"),
                    ("function-id", "7cf12edb-2181-4947-8b19-2b1c18270588")
                ]

                with grpc.secure_channel(target, credentials) as channel:
                    stub = studiovoice_pb2_grpc.MaxineStudioVoiceStub(channel)

                    logger.info(
                        "Starting NVIDIA Cloud Studio Voice enhancement process"
                    )
                    start_time = time.time()

                    # Generate request stream (non-streaming mode for simplicity)
                    def generate_request():
                        DATA_CHUNKS = (
                            64 * 1024
                        )  # bytes, we send the wav file in 64KB chunks
                        with open(audio_file_path, "rb") as fd:
                            while True:
                                buffer = fd.read(DATA_CHUNKS)
                                if buffer == b"":
                                    break
                                yield studiovoice_pb2.EnhanceAudioRequest(
                                    audio_stream_data=buffer
                                )

                    logger.info("Writing enhanced audio to output file")

                    # Call the gRPC service with metadata
                    response_stream = stub.EnhanceAudio(
                        generate_request(), metadata=metadata
                    )

                    # Write the response to output file
                    response_count = 0
                    with open(output_path, "wb") as fd:
                        for response in response_stream:
                            response_count += 1
                            if response.audio_stream_data:
                                fd.write(response.audio_stream_data)

                    processing_time = time.time() - start_time
                    logger.info(
                        f"Studio Voice enhancement completed in {processing_time:.2f} seconds"
                    )
                    logger.info(f"Received {response_count} response chunks")
                    logger.info(f"Output file saved to: {output_path}")

                    # Update inference request with success
                    output_data = {
                        "enhanced_audio_path": output_path,
                        "model_type": model_type,
                        "sample_rate": sample_rate,
                        "processing_time_seconds": processing_time,
                        "response_chunks": response_count,
                        "input_file": audio_file_path,
                        "output_file": output_path,
                        "api_type": "nvidia_cloud",
                    }
                    inference_request.set_output(output_data)
                    inference_request.save()

                    logger.info(
                        f"NVIDIA Cloud speech enhancement inference completed successfully for request {request_id}"
                    )

                    return output_data

            except grpc.RpcError as grpc_error:
                logger.error(
                    f"gRPC error during NVIDIA Cloud Studio Voice inference: {grpc_error}"
                )
                inference_request.set_error(
                    {
                        "error": f"gRPC error: {str(grpc_error)}",
                        "grpc_status": grpc_error.code().name,
                        "grpc_details": grpc_error.details(),
                    }
                )
                inference_request.save()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"gRPC error during NVIDIA Cloud Studio Voice inference: {str(grpc_error)}",
                )
            except Exception as e:
                logger.error(
                    f"Unexpected error during NVIDIA Cloud Studio Voice inference: {str(e)}"
                )
                inference_request.set_error(
                    {"error": str(e), "error_type": type(e).__name__}
                )
                inference_request.save()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Unexpected error during NVIDIA Cloud Studio Voice inference: {str(e)}",
                )
        else:
            # Use local NIM with gRPC
            logger.info("Using local NIM for speech enhancement")

            # Get NIM endpoint - hardcode port 8001 for Studio Voice gRPC
            target_host = nim_data.host
            target_port = 8001  # Hardcoded for Studio Voice gRPC
            target = f"{target_host}:{target_port}"

            logger.info(
                f"Connecting to Studio Voice NIM at: {target} (hardcoded port 8001 for gRPC)"
            )

            # Create gRPC channel and stub
            try:
                with grpc.insecure_channel(target) as channel:
                    stub = studiovoice_pb2_grpc.MaxineStudioVoiceStub(channel)

                    logger.info("Starting Studio Voice enhancement process")
                    start_time = time.time()

                    # Generate request stream (non-streaming mode for simplicity)
                    def generate_request():
                        DATA_CHUNKS = (
                            64 * 1024
                        )  # bytes, we send the wav file in 64KB chunks
                        with open(audio_file_path, "rb") as fd:
                            while True:
                                buffer = fd.read(DATA_CHUNKS)
                                if buffer == b"":
                                    break
                                yield studiovoice_pb2.EnhanceAudioRequest(
                                    audio_stream_data=buffer
                                )

                    # Call the gRPC service
                    responses = stub.EnhanceAudio(generate_request())

                    # Write output file from response stream
                    logger.info("Writing enhanced audio to output file")
                    with open(output_path, "wb") as fd:
                        response_count = 0
                        for response in responses:
                            response_count += 1
                            if response.HasField("audio_stream_data"):
                                fd.write(response.audio_stream_data)

                    end_time = time.time()
                    processing_time = end_time - start_time

                    logger.info(
                        f"Studio Voice enhancement completed in {processing_time:.2f}s"
                    )
                    logger.info(f"Processed {response_count} response chunks")
                    logger.info(f"Output file saved: {output_path}")

                    # Update inference request with success
                    inference_request.status = "completed"
                    inference_request.update_timestamp()

                    # Set output data
                    output_data = {
                        "enhanced_audio_path": output_path,
                        "model_type": model_type,
                        "sample_rate": sample_rate,
                        "processing_time_seconds": processing_time,
                        "response_chunks": response_count,
                        "input_file": audio_file_path,
                        "output_file": output_path,
                        "api_type": "local_nim",
                    }
                    inference_request.set_output(output_data)
                    inference_request.save()

                    logger.info(
                        f"Speech enhancement inference completed successfully for request {request_id}"
                    )

                    return output_data

            except grpc.RpcError as grpc_error:
                logger.error(f"gRPC error during Studio Voice inference: {grpc_error}")
                error_msg = f"gRPC error: {grpc_error.details() if hasattr(grpc_error, 'details') else str(grpc_error)}"

                inference_request.status = "error"
                inference_request.update_timestamp()
                inference_request.set_error(
                    {"error": error_msg, "grpc_code": grpc_error.code().name}
                )
                inference_request.save()

                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_msg
                )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error in speech enhancement inference: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error details: {repr(e)}")
        import traceback

        logger.error(f"Full traceback: {traceback.format_exc()}")

        # Update inference request with error
        inference_request.status = "error"
        inference_request.update_timestamp()
        inference_request.set_error({"error": str(e), "error_type": type(e).__name__})
        inference_request.save()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Speech enhancement inference failed: {str(e)}",
        )


async def perform_paddleocr_inference(
    nim_id: str,
    request_data: Dict[str, Any],
    inference_request: InferenceRequest,
    use_nvidia_api: bool = False,
) -> Dict[str, Any]:
    """
    Perform PaddleOCR text detection inference for a NIM.

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
        # Import PaddleOCR utilities
        from .paddleocr_utils import (
            extract_text_from_image,
            visualize_text_detections,
            process_paddleocr_response
        )

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
            invoke_url = base_url

            # Prepare headers for local NIM
            headers = {"accept": "application/json", "content-type": "application/json"}

        logger.info(f"Performing PaddleOCR inference for {nim_id}")
        logger.debug(f"NIM type: {nim_data.nim_type}")
        logger.debug(f"NIM metadata: {nim_metadata}")
        logger.info(f"Invoke URL: {invoke_url}")
        logger.debug(f"Request data: {request_data}")

        # Get image data from request
        image_data_url = request_data.get("image_data_url")
        if not image_data_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="image_data_url is required for PaddleOCR inference",
            )

        # Perform OCR inference
        response_data = extract_text_from_image(image_data_url, invoke_url, headers)
        logger.info(f"PaddleOCR inference successful for {nim_id}")

        # Create visualization if we have results
        if response_data.get("data"):
            try:
                # Create output directory
                request_id = inference_request.request_id
                media_dir = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "media"
                )
                paddleocr_dir = os.path.join(media_dir, "paddleocr", request_id)
                os.makedirs(paddleocr_dir, exist_ok=True)

                output_path = os.path.join(paddleocr_dir, "0.png")

                # Create visualization
                visualize_text_detections(image_data_url, response_data, output_path)

                # Add visualization path to response
                response_data["visualization_path"] = output_path
                logger.info(f"Created visualization at: {output_path}")

            except Exception as viz_error:
                logger.warning(f"Failed to create visualization: {viz_error}")
                # Don't fail the entire request if visualization fails

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
        error_msg = f"PaddleOCR inference timeout for {nim_id}"
        logger.error(error_msg)

        # Update inference request with timeout error
        inference_request.status = "error"
        inference_request.set_error(
            {"error": "Request timeout", "nim_id": nim_id, "timeout_seconds": 60}
        )
        inference_request.update_timestamp()
        inference_request.save()

        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=error_msg
        )

    except requests.exceptions.RequestException as e:
        error_msg = f"PaddleOCR inference request failed for {nim_id}: {str(e)}"
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
        error_msg = f"Unexpected error during PaddleOCR inference for {nim_id}: {str(e)}"
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
    elif nim_type == "asr":
        return await perform_asr_inference(
            nim_id, request_data, inference_request, use_nvidia_api
        )
    elif nim_type == "speech_enhancement":
        return await perform_speech_enhancement_inference(
            nim_id, request_data, inference_request, use_nvidia_api
        )
    elif nim_type == "paddleocr":
        return await perform_paddleocr_inference(
            nim_id, request_data, inference_request, use_nvidia_api
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"NIM type '{nim_type}' is not supported for inference",
        )
