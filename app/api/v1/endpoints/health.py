"""Health check endpoints."""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from redis import Redis, RedisError

from app.database.database import get_db
from app.config.settings import settings
from app.schemas.schemas import (
    HealthResponse,
    DatabaseHealthResponse,
    RedisHealthResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Basic health check endpoint."""
    return HealthResponse(status="ok", message="API Test Framework is running")


@router.get("/health/db", response_model=DatabaseHealthResponse)
async def database_health_check(db: Session = Depends(get_db)):
    """Database health check endpoint."""
    try:
        # Execute a simple query to ensure DB is reachable
        result = db.execute(text("SELECT 1"))
        # ensure query actually executed
        _ = result.scalar() if hasattr(result, "scalar") else result.fetchone()
        return DatabaseHealthResponse(
            status="ok",
            message="Database is healthy",
            database_status="connected",
        )
    except Exception:
        # Log the full exception for debug, but don't leak internals to clients
        logger.exception("Database health check failed")
        return DatabaseHealthResponse(
            status="error",
            message="Database connection failed",
            database_status="disconnected",
        )


@router.get("/health/redis", response_model=RedisHealthResponse)
async def redis_health_check():
    """Redis health check endpoint."""
    try:
        r = Redis.from_url(settings.redis_url)
        r.ping()
        return RedisHealthResponse(
            status="ok", message="Redis is healthy", redis_status="connected"
        )
    except RedisError:
        logger.exception("Redis health check failed")
        return RedisHealthResponse(
            status="error", message="Redis connection failed", redis_status="disconnected"
        )
    except Exception:
        # Catch any other unexpected exception types
        logger.exception("Unexpected error during Redis health check")
        return RedisHealthResponse(
            status="error", message="Redis connection failed", redis_status="disconnected"
        )
