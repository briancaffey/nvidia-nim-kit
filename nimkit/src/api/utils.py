"""Utility functions for NIM operations."""

import logging
import yaml
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from fastapi import HTTPException, status

from .db import get_redis_client
from .config.nims import NIMData

logger = logging.getLogger(__name__)


def get_nim_info(nim_id: str) -> Tuple[Optional[NIMData], Optional[Dict[str, Any]]]:
    """
    Get NIM information from both Redis (host/port) and YAML (metadata).

    Args:
        nim_id: The NIM ID in format 'publisher/model_name'

    Returns:
        Tuple of (NIMData from Redis, NIM metadata from YAML)
    """
    # Get NIM data from Redis
    redis_client = get_redis_client()
    nim_data = None

    try:
        key = f"nim:{nim_id}"
        data = redis_client.get(key)
        if data:
            import json
            nim_data_dict = json.loads(data)
            nim_data = NIMData(**nim_data_dict)
    except Exception as e:
        logger.error(f"Failed to get NIM data from Redis for {nim_id}: {e}")

    # Get NIM metadata from YAML
    nim_metadata = None
    try:
        current_dir = Path(__file__).parent
        nims_file = current_dir / "nims.yml"

        if nims_file.exists():
            with open(nims_file, 'r', encoding='utf-8') as f:
                nims_data = yaml.safe_load(f)

            # Find the NIM with matching ID
            for nim in nims_data:
                if nim.get('id') == nim_id:
                    nim_metadata = nim
                    break
    except Exception as e:
        logger.error(f"Failed to get NIM metadata from YAML for {nim_id}: {e}")

    return nim_data, nim_metadata


def validate_nim_exists(nim_id: str) -> Tuple[NIMData, Dict[str, Any]]:
    """
    Validate that a NIM exists and return its data.

    Args:
        nim_id: The NIM ID in format 'publisher/model_name'

    Returns:
        Tuple of (NIMData from Redis, NIM metadata from YAML)

    Raises:
        HTTPException: If NIM is not found or not properly configured
    """
    nim_data, nim_metadata = get_nim_info(nim_id)

    if not nim_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"NIM {nim_id} not found in Redis configuration"
        )

    if not nim_metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"NIM {nim_id} not found in catalog"
        )

    return nim_data, nim_metadata
