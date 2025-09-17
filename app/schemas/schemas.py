"""Pydantic schemas for API request/response validation."""

from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Generic, TypeVar
from pydantic import BaseModel, Field, HttpUrl, validator
import uuid

# Type variable for generic pagination
T = TypeVar('T')


# Base schemas
class AuthConfigBase(BaseModel):
    """Base authentication configuration schema."""

    type: str = Field(..., description="Authentication type: bearer, api_key, basic, oauth2")

    # Bearer
    token: Optional[str] = Field(None, description="Authentication token")

    # API Key
    key_name: Optional[str] = Field(None, description="API key name")
    key_value: Optional[str] = Field(None, description="API key value")

    # Basic
    username: Optional[str] = Field(None, description="Username for basic auth")
    password: Optional[str] = Field(None, description="Password for basic auth")

    # OAuth2
    client_id: Optional[str] = Field(None, description="OAuth2 client ID")
    client_secret: Optional[str] = Field(None, description="OAuth2 client secret")
    token_url: Optional[str] = Field(None, description="OAuth2 token URL")

    # Extra config
    extra: Optional[Dict[str, Any]] = Field(None, description="Additional configuration")

    # --------- Dynamic dict helpers ---------

    def _fields_for_type(self) -> List[str]:
        """Return the list of fields to expose for the current type."""
        mapping = {
            "bearer": ["token"],
            "api_key": ["key_name", "key_value"],
            "basic": ["username", "password"],
            "oauth2": ["client_id", "client_secret", "token_url", "token", "extra"],
        }
        return mapping.get(self.type.lower(), [])

    @staticmethod
    def _mask(value: Any) -> Any:
        """Mask secrets but preserve type/length hints when string-like."""
        if value is None:
            return None
        if isinstance(value, str):
            if len(value) > 6:
                return value[:2] + ("*" * (len(value) - 4)) + value[-2:]
            return "*" * len(value)
        return "<redacted>"

    def to_dynamic_dict(self, redact_secrets: bool = True) -> Dict[str, Any]:
        """
        Return a dictionary with only the fields relevant to `type`.
        Secrets are masked by default.
        """
        result: Dict[str, Any] = {"type": self.type}

        for f in self._fields_for_type():
            val = getattr(self, f, None)
            if redact_secrets and f in ("password", "client_secret", "key_value", "token"):
                result[f] = self._mask(val)
            else:
                result[f] = val

        return result


class AuthConfigCreate(AuthConfigBase):
    """Schema for creating authentication configuration."""
    pass


class AuthConfigUpdate(AuthConfigBase):
    """Schema for updating authentication configuration."""
    pass


class AuthConfigResponse(BaseModel):
    """Schema for authentication configuration response."""
    
    # Base fields always included
    id: uuid.UUID
    type: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        extra = "allow"  # Allow additional fields to be set dynamically

    @classmethod
    def from_auth_config(cls, auth_config):
        """Create response from AuthConfig model with dynamic field filtering."""
        if not auth_config:
            return None
            
        # Get the dynamic dict with masked secrets
        dynamic_data = auth_config.to_dynamic_dict(redact_secrets=True)
        
        # Add required fields
        base_data = {
            'id': auth_config.id,
            'type': auth_config.type,
            'created_at': auth_config.created_at,
            'updated_at': auth_config.updated_at
        }
        
        # Add only relevant fields for this auth type
        type_fields = cls._get_fields_for_type(auth_config.type)
        for field in type_fields:
            if field in dynamic_data and dynamic_data[field] is not None:
                base_data[field] = dynamic_data[field]
        
        return cls(**base_data)
    
    @staticmethod
    def _get_fields_for_type(auth_type: str) -> List[str]:
        """Return the list of fields to expose for a given auth type."""
        mapping = {
            "bearer": ["token"],
            "api_key": ["key_name", "key_value"],
            "apikey": ["key_name", "key_value"],  # tolerate variations
            "basic": ["username", "password"],
            "oauth2": ["client_id", "client_secret", "token_url", "token", "extra"],
            "oauth": ["client_id", "client_secret", "token_url", "token", "extra"],
        }
        return mapping.get(auth_type.lower(), [])


class ServiceBase(BaseModel):
    """Base service schema."""
    name: str = Field(..., min_length=1, max_length=255, description="Service name")
    description: Optional[str] = Field(None, description="Service description")
    base_url: HttpUrl = Field(..., description="Service base URL")
    is_active: bool = Field(True, description="Whether the service is active")


class ServiceCreate(ServiceBase):
    """Schema for creating a service."""
    auth_config: Optional[AuthConfigCreate] = Field(None, description="Authentication configuration")


