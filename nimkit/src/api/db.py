"""Database connection management for Redis."""

import os
import redis
from typing import Optional

# Global Redis connection instance
_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> redis.Redis:
    """Get or create Redis client instance."""
    global _redis_client

    if _redis_client is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        _redis_client = redis.from_url(redis_url, decode_responses=True)

    return _redis_client


def get_redis_connection() -> redis.Redis:
    """Alias for get_redis_client for backward compatibility."""
    return get_redis_client()
