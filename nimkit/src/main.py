"""Main FastAPI application for NVIDIA NIM Kit."""

import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from nimkit.src.tasks import debug_task
from nimkit.src.api.llm.health import router as health_router
from nimkit.src.api.llm.inference import router as inference_router
from nimkit.src.api.llm.metrics_api import router as metrics_router
from nimkit.src.api.config.routes import router as nims_router

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("nimkit.log")],
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="NVIDIA NIM Kit API",
    description="A toolkit for NVIDIA NIM integration",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include health routes
app.include_router(health_router)

# Include LLM inference routes
app.include_router(inference_router)

# Include metrics routes
app.include_router(metrics_router)

# Include NIM configuration routes
app.include_router(nims_router)


@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint."""
    return {"message": "Welcome to NVIDIA NIM Kit API"}


@app.get("/api/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.1.0",
        "service": "nvidia-nim-kit",
    }


@app.post("/api/tasks/debug")
async def trigger_debug_task() -> Dict[str, str]:
    """Trigger the debug Celery task."""
    logger.info("Triggering debug task...")
    task = debug_task.apply_async(queue="nimkit_tasks")
    logger.info(f"Debug task queued with ID: {task.id}")
    return {"task_id": task.id, "status": "Task queued successfully"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
