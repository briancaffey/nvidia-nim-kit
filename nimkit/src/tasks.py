"""Celery tasks for NVIDIA NIM Kit."""

import time
import logging
from nimkit.src.celery_app import celery_app
from nimkit.src.api.llm.metrics import metrics_processor

# Set up logging
logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def debug_task(self) -> str:
    """
    Simple debug task that sleeps for 1 second then finishes.

    Returns:
        str: A message indicating the task completed successfully
    """
    logger.info(f"Starting debug task with ID: {self.request.id}")

    # Sleep for 1 second
    logger.info("Sleeping for 1 second...")
    time.sleep(1)

    # Return a simple message
    result = f"Debug task completed successfully! Task ID: {self.request.id}"
    logger.info(f"Task completed: {result}")

    return result


@celery_app.task(bind=True, name="process_metrics", queue="nimkit_tasks")
def process_metrics(self) -> dict:
    """
    Process metrics from NIM endpoint and store in RedisTimeSeries.

    This task runs every 5 seconds via Celery Beat to continuously
    ingest Prometheus metrics from the NIM /v1/metrics endpoint.

    Returns:
        dict: Statistics about the processing (parsed, written, errors)
    """
    logger.info(f"Starting metrics processing task with ID: {self.request.id}")

    try:
        result = metrics_processor.process_metrics()
        logger.info(f"Metrics processing completed: {result}")
        return result

    except Exception as e:
        logger.error(f"Metrics processing failed: {e}")
        return {"parsed": 0, "written": 0, "errors": 1}
