"""Main API router for version 1 of the API."""

from fastapi import APIRouter

from app.api.v1.endpoints import health, services, tests, test_runs, auth_configs
import importlib
import logging

# Create main API router
api_router = APIRouter()

# Include endpoint routers
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(services.router, prefix="/services", tags=["Services"])
api_router.include_router(tests.router, prefix="/tests", tags=["Tests"])
api_router.include_router(test_runs.router, prefix="/test-runs", tags=["Test Runs"])
api_router.include_router(auth_configs.router, prefix="/auth-configs", tags=["Authentication Configs"])
# Optionally include utility endpoints (curl parser, assertion generator) if present

logger = logging.getLogger(__name__)

def _include_optional(module_path: str, prefix: str, tags: list[str]) -> None:
    try:
        mod = importlib.import_module(module_path)
    except ModuleNotFoundError:
        logger.debug("Optional module %s not found; skipping", module_path)
        return
    except Exception:
        logger.exception("Failed to import optional module %s; skipping", module_path)
        return

    router = getattr(mod, "router", None)
    if router is None:
        logger.debug("Optional module %s does not expose 'router'; skipping", module_path)
        return

    api_router.include_router(router, prefix=prefix, tags=tags)

_include_optional("app.api.v1.endpoints.curl_parser", "/utils/curl", ["Utils", "Curl Parser"])
_include_optional("app.api.v1.endpoints.assertion_generator", "/utils/assertions", ["Utils", "Assertion Generator"])