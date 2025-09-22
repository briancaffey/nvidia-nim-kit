"""Image conversion API endpoints for canny edge detection and depth mapping."""

import base64
import io
import logging
from typing import Dict, Any

import cv2
import numpy as np
import torch
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v0/image-conversion", tags=["image-conversion"])


class ImageConversionRequest(BaseModel):
    """Request body for image conversion."""

    image_data: str  # Base64 encoded image data URL
    conversion_type: str  # "canny" or "depth"
    # Canny edge detection parameters
    canny_lower_threshold: float = 0.7  # Lower threshold multiplier (0.0-1.0)
    canny_upper_threshold: float = 1.3  # Upper threshold multiplier (0.0-2.0)
    canny_blur_kernel_size: int = 5  # Gaussian blur kernel size (must be odd)
    canny_blur_sigma: float = 0.0  # Gaussian blur sigma (0 = auto)


class ImageConversionResponse(BaseModel):
    """Response body for image conversion."""

    converted_image_data: str  # Base64 encoded converted image data URL
    original_dimensions: Dict[str, int]  # {"width": int, "height": int}
    converted_dimensions: Dict[str, int]  # {"width": int, "height": int}


def decode_base64_image(image_data: str) -> np.ndarray:
    """🎯 Decode base64 image data URL to OpenCV image array."""
    try:
        logger.debug("🎯 Starting base64 image decoding")

        # Remove data URL prefix if present
        if image_data.startswith('data:image/'):
            image_data = image_data.split(',')[1]

        # Decode base64
        image_bytes = base64.b64decode(image_data)
        logger.debug(f"🎯 Decoded {len(image_bytes)} bytes from base64")

        # Convert to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        logger.debug(f"🎯 Created numpy array with {len(nparr)} elements")

        # Decode image
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("❌ Failed to decode image from bytes")

        logger.debug(f"🎯 Successfully decoded image with shape: {image.shape}")
        return image

    except Exception as e:
        logger.error(f"❌ Error decoding base64 image: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to decode image: {str(e)}"
        )


def encode_image_to_base64(image: np.ndarray, format: str = "jpeg") -> str:
    """🎯 Encode OpenCV image array to base64 data URL."""
    try:
        logger.debug(f"🎯 Starting image encoding to {format}")

        # Encode image
        if format.lower() == "jpeg":
            _, buffer = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 90])
        elif format.lower() == "png":
            _, buffer = cv2.imencode('.png', image)
        else:
            raise ValueError(f"❌ Unsupported format: {format}")

        logger.debug(f"🎯 Encoded image to buffer with {len(buffer)} bytes")

        # Convert to base64
        image_base64 = base64.b64encode(buffer).decode('utf-8')
        logger.debug(f"🎯 Created base64 string with {len(image_base64)} characters")

        # Create data URL
        data_url = f"data:image/{format.lower()};base64,{image_base64}"
        logger.debug("🎯 Successfully created data URL")

        return data_url

    except Exception as e:
        logger.error(f"❌ Error encoding image to base64: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to encode image: {str(e)}"
        )


def convert_to_canny(
    image: np.ndarray,
    lower_threshold: float = 0.7,
    upper_threshold: float = 1.3,
    blur_kernel_size: int = 5,
    blur_sigma: float = 0.0
) -> np.ndarray:
    """🔍 Convert image to canny edge detection with configurable parameters."""
    try:
        logger.debug("🔍 Starting canny edge detection conversion")

        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        logger.debug(f"🔍 Converted to grayscale with shape: {gray.shape}")

        # Apply Gaussian blur to reduce noise
        # Ensure kernel size is odd
        if blur_kernel_size % 2 == 0:
            blur_kernel_size += 1

        # Use auto sigma if not specified
        sigma = blur_sigma if blur_sigma > 0 else 0

        blurred = cv2.GaussianBlur(gray, (blur_kernel_size, blur_kernel_size), sigma)
        logger.debug(f"🔍 Applied Gaussian blur with kernel size {blur_kernel_size} and sigma {sigma}")

        # Apply Canny edge detection with configurable thresholds
        median_val = np.median(blurred)
        lower = int(max(0, lower_threshold * median_val))
        upper = int(min(255, upper_threshold * median_val))

        edges = cv2.Canny(blurred, lower, upper)
        logger.debug(f"🔍 Applied Canny edge detection with thresholds: {lower}, {upper} (multipliers: {lower_threshold}, {upper_threshold})")

        # Convert back to 3-channel for consistency
        edges_bgr = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
        logger.debug("🔍 Converted edges back to BGR format")

        logger.info("✅ Canny edge detection completed successfully")
        return edges_bgr

    except Exception as e:
        logger.error(f"❌ Error in canny edge detection: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Canny edge detection failed: {str(e)}"
        )


