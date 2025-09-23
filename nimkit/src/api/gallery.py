"""Gallery API endpoints for displaying inference requests."""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Query, HTTPException, status

from .llm.models import InferenceRequest
from .db import get_redis_client
from redis_om import Migrator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/gallery", tags=["gallery"])


@router.get("/inference-requests", response_model=Dict[str, Any])
async def get_inference_requests(
    limit: int = Query(
        default=10, ge=1, le=100, description="Number of results to return"
    ),
    offset: int = Query(default=0, ge=0, description="Number of results to skip"),
    search: Optional[str] = Query(
        default=None, description="Search term to filter results"
    ),
    nim_ids: Optional[str] = Query(
        default=None, description="Comma-separated list of NIM IDs to filter by"
    ),
) -> Dict[str, Any]:
    """
    Get paginated inference requests with optional filtering.

    Args:
        limit: Maximum number of results to return (1-100)
        offset: Number of results to skip for pagination
        search: Optional search term to filter by (searches input/output JSON)
        nim_ids: Optional comma-separated list of NIM IDs to filter by

    Returns:
        Dictionary containing the inference requests, pagination info, and metadata
    """
    logger.info(
        f"Gallery request: limit={limit}, offset={offset}, search='{search}', nim_ids='{nim_ids}'"
    )

    try:
        # Create index if it doesn't exist
        try:
            Migrator().run()
            logger.debug("Redis index created/verified successfully")
        except Exception as e:
            logger.warning(f"Failed to create Redis index: {e}")

        # Get all inference requests using direct Redis query since redis-om find().all() seems limited
        logger.debug("Fetching all inference requests from Redis using direct query")
        redis_client = get_redis_client()

        # Get all InferenceRequest keys
        pattern = ":nimkit.src.api.llm.models.InferenceRequest:*"
        keys = redis_client.keys(pattern)
        # Filter out the index key
        keys = [key for key in keys if not key.endswith(":index:hash")]

        logger.debug(f"Found {len(keys)} inference request keys in Redis")

        # Load all inference requests
        all_results = []
        for key in keys:
            try:
                # Get the hash data
                hash_data = redis_client.hgetall(key)
                if hash_data:
                    # Convert bytes to strings
                    data = {
                        k.decode("utf-8") if isinstance(k, bytes) else k: (
                            v.decode("utf-8") if isinstance(v, bytes) else v
                        )
                        for k, v in hash_data.items()
                    }

                    # Create InferenceRequest object from the data
                    request = InferenceRequest(**data)
                    all_results.append(request)
            except Exception as e:
                logger.warning(f"Failed to load inference request from key {key}: {e}")
                continue

        # Apply filters in Python
        filtered_results = []

        for request in all_results:
            # Apply NIM ID filter
            if nim_ids:
                nim_id_list = [
                    nim_id.strip() for nim_id in nim_ids.split(",") if nim_id.strip()
                ]
                if nim_id_list and request.nim_id not in nim_id_list:
                    continue

            # Apply search filter
            if search:
                search_term = search.lower()
                # Search in input_json and output_json fields
                input_matches = search_term in (request.input_json or "").lower()
                output_matches = search_term in (request.output_json or "").lower()
                if not input_matches and not output_matches:
                    continue

            filtered_results.append(request)

        logger.debug(f"After filtering: {len(filtered_results)} results")

        # Sort by date_created descending (most recent first) in Python
        filtered_results.sort(key=lambda x: x.date_created, reverse=True)

        # Apply pagination manually since redis-om doesn't have built-in pagination
        total_count = len(filtered_results)
        paginated_results = filtered_results[offset : offset + limit]

        logger.info(
            f"Query returned {total_count} total results, returning {len(paginated_results)} results"
        )

        # Convert InferenceRequest objects to dictionaries for JSON serialization
        serialized_results = []
        for request in paginated_results:
            try:
                # Get the basic request data
                request_data = {
                    "request_id": request.request_id,
                    "type": request.type,
                    "request_type": request.request_type,
                    "nim_id": request.nim_id,
                    "model": request.model,
                    "stream": request.get_stream(),
                    "status": request.status,
                    "date_created": request.date_created,
                    "date_updated": request.date_updated,
                }

                # Add parsed input/output data
                try:
                    request_data["input_data"] = request.get_input()
                except Exception as e:
                    logger.warning(
                        f"Failed to parse input data for request {request.request_id}: {e}"
                    )
                    request_data["input_data"] = {}

                try:
                    request_data["output_data"] = request.get_output()
                except Exception as e:
                    logger.warning(
                        f"Failed to parse output data for request {request.request_id}: {e}"
                    )
                    request_data["output_data"] = {}

                try:
                    request_data["error_data"] = request.get_error()
                except Exception as e:
                    logger.warning(
                        f"Failed to parse error data for request {request.request_id}: {e}"
                    )
                    request_data["error_data"] = {}

                serialized_results.append(request_data)

            except Exception as e:
                logger.error(f"Failed to serialize request {request.request_id}: {e}")
                continue

        # Calculate pagination metadata
        has_next = offset + limit < total_count
        has_previous = offset > 0
        total_pages = (total_count + limit - 1) // limit  # Ceiling division
        current_page = (offset // limit) + 1

        response_data = {
            "results": serialized_results,
            "pagination": {
                "total_count": total_count,
                "limit": limit,
                "offset": offset,
                "current_page": current_page,
                "total_pages": total_pages,
                "has_next": has_next,
                "has_previous": has_previous,
            },
            "filters": {
                "search": search,
                "nim_ids": nim_ids,
            },
            "status": "success",
        }

        logger.info(
            f"Successfully returned {len(serialized_results)} inference requests"
        )
        return response_data

    except Exception as e:
        logger.error(f"Error fetching inference requests: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch inference requests: {str(e)}",
        )
