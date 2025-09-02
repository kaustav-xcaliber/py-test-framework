"""Schemas package for the API Test Framework."""

from .schemas import (
    # Base schemas
    AuthConfigBase,
    ServiceBase,
    TestCaseBase,
    TestRunBase,
    TestResultBase,
    
    # Create schemas
    AuthConfigCreate,
    ServiceCreate,
    TestCaseCreate,
    TestRunCreate,
    TestResultCreate,
    
    # Update schemas
    AuthConfigUpdate,
    ServiceUpdate,
    TestCaseUpdate,
    TestRunUpdate,
    TestResultUpdate,
    
    # Response schemas
    AuthConfigResponse,
    ServiceResponse,
    TestCaseResponse,
    TestRunResponse,
    TestResultResponse,
    
    # Test specification
    TestSpecBase,
    
    # Curl parsing
    CurlRequest,
    
    # Health check
    HealthResponse,
    DatabaseHealthResponse,
    RedisHealthResponse,
    
    # Error handling
    ErrorResponse,
    
    # Pagination
    PaginationParams,
    PaginatedResponse,
)

__all__ = [
    "AuthConfigBase",
    "ServiceBase", 
    "TestCaseBase",
    "TestRunBase",
    "TestResultBase",
    "AuthConfigCreate",
    "ServiceCreate",
    "TestCaseCreate",
    "TestRunCreate",
    "TestResultCreate",
    "AuthConfigUpdate",
    "ServiceUpdate",
    "TestCaseUpdate",
    "TestRunUpdate",
    "TestResultUpdate",
    "AuthConfigResponse",
    "ServiceResponse",
    "TestCaseResponse",
    "TestRunResponse",
    "TestResultResponse",
    "TestSpecBase",
    "CurlRequest",
    "HealthResponse",
    "DatabaseHealthResponse",
    "RedisHealthResponse",
    "ErrorResponse",
    "PaginationParams",
    "PaginatedResponse",
]