@torch.inference_mode()
def run_midas(image_bgr: np.ndarray, model_type: str = "dpt_hybrid", device: str = "cpu") -> np.ndarray:
    """🗺️ Run MiDaS depth estimation on image."""
    try:
        logger.debug(f"🗺️ Starting MiDaS depth estimation with model: {model_type}")
        logger.debug(f"🗺️ Using device: {device}")

        # Load MiDaS model + transforms via torch.hub
        repo = "intel-isl/MiDaS"
        model_name = {
            "dpt_large": "DPT_Large",
            "dpt_hybrid": "DPT_Hybrid",
            "midas_small": "MiDaS_small",
        }[model_type]

        logger.debug(f"🗺️ Loading model: {model_name} from {repo}")
        model = torch.hub.load(repo, model_name, pretrained=True).to(device)
        model.eval()
        logger.debug("🗺️ Model loaded and set to eval mode")

        transforms = torch.hub.load(repo, "transforms")
        if model_type in ["dpt_large", "dpt_hybrid"]:
            transform = transforms.dpt_transform
        else:
            transform = transforms.small_transform
        logger.debug(f"🗺️ Loaded transforms for {model_type}")

        # Prepare input (RGB)
        img_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        logger.debug(f"🗺️ Converted to RGB with shape: {img_rgb.shape}")

        input_batch = transform(img_rgb).to(device)
        logger.debug(f"🗺️ Prepared input batch with shape: {input_batch.shape}")

        # Predict
        logger.debug("🗺️ Running depth prediction...")
        prediction = model(input_batch)
        logger.debug(f"🗺️ Got prediction with shape: {prediction.shape}")

        prediction = torch.nn.functional.interpolate(
            prediction.unsqueeze(1),
            size=img_rgb.shape[:2],
            mode="bicubic",
            align_corners=False,
        ).squeeze(1)
        logger.debug(f"🗺️ Interpolated prediction to original size: {prediction.shape}")

        depth = prediction.squeeze().float().cpu().numpy()
        logger.debug(f"🗺️ Final depth map shape: {depth.shape}")

        logger.info("✅ MiDaS depth estimation completed successfully")
        return depth

    except Exception as e:
        logger.error(f"❌ Error in MiDaS depth estimation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"MiDaS depth estimation failed: {str(e)}"
        )


def normalize_depth(depth: np.ndarray, invert: bool = True) -> np.ndarray:
    """🗺️ Normalize depth to 0..255 uint8 for visualization."""
    try:
        logger.debug("🗺️ Starting depth normalization")

        d = depth.copy()
        # Robust normalization to reduce influence of outliers
        d_min = np.percentile(d, 2)
        d_max = np.percentile(d, 98)
        logger.debug(f"🗺️ Depth range: {d_min:.3f} to {d_max:.3f}")

        d = np.clip(d, d_min, d_max)
        if invert:
            d = d_max - (d - d_min)
        else:
            d = d - d_min
        d = d / (d_max - d_min + 1e-8)
        d8 = (d * 255.0).astype(np.uint8)

        logger.debug("🗺️ Depth normalization completed")
        return d8

    except Exception as e:
        logger.error(f"❌ Error in depth normalization: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Depth normalization failed: {str(e)}"
        )


