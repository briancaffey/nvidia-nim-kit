"""PaddleOCR utility functions for text detection and visualization."""

import base64
import io
import json
import logging
import os
import requests
from typing import Dict, Any, List, Tuple
from PIL import Image, ImageDraw, ImageFont
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


def encode_image_to_base64(image_source: str) -> str:
    """
    Encode an image to base64 data URL.

    Args:
        image_source: A URL or a local file path

    Returns:
        A base64-encoded data URL
    """
    try:
        # Check if the source is a URL or local file
        if image_source.startswith(("http://", "https://")):
            # Handle remote URL
            response = requests.get(image_source)
            response.raise_for_status()
            image_bytes = response.content
        else:
            # Handle local file
            with open(image_source, "rb") as f:
                image_bytes = f.read()

        # Encode to base64
        base64_image = base64.b64encode(image_bytes).decode("utf-8")
        return f"data:image/jpeg;base64,{base64_image}"

    except Exception as e:
        logger.error(f"Failed to encode image to base64: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to encode image: {str(e)}",
        )


def extract_text_from_image(
    image_data_url: str, api_endpoint: str, headers: Dict[str, str]
) -> Dict[str, Any]:
    """
    Extract text from images using the PaddleOCR NIM API.

    Args:
        image_data_url: Data URL of the image to process
        api_endpoint: Base URL of the NIM service
        headers: Request headers

    Returns:
        API response dict
    """
    try:
        # Prepare payload according to PaddleOCR API format
        payload = {
            "input": [
                {
                    "type": "image_url",
                    "url": image_data_url,
                }
            ]
        }

        # Make inference request
        url = f"{api_endpoint}/v1/infer"

        logger.info(f"Making PaddleOCR request to: {url}")
        logger.debug(f"Request payload: {json.dumps(payload, indent=2)}")

        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()

        result = response.json()
        logger.info("PaddleOCR inference successful")
        logger.debug(
            f"Response keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}"
        )

        return result

    except requests.exceptions.RequestException as e:
        logger.error(f"PaddleOCR API request failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"PaddleOCR API request failed: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Unexpected error in PaddleOCR inference: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PaddleOCR inference failed: {str(e)}",
        )


def visualize_text_detections(
    image_data_url: str, result: Dict[str, Any], output_path: str
) -> None:
    """
    Draw bounding boxes on the image based on API results.

    Args:
        image_data_url: Data URL of the original image
        result: PaddleOCR API response
        output_path: Path to save the annotated image
    """
    try:
        # Load image from data URL
        if image_data_url.startswith("data:"):
            # Extract base64 data after the comma
            b64_data = image_data_url.split(",")[1]
            image_bytes = base64.b64decode(b64_data)
            image = Image.open(io.BytesIO(image_bytes))
        else:
            # Download from URL
            response = requests.get(image_data_url)
            image = Image.open(io.BytesIO(response.content))

        draw = ImageDraw.Draw(image)

        # Get image dimensions
        width, height = image.size
        logger.debug(f"Image dimensions: {width}x{height}")

        # Draw detected elements
        detections_count = 0
        for detection in result.get("data", []):
            for text_detection in detection.get("text_detections", []):
                detections_count += 1

                # Get bounding box points
                box = text_detection.get("bounding_box", {}).get("points", [])
                if not box or len(box) < 4:
                    logger.warning(
                        f"Invalid bounding box for detection {detections_count}"
                    )
                    continue

                # Convert normalized coordinates to pixels
                x_coords = [point.get("x", 0) for point in box]
                y_coords = [point.get("y", 0) for point in box]

                x_min = int(min(x_coords) * width)
                y_min = int(min(y_coords) * height)
                x_max = int(max(x_coords) * width)
                y_max = int(max(y_coords) * height)

                # Draw rectangle
                draw.rectangle([x_min, y_min, x_max, y_max], outline="blue", width=3)

                # Get text and confidence
                text_prediction = text_detection.get("text_prediction", {})
                text = text_prediction.get("text", "")
                confidence = text_prediction.get("confidence", 0.0)

                # Add label with confidence
                label = f"{text}: {confidence:.2f}"

                # Try to use a font, fallback to default if not available
                try:
                    # Try to use a system font
                    font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 12)
                except (OSError, IOError):
                    try:
                        # Try alternative font path
                        font = ImageFont.truetype(
                            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12
                        )
                    except (OSError, IOError):
                        # Use default font
                        font = ImageFont.load_default()

                # Draw text background
                text_bbox = draw.textbbox((x_min, y_min - 20), label, font=font)
                draw.rectangle(text_bbox, fill="white", outline="blue")
                draw.text((x_min, y_min - 20), label, fill="blue", font=font)

        logger.info(f"Drew {detections_count} text detections on image")

        # Save the annotated image
        image.save(output_path)
        logger.info(f"Annotated image saved to {output_path}")

    except Exception as e:
        logger.error(f"Failed to visualize text detections: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create visualization: {str(e)}",
        )


def process_paddleocr_response(response_data: Dict[str, Any], request_id: str) -> str:
    """
    Process PaddleOCR response and save visualization.

    Args:
        response_data: The PaddleOCR API response
        request_id: The inference request ID to use as filename

    Returns:
        Path to the saved visualization image
    """
    try:
        # Create media/paddleocr directory structure
        media_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "media"
        )
        paddleocr_dir = os.path.join(media_dir, "paddleocr", request_id)
        os.makedirs(paddleocr_dir, exist_ok=True)
        logger.debug(f"Created PaddleOCR directory: {paddleocr_dir}")

        # For now, we'll save as 0.png (can be extended for multiple images)
        output_filename = "0.png"
        output_path = os.path.join(paddleocr_dir, output_filename)

        # Extract the original image from the response or request
        # For now, we'll need to get this from the request data
        # This is a limitation - we need the original image data
        logger.warning(
            "Visualization requires original image data - this needs to be passed from the request"
        )

        return output_path

    except Exception as e:
        logger.error(f"Failed to process PaddleOCR response: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process PaddleOCR response: {str(e)}",
        )


def create_paddleocr_payload(image_data_url: str) -> Dict[str, Any]:
    """
    Create the payload for PaddleOCR API request.

    Args:
        image_data_url: Base64 encoded image data URL

    Returns:
        Formatted payload for PaddleOCR API
    """
    return {"input": [{"type": "image_url", "url": image_data_url}]}
