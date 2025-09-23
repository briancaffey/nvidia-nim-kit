"""Utility functions for NVIDIA API integration."""

import os
import yaml
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from fastapi import HTTPException, status
from .db import get_redis_client
from .config.nims import nim_manager


def get_nvidia_api_key() -> Optional[str]:
    """
    Get NVIDIA API key from Redis or environment variable.

    Returns:
        Optional[str]: The NVIDIA API key if found, None otherwise.
    """
    # Try Redis first
    redis_client = get_redis_client()
    if redis_key := redis_client.get("nims:nvidia_api_key"):
        return redis_key

    # Fall back to environment variable
    return os.getenv("NVIDIA_API_KEY")


def set_nvidia_api_key(api_key: str) -> bool:
    """
    Set NVIDIA API key in Redis with validation.

    Args:
        api_key (str): The API key to store

    Returns:
        bool: True if successful, False otherwise
    """
    # Validate API key format
    if not api_key.startswith("nvapi-"):
        return False

    try:
        redis_client = get_redis_client()
        redis_client.set("nims:nvidia_api_key", api_key)
        return True
    except Exception:
        return False


def delete_nvidia_api_key() -> bool:
    """
    Delete NVIDIA API key from Redis.

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        redis_client = get_redis_client()
        redis_client.delete("nims:nvidia_api_key")
        return True
    except Exception:
        return False


def get_nvidia_api_key_preview() -> str:
    """
    Get a preview of the NVIDIA API key (first 10 characters + ...).

    Returns:
        str: Preview of the API key or "No API key configured"
    """
    api_key = get_nvidia_api_key()
    if api_key:
        return f"{api_key[:10]}..."
    return "No API key configured"


def get_nvidia_api_key_source() -> str:
    """
    Get the source of the NVIDIA API key (redis, env, or none).

    Returns:
        str: "redis", "env", or "none"
    """
    redis_client = get_redis_client()
    if redis_client.get("nims:nvidia_api_key"):
        return "redis"
    elif os.getenv("NVIDIA_API_KEY"):
        return "env"
    return "none"


def get_nvidia_api_headers() -> dict:
    """
    Get headers for NVIDIA API requests with Authorization header.

    Returns:
        dict: Headers with Authorization if API key is available, empty dict otherwise
    """
    api_key = get_nvidia_api_key()
    if api_key:
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
    return {"Content-Type": "application/json", "Accept": "application/json"}


def validate_nim_exists(nim_id: str) -> Tuple[Any, Dict[str, Any]]:
    """
    Validate that a NIM exists and return both NIM data and metadata.

    Args:
        nim_id: The NIM ID in format 'publisher/model_name'

    Returns:
        Tuple of (nim_data, nim_metadata)

    Raises:
        HTTPException: If NIM is not found
    """
    # Get NIM data from Redis
    nim_data = nim_manager.get_nim_data(nim_id)
    if not nim_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"NIM {nim_id} not found in configuration",
        )

    # Get NIM metadata from nims.yml
    try:
        current_dir = Path(__file__).parent
        nims_file = current_dir / "nims.yml"

        if not nims_file.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="NIMs catalog file not found",
            )

        with open(nims_file, "r", encoding="utf-8") as f:
            nims_data = yaml.safe_load(f)

        # Find the NIM with the matching ID
        nim_metadata = None
        for nim in nims_data:
            if nim.get("id") == nim_id:
                nim_metadata = nim
                break

        if not nim_metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"NIM {nim_id} not found in catalog",
            )

        return nim_data, nim_metadata

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error loading NIM metadata: {str(e)}",
        )