class ServiceUpdate(ServiceBase):
    """Schema for updating a service."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    base_url: Optional[HttpUrl] = Field(None)
    auth_config: Optional[AuthConfigCreate] = Field(None)


class ServiceResponse(ServiceBase):
    """Schema for service response."""
    id: uuid.UUID
    auth_config: Optional[AuthConfigResponse] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
    
    @classmethod
    def from_service(cls, service):
        """Create ServiceResponse with properly formatted auth_config."""
        auth_config_response = None
        if service.auth_config:
            auth_config_response = AuthConfigResponse.from_auth_config(service.auth_config)
        
        return cls(
            id=service.id,
            name=service.name,
            description=service.description,
            base_url=service.base_url,
            is_active=service.is_active,
            auth_config=auth_config_response,
            created_at=service.created_at,
            updated_at=service.updated_at
        )


class TestSpecBase(BaseModel):
    """Base test specification schema."""
    name: str = Field(..., description="Test name")
    method: str = Field(..., description="HTTP method")
    path: str = Field(..., description="Request path")
    headers: Optional[Dict[str, str]] = Field(None, description="Request headers")
    query_params: Optional[Dict[str, str]] = Field(None, description="Query parameters")
    path_variables: Optional[Dict[str, str]] = Field(None, description="Path variables")
    body: Optional[Any] = Field(None, description="Request body")
    assertions: List[Dict[str, Any]] = Field(..., description="Test assertions")


class TestCaseBase(BaseModel):
    """Base test case schema."""
    name: str = Field(..., min_length=1, max_length=255, description="Test case name")
    description: Optional[str] = Field(None, description="Test case description")
    test_spec: TestSpecBase = Field(..., description="Test specification")
    is_active: bool = Field(True, description="Whether the test case is active")


class TestCaseCreate(TestCaseBase):
    """Schema for creating a test case."""
    service_id: uuid.UUID = Field(..., description="Service ID")


class TestCaseUpdate(TestCaseBase):
    """Schema for updating a test case."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    test_spec: Optional[TestSpecBase] = Field(None)
    service_id: Optional[uuid.UUID] = Field(None)


class TestCaseResponse(TestCaseBase):
    """Schema for test case response."""
    id: uuid.UUID
    service_id: uuid.UUID
    service: Optional[ServiceResponse] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TestRunBase(BaseModel):
    """Base test run schema."""
    name: Optional[str] = Field(None, description="Test run name")


class TestRunCreate(TestRunBase):
    """Schema for creating a test run."""
    test_case_ids: Optional[List[uuid.UUID]] = Field(None, description="List of test case IDs to execute")


class TestRunUpdate(TestRunBase):
    """Schema for updating a test run."""
    status: Optional[str] = Field(None, description="Test run status")
    completed_at: Optional[datetime] = Field(None, description="Completion time")


class TestRunResponse(TestRunBase):
    """Schema for test run response."""
    id: uuid.UUID
    status: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    execution_time_ms: int
    started_at: datetime
    completed_at: Optional[datetime]
    test_results: List["TestResultResponse"] = []

    class Config:
        from_attributes = True


class TestResultBase(BaseModel):
    """Base test result schema."""
    test_name: str = Field(..., description="Test name")
    status: str = Field(..., description="Test status")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    response_data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    assertion_results: Optional[List[Dict[str, Any]]] = Field(None, description="Assertion results")


class TestResultCreate(TestResultBase):
    """Schema for creating a test result."""
    test_run_id: uuid.UUID = Field(..., description="Test run ID")
    test_case_id: uuid.UUID = Field(..., description="Test case ID")


class TestResultUpdate(TestResultBase):
    """Schema for updating a test result."""
    end_time: Optional[datetime] = Field(None, description="Test end time")
    duration_ms: Optional[int] = Field(None, description="Test duration in milliseconds")
    request_size: Optional[int] = Field(None, description="Request size in bytes")
    response_size: Optional[int] = Field(None, description="Response size in bytes")
    response_time_ms: Optional[int] = Field(None, description="Response time in milliseconds")


class TestResultResponse(TestResultBase):
    """Schema for test result response."""
    id: uuid.UUID
    test_run_id: uuid.UUID
    test_case_id: uuid.UUID
    start_time: datetime
    end_time: Optional[datetime]
    duration_ms: int
    request_size: int
    response_size: int
    response_time_ms: int

    class Config:
        from_attributes = True


# Update forward references
TestRunResponse.model_rebuild()
TestResultResponse.model_rebuild()


# Curl parsing schemas
class TestCaseFromCurlCreate(BaseModel):
    """Schema for creating a test case from curl command."""
    service_id: uuid.UUID = Field(..., description="Service ID")
    name: str = Field(..., min_length=1, max_length=255, description="Test case name")
    description: Optional[str] = Field(None, description="Test case description")
    curl_command: str = Field(..., description="Curl command to convert to test specification")
    assertions: Optional[List[Dict[str, Any]]] = Field(default=[], description="List of assertions for the test case")
class CurlRequest(BaseModel):
    """Schema for parsed curl command."""
    method: str = Field(..., description="HTTP method")
    url: str = Field(..., description="Request URL")
    headers: Dict[str, str] = Field(default_factory=dict, description="Request headers")
    body: Optional[str] = Field(None, description="Request body")
    query_params: Dict[str, str] = Field(default_factory=dict, description="Query parameters")
    path_variables: Dict[str, str] = Field(default_factory=dict, description="Path variables")
    request_type: str = Field(default="json", description="Request content type")
    raw_command: str = Field(..., description="Original curl command")


# Health check schemas
class HealthResponse(BaseModel):
    """Schema for health check response."""
    status: str = Field(..., description="Health status")
    message: str = Field(..., description="Health message")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Check timestamp")


class DatabaseHealthResponse(HealthResponse):
    """Schema for database health check response."""
    database_status: str = Field(..., description="Database connection status")


class RedisHealthResponse(HealthResponse):
    """Schema for Redis health check response."""
    redis_status: str = Field(..., description="Redis connection status")


# Error schemas
class ErrorResponse(BaseModel):
    """Schema for error responses."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Error timestamp")


# Pagination schemas
class PaginationParams(BaseModel):
    """Schema for pagination parameters."""
    page: int = Field(1, ge=1, description="Page number")
    size: int = Field(10, ge=1, le=100, description="Page size")


class PaginatedResponse(BaseModel, Generic[T]):
    """Schema for paginated responses."""
    items: List[T] = Field(..., description="Page items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size")
    pages: int = Field(..., description="Total number of pages")
