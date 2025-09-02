"""Core package for the API Test Framework."""

from .exceptions import (
    APIException,
    ValidationError,
    NotFoundError,
    ConflictError,
    DatabaseError,
    TestExecutionError,
    ServiceUnavailableError,
    AuthenticationError,
    AuthorizationError,
    RateLimitError,
)

__all__ = [
    "APIException",
    "ValidationError",
    "NotFoundError",
    "ConflictError",
    "DatabaseError",
    "TestExecutionError",
    "ServiceUnavailableError",
    "AuthenticationError",
    "AuthorizationError",
    "RateLimitError",
]
