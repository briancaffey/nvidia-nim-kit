"""FastAPI endpoints for querying metrics from RedisTimeSeries."""

import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from urllib.parse import parse_qs

import redis
from dateutil import parser as date_parser
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


class MetricsQueryResponse(BaseModel):
    """Response model for metrics query."""

    series: List[Dict[str, Any]]


class MetricsKeysResponse(BaseModel):
    """Response model for metrics keys discovery."""

    keys: List[Dict[str, Any]]


class MetricsAPI:
    """Handles metrics querying from RedisTimeSeries."""

    def __init__(self):
        """Initialize Redis connection."""
        self.redis_client = redis.from_url(REDIS_URL, decode_responses=True)

    def _parse_time(self, time_str: Union[str, int]) -> int:
        """Parse time string or int to milliseconds."""
        if isinstance(time_str, int):
            # Assume it's already in milliseconds if it's an int
            return time_str

        try:
            # Try parsing as ISO8601
            dt = date_parser.parse(time_str)
            return int(dt.timestamp() * 1000)
        except Exception:
            # Try parsing as milliseconds since epoch
            try:
                return int(time_str)
            except ValueError:
                raise HTTPException(
                    status_code=400, detail=f"Invalid time format: {time_str}"
                )

    def _parse_labels(self, labels_str: Optional[str]) -> List[str]:
        """Parse comma-separated label filters."""
        if not labels_str:
            return []

        filters = []
        for label_pair in labels_str.split(","):
            label_pair = label_pair.strip()
            if "=" in label_pair:
                filters.append(label_pair)
            else:
                raise HTTPException(
                    status_code=400, detail=f"Invalid label format: {label_pair}"
                )

        return filters

    def _matches_filters(self, labels_dict: Dict[str, str], filters: List[str]) -> bool:
        """Check if labels match the given filters."""
        if not filters:
            return True

        for filter_str in filters:
            if "=" not in filter_str:
                continue

            key, value = filter_str.split("=", 1)
            if labels_dict.get(key) != value:
                return False

        return True

    def _build_filter_list(
        self,
        metric: str,
        labels: List[str],
        le: Optional[str] = None,
        quantile: Optional[str] = None,
    ) -> List[str]:
        """Build RedisTimeSeries filter list."""
        filters = []

        # Add metric filter
        filters.append(f"metric={metric}")

        # Add other label filters
        filters.extend(labels)

        # Add special filters
        if le:
            filters.append(f"le={le}")
        if quantile:
            filters.append(f"quantile={quantile}")

        return filters

    def query_metrics(
        self,
        metric: str,
        start: Union[str, int],
        end: Optional[Union[str, int]] = None,
        labels: Optional[str] = None,
        le: Optional[str] = None,
        quantile: Optional[str] = None,
        agg: Optional[str] = None,
        bucket_ms: Optional[int] = None,
        limit: int = 50,
    ) -> MetricsQueryResponse:
        """Query metrics from RedisTimeSeries."""
        try:
            # Parse time parameters
            start_ms = self._parse_time(start)
            end_ms = (
                self._parse_time(end) if end else int(datetime.now().timestamp() * 1000)
            )

            # Find keys that match the metric
            pattern = f"ts:prom:{metric}:*"
            keys = self.redis_client.keys(pattern)

            logger.debug(f"Found {len(keys)} keys matching pattern: {pattern}")

            # Query each key individually using TS.RANGE
            series = []
            for key in keys[:limit]:  # Apply limit
                try:
                    # Build TS.RANGE command
                    cmd_args = ["TS.RANGE", key, start_ms, end_ms]

                    # Add aggregation if specified
                    if agg and bucket_ms:
                        if agg not in ["avg", "sum", "min", "max", "count"]:
                            raise HTTPException(
                                status_code=400, detail=f"Invalid aggregation: {agg}"
                            )
                        cmd_args.extend(["AGGREGATION", agg, bucket_ms])

                    logger.debug(f"Executing TS.RANGE command: {cmd_args}")

                    # Execute command
                    samples = self.redis_client.execute_command(*cmd_args)

                    # Extract metric name from key
                    if key.startswith("ts:prom:"):
                        remaining = key[8:]  # Remove "ts:prom:"
                        parts = remaining.split(":")
                        if len(parts) >= 2:
                            metric_name = ":".join(parts[:-1])
                        else:
                            metric_name = metric
                    else:
                        metric_name = metric

                    # Create labels dict
                    labels_dict = {"metric": metric_name}

                    series.append(
                        {"key": key, "labels": labels_dict, "samples": samples}
                    )

                except Exception as e:
                    logger.warning(f"Failed to query key {key}: {e}")
                    continue

            return MetricsQueryResponse(series=series)

        except Exception as e:
            logger.error(f"Failed to query metrics: {e}")
            raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

    def get_metrics_keys(
        self,
        metric: Optional[str] = None,
        labels: Optional[str] = None,
        le: Optional[str] = None,
        quantile: Optional[str] = None,
        limit: int = 50,
    ) -> MetricsKeysResponse:
        """Get available metrics keys."""
        try:
            # Use Redis KEYS command to find time series keys
            pattern = "ts:prom:*"
            keys = self.redis_client.keys(pattern)

            logger.debug(f"Found {len(keys)} keys matching pattern: {pattern}")

            # Get metadata for each key
            result_keys = []
            for key in keys[:limit]:  # Apply limit early for performance
                try:
                    # Extract metric name from key
                    # Key format: ts:prom:{metric_name}:{hash}
                    # We need to extract the full metric name from the key
                    if key.startswith("ts:prom:"):
                        # Remove "ts:prom:" prefix and split by ":"
                        remaining = key[8:]  # Remove "ts:prom:"
                        parts = remaining.split(":")
                        if len(parts) >= 2:
                            # The metric name is everything except the last part (hash)
                            metric_name = ":".join(parts[:-1])

                            # Create basic labels dict with full metric name
                            labels_dict = {"metric": metric_name}
                        else:
                            continue
                    else:
                        continue

                    # Add key to results
                    result_keys.append({"key": key, "labels": labels_dict})

                except Exception as e:
                    logger.warning(f"Failed to process key {key}: {e}")
                    continue

            return MetricsKeysResponse(keys=result_keys)

        except Exception as e:
            logger.error(f"Failed to get metrics keys: {e}")
            raise HTTPException(status_code=500, detail=f"Keys query failed: {str(e)}")


