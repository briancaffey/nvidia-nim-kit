"""Metrics processing and RedisTimeSeries storage."""

import hashlib
import json
import logging
import os
import time
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

import redis
import requests
from prometheus_client.parser import text_string_to_metric_families

from nimkit.src.api.config.nims import nim_manager

logger = logging.getLogger(__name__)

# Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
TS_RETENTION_MS = int(os.getenv("TS_RETENTION_MS", "604800000"))  # 7 days
REQUEST_TIMEOUT_SEC = int(os.getenv("REQUEST_TIMEOUT_SEC", "3"))


class MetricsProcessor:
    """Handles fetching, parsing, and storing Prometheus metrics to RedisTimeSeries."""

    def __init__(self):
        """Initialize Redis connection and cache for created time series."""
        self.redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        self.created_keys = set()  # Cache for created time series keys

    def _get_nim_host_port(self) -> Tuple[str, int]:
        """Get NIM host and port from the first available LLM NIM."""
        nim_ids = nim_manager.list_nim_ids()
        for nim_id in nim_ids:
            nim_data = nim_manager.get_nim_data(nim_id)
            if nim_data and nim_data.nim_type == "llm":
                return nim_data.host, nim_data.port

        # Fallback to localhost if no NIM found
        logger.warning("No LLM NIM found, using localhost:8000")
        return "localhost", 8000

    def _build_key_and_labels(self, metric_name: str, labels: Dict[str, str]) -> Tuple[str, Dict[str, str]]:
        """Build RedisTimeSeries key and labels from metric name and Prometheus labels."""
        # Create a stable hash of labels for the key
        sorted_labels = sorted(labels.items())
        label_hash = hashlib.sha1(json.dumps(sorted_labels, sort_keys=True).encode()).hexdigest()[:8]

        # Build the key
        key = f"ts:prom:{metric_name}:{label_hash}"

        # Build TS labels (include all original labels plus metric name)
        ts_labels = {"metric": metric_name}
        ts_labels.update(labels)

        return key, ts_labels

    def _ensure_ts_created(self, key: str, labels: Dict[str, str]) -> bool:
        """Ensure time series exists in Redis, create if needed."""
        if key in self.created_keys:
            return True

        try:
            # Check if TS already exists
            try:
                self.redis_client.execute_command("TS.INFO", key)
                self.created_keys.add(key)
                return True
            except redis.ResponseError:
                # TS doesn't exist, create it
                pass

            # Create new time series
            cmd_args = [
                "TS.CREATE", key,
                "RETENTION", TS_RETENTION_MS,
                "DUPLICATE_POLICY", "LAST"
            ]

            # Add labels
            for label_key, label_value in labels.items():
                cmd_args.extend(["LABELS", label_key, label_value])

            self.redis_client.execute_command(*cmd_args)
            self.created_keys.add(key)
            logger.debug(f"Created time series: {key}")
            return True

        except Exception as e:
            logger.error(f"Failed to create time series {key}: {e}")
            return False

    def _classify_metric_type(self, metric_name: str, labels: Dict[str, str]) -> str:
        """Classify metric type based on name and labels."""
        if metric_name.endswith("_bucket"):
            return "histogram_bucket"
        elif metric_name.endswith("_sum"):
            return "histogram_sum"
        elif metric_name.endswith("_count"):
            return "histogram_count"
        elif "quantile" in labels:
            return "summary_quantile"
        else:
            return "counter_or_gauge"

    def fetch_metrics(self) -> Optional[str]:
        """Fetch metrics from NIM endpoint."""
        try:
            host, port = self._get_nim_host_port()
            url = f"http://{host}:{port}/v1/metrics"

            logger.debug(f"Fetching metrics from {url}")
            response = requests.get(url, timeout=REQUEST_TIMEOUT_SEC)
            response.raise_for_status()

            return response.text

        except Exception as e:
            logger.error(f"Failed to fetch metrics: {e}")
            return None

    def process_metrics(self) -> Dict[str, int]:
        """Process metrics and store them in RedisTimeSeries."""
        metrics_text = self.fetch_metrics()
        if not metrics_text:
            return {"parsed": 0, "written": 0, "errors": 1}

        try:
            # Parse Prometheus metrics
            families = list(text_string_to_metric_families(metrics_text))

            now_ms = int(time.time() * 1000)
            written_count = 0
            error_count = 0

            # Use pipeline for batch operations
            pipe = self.redis_client.pipeline()

            for family in families:
                for sample in family.samples:
                    metric_name = sample.name
                    labels = sample.labels
                    value = sample.value

                    # Use sample timestamp if available, otherwise use current time
                    ts_ms = int(sample.timestamp * 1000) if sample.timestamp else now_ms

                    # Build key and labels
                    key, ts_labels = self._build_key_and_labels(metric_name, labels)

                    # Ensure time series exists
                    if not self._ensure_ts_created(key, ts_labels):
                        error_count += 1
                        continue

                    # Add to pipeline
                    try:
                        pipe.execute_command("TS.ADD", key, ts_ms, value)
                        written_count += 1
                    except Exception as e:
                        logger.error(f"Failed to add sample to pipeline: {e}")
                        error_count += 1

            # Execute pipeline
            try:
                pipe.execute()
                logger.info(f"Processed metrics: {written_count} samples written, {error_count} errors")
            except Exception as e:
                logger.error(f"Pipeline execution failed: {e}")
                error_count += written_count
                written_count = 0

            return {
                "parsed": len(families),
                "written": written_count,
                "errors": error_count
            }

        except Exception as e:
            logger.error(f"Failed to process metrics: {e}")
            return {"parsed": 0, "written": 0, "errors": 1}


# Global processor instance
metrics_processor = MetricsProcessor()
