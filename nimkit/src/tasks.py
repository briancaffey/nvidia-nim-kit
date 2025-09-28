"""Celery tasks for NVIDIA NIM Kit."""

import time
import logging
from nimkit.src.celery_app import celery_app

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