# Global API instance
metrics_api = MetricsAPI()

# FastAPI router
router = APIRouter(prefix="/api/metrics", tags=["metrics"])


@router.get("/query", response_model=MetricsQueryResponse)
def query_metrics(
    metric: str = Query(..., description="Metric name to query"),
    start: Union[str, int] = Query(..., description="Start time (ISO8601 or ms epoch)"),
    end: Optional[Union[str, int]] = Query(
        None, description="End time (ISO8601 or ms epoch)"
    ),
    labels: Optional[str] = Query(
        None, description="Label filters (comma-separated key=value pairs)"
    ),
    le: Optional[str] = Query(None, description="Histogram bucket upper bound"),
    quantile: Optional[str] = Query(None, description="Summary quantile"),
    agg: Optional[str] = Query(
        None, description="Aggregation function (avg|sum|min|max|count)"
    ),
    bucket_ms: Optional[int] = Query(
        None, description="Bucket size in milliseconds (required with agg)"
    ),
    limit: int = Query(50, description="Maximum number of series to return"),
):
    """
    Query metrics from RedisTimeSeries.

    Returns time series data for the specified metric with optional filtering and aggregation.
    """
    if agg and not bucket_ms:
        raise HTTPException(
            status_code=400, detail="bucket_ms is required when agg is specified"
        )

    return metrics_api.query_metrics(
        metric=metric,
        start=start,
        end=end,
        labels=labels,
        le=le,
        quantile=quantile,
        agg=agg,
        bucket_ms=bucket_ms,
        limit=limit,
    )


@router.get("/keys", response_model=MetricsKeysResponse)
def get_metrics_keys(
    metric: Optional[str] = Query(None, description="Metric name filter"),
    labels: Optional[str] = Query(
        None, description="Label filters (comma-separated key=value pairs)"
    ),
    le: Optional[str] = Query(None, description="Histogram bucket upper bound"),
    quantile: Optional[str] = Query(None, description="Summary quantile"),
    limit: int = Query(50, description="Maximum number of keys to return"),
):
    """
    Get available metrics keys.

    Returns metadata about available time series without the actual data.
    """
    return metrics_api.get_metrics_keys(
        metric=metric, labels=labels, le=le, quantile=quantile, limit=limit
    )
