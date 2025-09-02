"""Main API router for version 1 of the API."""

from fastapi import APIRouter

from app.api.v1.endpoints import health, services, tests, test_runs, auth_configs

# Create main API router
api_router = APIRouter()

# Include endpoint routers
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(services.router, prefix="/services", tags=["Services"])
api_router.include_router(tests.router, prefix="/tests", tags=["Tests"])
api_router.include_router(test_runs.router, prefix="/test-runs", tags=["Test Runs"])
api_router.include_router(auth_configs.router, prefix="/auth-configs", tags=["Authentication Configs"])
