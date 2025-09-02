"""Custom exception classes for the API Test Framework."""

from datetime import datetime
from typing import Optional, Dict, Any


class APIException(Exception):
    """Base exception class for API errors."""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_type: str = "API_ERROR",
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_type = error_type
        self.code = code
        self.details = details or {}
        self.timestamp = datetime.utcnow()
        
        super().__init__(self.message)


class ValidationError(APIException):
    """Exception for validation errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=400,
            error_type="VALIDATION_ERROR",
            code="VALIDATION_FAILED",
            details=details
        )


class NotFoundError(APIException):
    """Exception for resource not found errors."""
    
    def __init__(self, resource: str, resource_id: str):
        super().__init__(
            message=f"{resource} with id {resource_id} not found",
            status_code=404,
            error_type="NOT_FOUND",
            code="RESOURCE_NOT_FOUND",
            details={"resource": resource, "resource_id": resource_id}
        )


class ConflictError(APIException):
    """Exception for resource conflict errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=409,
            error_type="CONFLICT",
            code="RESOURCE_CONFLICT",
            details=details
        )


class DatabaseError(APIException):
    """Exception for database operation errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=500,
            error_type="DATABASE_ERROR",
            code="DATABASE_OPERATION_FAILED",
            details=details
        )


class TestExecutionError(APIException):
    """Exception for test execution errors."""
    
    def __init__(self, message: str, test_name: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=500,
            error_type="TEST_EXECUTION_ERROR",
            code="TEST_EXECUTION_FAILED",
            details={"test_name": test_name, **details} if details else {"test_name": test_name}
        )


class ServiceUnavailableError(APIException):
    """Exception for service unavailable errors."""
    
    def __init__(self, service: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Service {service} is currently unavailable",
            status_code=503,
            error_type="SERVICE_UNAVAILABLE",
            code="SERVICE_DOWN",
            details={"service": service, **details} if details else {"service": service}
        )


class AuthenticationError(APIException):
    """Exception for authentication errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=401,
            error_type="AUTHENTICATION_ERROR",
            code="AUTH_FAILED",
            details=details
        )


class AuthorizationError(APIException):
    """Exception for authorization errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=403,
            error_type="AUTHORIZATION_ERROR",
            code="ACCESS_DENIED",
            details=details
        )


class RateLimitError(APIException):
    """Exception for rate limiting errors."""
    
    def __init__(self, message: str, retry_after: Optional[int] = None):
        details = {"retry_after": retry_after} if retry_after else {}
        super().__init__(
            message=message,
            status_code=429,
            error_type="RATE_LIMIT_ERROR",
            code="RATE_LIMIT_EXCEEDED",
            details=details
        )