def enhance_depth_gray(gray: np.ndarray, bilateral: bool = False) -> np.ndarray:
    """🗺️ Enhance depth map for better visualization."""
    try:
        logger.debug("🗺️ Starting depth enhancement")

        out = gray
        # Contrast Limited Adaptive Histogram Equalization for clearer edges
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        out = clahe.apply(out)
        logger.debug("🗺️ Applied CLAHE enhancement")

        if bilateral:
            # Gentle smoothing while preserving edges
            out = cv2.bilateralFilter(out, d=7, sigmaColor=50, sigmaSpace=7)
            logger.debug("🗺️ Applied bilateral filtering")

        logger.debug("🗺️ Depth enhancement completed")
        return out

    except Exception as e:
        logger.error(f"❌ Error in depth enhancement: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Depth enhancement failed: {str(e)}"
        )


def convert_to_depth(image: np.ndarray) -> np.ndarray:
    """🗺️ Convert image to depth map using MiDaS."""
    try:
        logger.debug("🗺️ Starting depth map conversion")

        # Determine device
        device = "cpu" if not torch.cuda.is_available() else "cuda"
        logger.debug(f"🗺️ Using device: {device}")

        # Run MiDaS depth estimation
        depth = run_midas(image, model_type="dpt_hybrid", device=device)

        # Normalize depth
        depth_gray = normalize_depth(depth, invert=True)
        logger.debug("🗺️ Normalized depth to grayscale")

        # Enhance depth
        depth_gray = enhance_depth_gray(depth_gray, bilateral=True)
        logger.debug("🗺️ Enhanced depth map")

        # Convert to 3-channel grayscale for consistency with other outputs
        depth_bgr = cv2.cvtColor(depth_gray, cv2.COLOR_GRAY2BGR)
        logger.debug("🗺️ Converted to BGR format")

        logger.info("✅ Depth map conversion completed successfully")
        return depth_bgr

    except Exception as e:
        logger.error(f"❌ Error in depth map conversion: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Depth map conversion failed: {str(e)}"
        )


@router.post("/convert", response_model=ImageConversionResponse)
async def convert_image(request: ImageConversionRequest) -> ImageConversionResponse:
    """
    🎨 Convert image to canny edges or depth map.

    Args:
        request: Image conversion request with base64 image data and conversion type

    Returns:
        ImageConversionResponse with converted image data and dimensions
    """
    logger.info(f"🎨 Starting image conversion request: {request.conversion_type}")

    try:
        # Validate conversion type
        if request.conversion_type not in ["canny", "depth"]:
            logger.error(f"❌ Invalid conversion type: {request.conversion_type}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Conversion type must be 'canny' or 'depth'"
            )

        logger.debug(f"🎨 Valid conversion type: {request.conversion_type}")

        # Decode input image
        logger.debug("🎨 Decoding input image...")
        original_image = decode_base64_image(request.image_data)
        original_height, original_width = original_image.shape[:2]
        logger.debug(f"🎨 Original image dimensions: {original_width}x{original_height}")

        # Perform conversion
        if request.conversion_type == "canny":
            logger.info("🔍 Converting to canny edge detection")
            converted_image = convert_to_canny(
                original_image,
                lower_threshold=request.canny_lower_threshold,
                upper_threshold=request.canny_upper_threshold,
                blur_kernel_size=request.canny_blur_kernel_size,
                blur_sigma=request.canny_blur_sigma
            )
        elif request.conversion_type == "depth":
            logger.info("🗺️ Converting to depth map")
            converted_image = convert_to_depth(original_image)

        converted_height, converted_width = converted_image.shape[:2]
        logger.debug(f"🎨 Converted image dimensions: {converted_width}x{converted_height}")

        # Encode converted image
        logger.debug("🎨 Encoding converted image...")
        converted_image_data = encode_image_to_base64(converted_image, "jpeg")

        logger.info(f"✅ Image conversion completed successfully: {request.conversion_type}")

        return ImageConversionResponse(
            converted_image_data=converted_image_data,
            original_dimensions={"width": original_width, "height": original_height},
            converted_dimensions={"width": converted_width, "height": converted_height}
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error in image conversion: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image conversion failed: {str(e)}"
        )
