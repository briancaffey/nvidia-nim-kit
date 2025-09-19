"""Health check endpoints for LLM service."""

import logging
from datetime import datetime
from typing import Dict, Any

import httpx
from fastapi import APIRouter, HTTPException

# Set up logging
logger = logging.getLogger(__name__)

# Base URL for the external LLM service (will be moved to config later)
LLM_SERVICE_BASE_URL = "http://192.168.5.173:8000"

# Create router for health endpoints
router = APIRouter()


@router.get("/v1/health/ready")
async def health_ready() -> Dict[str, Any]:
    """Health ready endpoint - checks if the external LLM service is ready to accept requests."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{LLM_SERVICE_BASE_URL}/v1/health/ready")
            response.raise_for_status()

            return {
                "status": "ready",
                "timestamp": datetime.utcnow().isoformat(),
                "service": "nvidia-nim-kit",
                "external_service": "healthy",
                "external_response": response.json() if response.content else None,
            }
    except httpx.TimeoutException:
        logger.error("Timeout when checking external LLM service readiness")
        raise HTTPException(status_code=503, detail="External LLM service timeout")
    except httpx.HTTPStatusError as e:
        logger.error(f"External LLM service returned error: {e.response.status_code}")
        raise HTTPException(
            status_code=503,
            detail=f"External LLM service error: {e.response.status_code}",
        )
    except Exception as e:
        logger.error(f"Error checking external LLM service readiness: {str(e)}")
        raise HTTPException(status_code=503, detail="External LLM service unavailable")


@router.get("/v1/health/live")
async def health_live() -> Dict[str, Any]:
    """Health live endpoint - checks if the external LLM service is alive."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{LLM_SERVICE_BASE_URL}/v1/health/live")
            response.raise_for_status()

            return {
                "status": "live",
                "timestamp": datetime.utcnow().isoformat(),
                "service": "nvidia-nim-kit",
                "external_service": "healthy",
                "external_response": response.json() if response.content else None,
            }
    except httpx.TimeoutException:
        logger.error("Timeout when checking external LLM service liveness")
        raise HTTPException(status_code=503, detail="External LLM service timeout")
    except httpx.HTTPStatusError as e:
        logger.error(f"External LLM service returned error: {e.response.status_code}")
        raise HTTPException(
            status_code=503,
            detail=f"External LLM service error: {e.response.status_code}",
        )
    except Exception as e:
        logger.error(f"Error checking external LLM service liveness: {str(e)}")
        raise HTTPException(status_code=503, detail="External LLM service unavailable")
