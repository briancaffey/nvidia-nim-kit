"""Utility functions for NIM configuration."""

import logging
from typing import Optional, Tuple

from .nims import nim_manager

logger = logging.getLogger(__name__)


def get_nim_endpoint(nim_id: str) -> Optional[Tuple[str, int]]:
    """
    Get the host and port for a NIM by its ID.

    Args:
        nim_id: The unique identifier for the NIM

    Returns:
        Tuple of (host, port) if found, None otherwise
    """
    try:
        nim_data = nim_manager.get_nim_data(nim_id)
        if nim_data:
            return (nim_data.host, nim_data.port)
        return None
    except Exception as e:
        logger.error(f"Error getting NIM endpoint for {nim_id}: {e}")
        return None


def get_nim_host(nim_id: str) -> Optional[str]:
    """
    Get the host for a NIM by its ID.

    Args:
        nim_id: The unique identifier for the NIM

    Returns:
        Host string if found, None otherwise
    """
    try:
        nim_data = nim_manager.get_nim_data(nim_id)
        if nim_data:
            return nim_data.host
        return None
    except Exception as e:
        logger.error(f"Error getting NIM host for {nim_id}: {e}")
        return None


def get_nim_port(nim_id: str) -> Optional[int]:
    """
    Get the port for a NIM by its ID.

    Args:
        nim_id: The unique identifier for the NIM

    Returns:
        Port number if found, None otherwise
    """
    try:
        nim_data = nim_manager.get_nim_data(nim_id)
        if nim_data:
            return nim_data.port
        return None
    except Exception as e:
        logger.error(f"Error getting NIM port for {nim_id}: {e}")
        return None


def get_nim_url(nim_id: str, protocol: str = "http") -> Optional[str]:
    """
    Get the full URL for a NIM by its ID.

    Args:
        nim_id: The unique identifier for the NIM
        protocol: The protocol to use (default: "http")

    Returns:
        Full URL string if found, None otherwise
    """
    try:
        endpoint = get_nim_endpoint(nim_id)
        if endpoint:
            host, port = endpoint
            return f"{protocol}://{host}:{port}"
        return None
    except Exception as e:
        logger.error(f"Error getting NIM URL for {nim_id}: {e}")
        return None


def is_nim_available(nim_id: str) -> bool:
    """
    Check if NIM data is available for a given NIM ID.

    Args:
        nim_id: The unique identifier for the NIM

    Returns:
        True if NIM data exists, False otherwise
    """
    try:
        nim_data = nim_manager.get_nim_data(nim_id)
        return nim_data is not None
    except Exception as e:
        logger.error(f"Error checking NIM availability for {nim_id}: {e}")
        return False
