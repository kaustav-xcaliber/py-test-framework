"""SQLAlchemy models for the API Test Framework."""

import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from sqlalchemy import Column, String, Text, Boolean, DateTime, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.database.database import Base


class AuthConfig(Base):
    """Authentication configuration for a service."""

    __tablename__ = "auth_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(String(50), nullable=False)  # "bearer", "api_key", "basic", "oauth2"

    # Bearer
    token = Column(Text, nullable=True)

    # API Key
    key_name = Column(String(100), nullable=True)
    key_value = Column(String(255), nullable=True)

    # Basic
    username = Column(String(100), nullable=True)
    password = Column(String(255), nullable=True)

    # OAuth2
    client_id = Column(String(100), nullable=True)
    client_secret = Column(String(255), nullable=True)
    token_url = Column(Text, nullable=True)

    # Extra config
    extra = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # ---------- Dynamic serialization helpers ----------

    def _fields_for_type(self, t: str) -> List[str]:
        """Return the list of fields to expose for a given auth type."""
        mapping = {
            "bearer": ["token"],
            "api_key": ["key_name", "key_value"],
            "apikey": ["key_name", "key_value"],  # tolerate variations
            "basic": ["username", "password"],
            "oauth2": ["client_id", "client_secret", "token_url", "token", "extra"],
            "oauth": ["client_id", "client_secret", "token_url", "token", "extra"],
        }
        return mapping.get(t.lower(), [])

    @staticmethod
    def _mask(value: Any) -> Any:
        """Mask secrets but preserve hints when string-like."""
        if value is None:
            return None
        if isinstance(value, str):
            if len(value) > 6:
                return value[:2] + ("*" * (len(value) - 4)) + value[-2:]
            return "*" * len(value)
        return "<redacted>"

    def to_dynamic_dict(self, redact_secrets: bool = True) -> Dict[str, Any]:
        """
        Return a dictionary containing only fields relevant to `type`.
        By default, secrets are masked. Pass redact_secrets=False to return raw values.
        """
        result: Dict[str, Any] = {
            "id": str(self.id) if self.id else None,
            "type": self.type,
        }

        if not self.type:
            return result

        fields = self._fields_for_type(self.type)

        for f in fields:
            val = getattr(self, f, None)
            if redact_secrets and f in ("password", "client_secret", "key_value", "token"):
                result[f] = self._mask(val)
            else:
                result[f] = val

        # always include timestamps
        result["created_at"] = self.created_at.isoformat() if self.created_at else None
        result["updated_at"] = self.updated_at.isoformat() if self.updated_at else None

        return result

    def to_dict(self, redact_secrets: bool = True) -> Dict[str, Any]:
        """
        Convenience method that calls to_dynamic_dict().
        Maintains compatibility with other model's to_dict() methods.
        """
        return self.to_dynamic_dict(redact_secrets=redact_secrets)

class Service(Base):
    """Service represents a microservice that can be tested."""
    
    __tablename__ = "services"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    base_url = Column(Text, nullable=False)
    auth_config_id = Column(UUID(as_uuid=True), ForeignKey("auth_configs.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    auth_config = relationship("AuthConfig", backref="services")
    test_cases = relationship("TestCase", back_populates="service", cascade="all, delete-orphan")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "base_url": self.base_url,
            "auth_config": self.auth_config.to_dict() if self.auth_config else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_active": self.is_active
        }


class TestCase(Base):
    """Test case for a service."""
    
    __tablename__ = "test_cases"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_id = Column(UUID(as_uuid=True), ForeignKey("services.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    test_spec = Column(JSON, nullable=False)  # Test specification as JSON
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    service = relationship("Service", back_populates="test_cases")
    test_results = relationship("TestResult", back_populates="test_case", cascade="all, delete-orphan")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "service_id": str(self.service_id),
            "name": self.name,
            "description": self.description,
            "test_spec": self.test_spec,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_active": self.is_active,
            "service": self.service.to_dict() if self.service else None
        }


class TestRun(Base):
    """Test execution run."""
    
    __tablename__ = "test_runs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=True)
    status = Column(String(50), default="running", nullable=False)  # running, completed, failed
    total_tests = Column(Integer, default=0, nullable=False)
    passed_tests = Column(Integer, default=0, nullable=False)
    failed_tests = Column(Integer, default=0, nullable=False)
    execution_time_ms = Column(Integer, default=0, nullable=False)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    test_results = relationship("TestResult", back_populates="test_run", cascade="all, delete-orphan")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "status": self.status,
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "execution_time_ms": self.execution_time_ms,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "test_results": [result.to_dict() for result in self.test_results]
        }


class TestResult(Base):
    """Result of a single test execution."""
    
    __tablename__ = "test_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    test_run_id = Column(UUID(as_uuid=True), ForeignKey("test_runs.id"), nullable=False, index=True)
    test_case_id = Column(UUID(as_uuid=True), ForeignKey("test_cases.id"), nullable=False, index=True)
    test_name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False)  # passed, failed, skipped
    start_time = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    end_time = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    response_data = Column(JSON, nullable=True)  # Response data as JSON
    assertion_results = Column(JSON, nullable=True)  # Assertion results as JSON
    request_size = Column(Integer, default=0, nullable=False)
    response_size = Column(Integer, default=0, nullable=False)
    response_time_ms = Column(Integer, default=0, nullable=False)
    
    # Relationships
    test_run = relationship("TestRun", back_populates="test_results")
    test_case = relationship("TestCase", back_populates="test_results")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "test_run_id": str(self.test_run_id),
            "test_case_id": str(self.test_case_id),
            "test_name": self.test_name,
            "status": self.status,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
            "error_message": self.error_message,
            "response_data": self.response_data,
            "assertion_results": self.assertion_results,
            "request_size": self.request_size,
            "response_size": self.response_size,
            "response_time_ms": self.response_time_ms
        }
