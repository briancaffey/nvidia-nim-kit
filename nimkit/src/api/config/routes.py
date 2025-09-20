"""API routes for NIM configuration."""

import logging
import yaml
from pathlib import Path
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, status

from .nims import NIMData, NIMDataUpdate, nim_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/nims", tags=["nims"])


@router.get("/catalog", response_model=List[Dict[str, Any]])
async def get_nims_catalog() -> List[Dict[str, Any]]:
    """Get the NIMs catalog from nims.yml file."""
    try:
        # Get the path to nims.yml relative to this file
        current_dir = Path(__file__).parent
        nims_file = current_dir.parent / "nims.yml"

        if not nims_file.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="NIMs catalog file not found"
            )

        with open(nims_file, 'r', encoding='utf-8') as f:
            nims_data = yaml.safe_load(f)

        return nims_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reading NIMs catalog: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.get("/catalog/{nim_id:path}", response_model=Dict[str, Any])
async def get_nim_details(nim_id: str) -> Dict[str, Any]:
    """Get details for a specific NIM by ID."""
    try:
        # Get the path to nims.yml relative to this file
        current_dir = Path(__file__).parent
        nims_file = current_dir.parent / "nims.yml"

        if not nims_file.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="NIMs catalog file not found"
            )

        with open(nims_file, 'r', encoding='utf-8') as f:
            nims_data = yaml.safe_load(f)

        # Find the NIM with the matching ID
        for nim in nims_data:
            if nim.get('id') == nim_id:
                return nim

        # If not found, return 404
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"NIM with ID '{nim_id}' not found"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reading NIM details for {nim_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.get("/", response_model=Dict[str, Any])
async def list_nims() -> Dict[str, Any]:
    """List all NIM IDs."""
    try:
        nim_ids = nim_manager.list_nim_ids()
        return {"nim_ids": nim_ids, "count": len(nim_ids), "status": "success"}
    except Exception as e:
        logger.error(f"Error listing NIMs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.post("/{nim_id:path}", response_model=Dict[str, Any])
async def set_nim_data(nim_id: str, nim_data: NIMDataUpdate) -> Dict[str, Any]:
    """Set NIM data for a given NIM ID."""
    try:
        success = nim_manager.set_nim_data(
            nim_id=nim_id,
            host=nim_data.host,
            port=nim_data.port,
            nim_type=nim_data.nim_type,
        )

        if success:
            return {
                "nim_id": nim_id,
                "host": nim_data.host,
                "port": nim_data.port,
                "nim_type": nim_data.nim_type,
                "status": "success",
                "message": f"NIM data set successfully for {nim_id}",
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to set NIM data for {nim_id}",
            )
    except Exception as e:
        logger.error(f"Error setting NIM data for {nim_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.get("/{nim_id:path}", response_model=Dict[str, Any])
async def get_nim_data(nim_id: str) -> Dict[str, Any]:
    """Get NIM data for a given NIM ID."""
    try:
        nim_data = nim_manager.get_nim_data(nim_id)

        if nim_data:
            return {
                "nim_id": nim_data.nim_id,
                "host": nim_data.host,
                "port": nim_data.port,
                "nim_type": nim_data.nim_type,
                "status": "success",
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"NIM data not found for {nim_id}",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting NIM data for {nim_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.put("/{nim_id:path}", response_model=Dict[str, Any])
async def update_nim_data(nim_id: str, nim_data: NIMDataUpdate) -> Dict[str, Any]:
    """Update NIM data for a given NIM ID."""
    try:
        # Check if NIM data exists
        existing_data = nim_manager.get_nim_data(nim_id)
        if not existing_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"NIM data not found for {nim_id}",
            )

        success = nim_manager.set_nim_data(
            nim_id=nim_id,
            host=nim_data.host,
            port=nim_data.port,
            nim_type=nim_data.nim_type,
        )

        if success:
            return {
                "nim_id": nim_id,
                "host": nim_data.host,
                "port": nim_data.port,
                "nim_type": nim_data.nim_type,
                "status": "success",
                "message": f"NIM data updated successfully for {nim_id}",
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update NIM data for {nim_id}",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating NIM data for {nim_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.delete("/{nim_id:path}", response_model=Dict[str, Any])
async def delete_nim_data(nim_id: str) -> Dict[str, Any]:
    """Delete NIM data for a given NIM ID."""
    try:
        success = nim_manager.delete_nim_data(nim_id)

        if success:
            return {
                "nim_id": nim_id,
                "status": "success",
                "message": f"NIM data deleted successfully for {nim_id}",
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"NIM data not found for {nim_id}",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting NIM data for {nim_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )
