"""Configuration settings for the API Test Framework."""

import os
from typing import List, Union, Any
from pydantic import Field, field_validator, field_serializer, computed_field
from pydantic_settings import BaseSettings


def parse_comma_separated(value: Any) -> List[str]:
    """Parse comma-separated string into list."""
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    elif isinstance(value, list):
        return value
    return []


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database Configuration
    database_url: str = Field(
        default="postgresql://user:password@localhost:5432/api_test_framework",
        env="DATABASE_URL"
    )
    database_host: str = Field(default="localhost", env="DATABASE_HOST")
    database_port: int = Field(default=5432, env="DATABASE_PORT")
    database_name: str = Field(default="", env="DATABASE_NAME")
    database_user: str = Field(default="username", env="DATABASE_USER")
    database_password: str = Field(default="password", env="DATABASE_PASSWORD")
    
    # Redis Configuration
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_db: int = Field(default=0, env="REDIS_DB")
    redis_password: str = Field(default="", env="REDIS_PASSWORD")
    
    # Application Configuration
    app_name: str = Field(default="API Test Framework", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=True, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    secret_key: str = Field(default="your-secret-key-here", env="SECRET_KEY")
    allowed_hosts: List[str] = Field(
        default=["localhost", "127.0.0.1"],
        description="Comma-separated list of allowed hosts",
        exclude=True  # Don't load from environment variables
    )
    
    # Server Configuration
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    workers: int = Field(default=4, env="WORKERS")
    
    # Test Execution Configuration
    max_concurrent_tests: int = Field(default=10, env="MAX_CONCURRENT_TESTS")
    test_timeout_seconds: int = Field(default=300, env="TEST_TIMEOUT_SECONDS")
    default_request_timeout: int = Field(default=30, env="DEFAULT_REQUEST_TIMEOUT")
    
    # File Upload Configuration
    max_file_size: int = Field(default=10485760, env="MAX_FILE_SIZE")  # 10MB
    upload_dir: str = Field(default="./uploads", env="UPLOAD_DIR")
    
    # CORS Configuration
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="Comma-separated list of CORS origins",
        exclude=True  # Don't load from environment variables
    )
    cors_allow_credentials: bool = Field(default=True, env="CORS_ALLOW_CREDENTIALS")
    
    class Config:
        env_file = ".env" if not os.getenv("TESTING") else None
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance - lazy creation to avoid import-time issues
_settings_instance = None

def get_settings() -> Settings:
    """Get or create the global settings instance."""
    global _settings_instance
    if _settings_instance is None:
        if os.getenv("TESTING"):
            _settings_instance = Settings(
                database_url="sqlite:///./test.db",
                debug=True,
                allowed_hosts=["localhost", "127.0.0.1"],
                cors_origins=["http://localhost:3000", "http://localhost:8080"]
            )
        else:
            _settings_instance = Settings()
    return _settings_instance

# For backward compatibility
settings = get_settings()
