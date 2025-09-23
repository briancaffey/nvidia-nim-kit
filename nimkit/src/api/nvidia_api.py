"""NVIDIA API key management endpoints."""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status

from .utils import (
    get_nvidia_api_key_preview,
    set_nvidia_api_key,
    delete_nvidia_api_key,
    get_nvidia_api_key_source,
    get_nvidia_api_key,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/nvidia", tags=["nvidia-api"])


@router.get("/api-key", response_model=Dict[str, Any])
async def get_nvidia_api_key_status() -> Dict[str, Any]:
    """Get the status of the NVIDIA API key (preview only)."""
    try:
        preview = get_nvidia_api_key_preview()
        has_key = preview != "No API key configured"
        source = get_nvidia_api_key_source()

        return {
            "preview": preview,
            "has_key": has_key,
            "source": source,
            "status": "success",
        }
    except Exception as e:
        logger.error(f"Error getting NVIDIA API key status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.post("/api-key", response_model=Dict[str, Any])
async def set_nvidia_api_key_endpoint(api_key_data: Dict[str, str]) -> Dict[str, Any]:
    """Set the NVIDIA API key in Redis."""
    try:
        api_key = api_key_data.get("api_key", "").strip()

        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="API key is required"
            )

        if not api_key.startswith("nvapi-"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="API key must start with 'nvapi-'",
            )

        success = set_nvidia_api_key(api_key)

        if success:
            return {
                "status": "success",
                "message": "NVIDIA API key set successfully",
                "preview": f"{api_key[:10]}...",
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to set NVIDIA API key",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting NVIDIA API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.delete("/api-key", response_model=Dict[str, Any])
async def delete_nvidia_api_key_endpoint() -> Dict[str, Any]:
    """Delete the NVIDIA API key from Redis."""
    try:
        success = delete_nvidia_api_key()

        if success:
            return {
                "status": "success",
                "message": "NVIDIA API key deleted successfully",
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete NVIDIA API key",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting NVIDIA API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.get("/toggle", response_model=Dict[str, Any])
async def get_nvidia_api_toggle() -> Dict[str, Any]:
    """Get the NVIDIA API toggle state."""
    try:
        from .db import get_redis_client

        # Check if API key is available
        api_key = get_nvidia_api_key()
        if not api_key:
            # No API key available, toggle should be False
            return {
                "enabled": False,
                "can_enable": False,
                "reason": "No NVIDIA API key configured",
            }

        # Get toggle state from Redis
        redis_client = get_redis_client()
        toggle_state = redis_client.get("nims:nvidia_api_toggle")

        enabled = toggle_state == "true" if toggle_state else False

        return {"enabled": enabled, "can_enable": True, "reason": None}
    except Exception as e:
        logger.error(f"Error getting NVIDIA API toggle: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.post("/toggle", response_model=Dict[str, Any])
async def set_nvidia_api_toggle(toggle_data: Dict[str, bool]) -> Dict[str, Any]:
    """Set the NVIDIA API toggle state."""
    try:
        from .db import get_redis_client

        # Check if API key is available
        api_key = get_nvidia_api_key()
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot enable NVIDIA API without a configured API key",
            )

        enabled = toggle_data.get("enabled", False)

        # Store toggle state in Redis
        redis_client = get_redis_client()
        redis_client.set("nims:nvidia_api_toggle", str(enabled).lower())

        return {"enabled": enabled, "can_enable": True, "status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting NVIDIA API toggle: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )
