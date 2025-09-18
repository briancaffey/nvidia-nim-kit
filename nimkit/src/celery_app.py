"""Celery application configuration for NVIDIA NIM Kit."""

import os
from celery import Celery

# Create Celery app
celery_app = Celery(
    "nimkit",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
    include=["nimkit.src.tasks"],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    # Enable remote inspection for Flower
    worker_send_task_events=True,
    task_send_sent_event=True,
)

# Optional configuration for development
if os.getenv("CELERY_ALWAYS_EAGER", "false").lower() == "true":
    celery_app.conf.task_always_eager = True
