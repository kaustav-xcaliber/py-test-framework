"""Health check endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import redis

from app.database.database import get_db
from app.config.settings import settings
from app.schemas.schemas import HealthResponse, DatabaseHealthResponse, RedisHealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Basic health check endpoint."""
    return HealthResponse(
        status="ok",
        message="API Test Framework is running"
    )


@router.get("/health/db", response_model=DatabaseHealthResponse)
async def database_health_check(db: Session = Depends(get_db)):
    """Database health check endpoint."""
    try:
        # Try to execute a simple query
        db.execute("SELECT 1")
        return DatabaseHealthResponse(
            status="ok",
            message="Database is healthy",
            database_status="connected"
        )
    except Exception as e:
        return DatabaseHealthResponse(
            status="error",
            message="Database connection failed",
            database_status="disconnected"
        )


@router.get("/health/redis", response_model=RedisHealthResponse)
async def redis_health_check():
    """Redis health check endpoint."""
    try:
        # Try to connect to Redis
        r = redis.Redis.from_url(settings.redis_url)
        r.ping()
        return RedisHealthResponse(
            status="ok",
            message="Redis is healthy",
            redis_status="connected"
        )
    except Exception as e:
        return RedisHealthResponse(
            status="error",
            message="Redis connection failed",
            redis_status="disconnected"
        )
