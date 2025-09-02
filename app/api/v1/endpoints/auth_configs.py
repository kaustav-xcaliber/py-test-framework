"""Authentication configuration management endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.database.database import get_db
from app.models.models import AuthConfig
from app.schemas.schemas import (
    AuthConfigCreate,
    AuthConfigUpdate,
    AuthConfigResponse,
    PaginationParams,
    PaginatedResponse
)
from app.core.exceptions import NotFoundError, ConflictError

router = APIRouter()


@router.post("/", response_model=AuthConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_auth_config(
    auth_config_data: AuthConfigCreate,
    db: Session = Depends(get_db)
):
    """Create a new authentication configuration."""
    try:
        # Validate auth type
        valid_types = ["bearer", "api_key", "basic", "oauth2"]
        if auth_config_data.type.lower() not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid auth type. Must be one of: {', '.join(valid_types)}"
            )
        
        # Validate required fields based on auth type
        auth_type = auth_config_data.type.lower()
        if auth_type == "bearer" and not auth_config_data.token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bearer auth requires a token"
            )
        elif auth_type == "api_key" and (not auth_config_data.key_name or not auth_config_data.key_value):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="API key auth requires both key_name and key_value"
            )
        elif auth_type == "basic" and (not auth_config_data.username or not auth_config_data.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Basic auth requires both username and password"
            )
        elif auth_type == "oauth2" and (not auth_config_data.client_id or not auth_config_data.client_secret or not auth_config_data.token_url):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OAuth2 auth requires client_id, client_secret, and token_url"
            )
        
        # Create auth config
        auth_config = AuthConfig(**auth_config_data.dict())
        
        db.add(auth_config)
        db.commit()
        db.refresh(auth_config)
        
        return AuthConfigResponse.from_orm(auth_config)
        
    except Exception as e:
        db.rollback()
        raise e


@router.get("/", response_model=PaginatedResponse[AuthConfigResponse])
async def list_auth_configs(
    auth_type: str = None,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db)
):
    """List all authentication configurations with optional filtering and pagination."""
    try:
        query = db.query(AuthConfig)
        
        # Filter by auth type if specified
        if auth_type:
            query = query.filter(AuthConfig.type == auth_type.lower())
        
        # Get total count
        total = query.count()
        
        # Get paginated results
        auth_configs = (
            query
            .order_by(AuthConfig.created_at.desc())
            .offset((pagination.page - 1) * pagination.size)
            .limit(pagination.size)
            .all()
        )
        
        # Calculate total pages
        pages = (total + pagination.size - 1) // pagination.size
        
        return PaginatedResponse(
            items=[AuthConfigResponse.from_orm(auth_config) for auth_config in auth_configs],
            total=total,
            page=pagination.page,
            size=pagination.size,
            pages=pages
        )
        
    except Exception as e:
        raise e


@router.get("/{auth_config_id}", response_model=AuthConfigResponse)
async def get_auth_config(
    auth_config_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific authentication configuration by ID."""
    try:
        auth_config = db.query(AuthConfig).filter(AuthConfig.id == auth_config_id).first()
        
        if not auth_config:
            raise NotFoundError("AuthConfig", auth_config_id)
        
        return AuthConfigResponse.from_orm(auth_config)
        
    except Exception as e:
        raise e


@router.put("/{auth_config_id}", response_model=AuthConfigResponse)
async def update_auth_config(
    auth_config_id: str,
    auth_config_data: AuthConfigUpdate,
    db: Session = Depends(get_db)
):
    """Update an authentication configuration."""
    try:
        auth_config = db.query(AuthConfig).filter(AuthConfig.id == auth_config_id).first()
        
        if not auth_config:
            raise NotFoundError("AuthConfig", auth_config_id)
        
        # Validate auth type if provided
        if auth_config_data.type is not None:
            valid_types = ["bearer", "api_key", "basic", "oauth2"]
            if auth_config_data.type.lower() not in valid_types:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid auth type. Must be one of: {', '.join(valid_types)}"
                )
        
        # Update fields if provided
        update_data = auth_config_data.dict(exclude_unset=True)
        
        # Validate required fields based on auth type
        auth_type = update_data.get("type", auth_config.type).lower()
        if auth_type == "bearer" and not update_data.get("token", auth_config.token):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bearer auth requires a token"
            )
        elif auth_type == "api_key" and (not update_data.get("key_name", auth_config.key_name) or not update_data.get("key_value", auth_config.key_value)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="API key auth requires both key_name and key_value"
            )
        elif auth_type == "basic" and (not update_data.get("username", auth_config.username) or not update_data.get("password", auth_config.password)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Basic auth requires both username and password"
            )
        elif auth_type == "oauth2" and (not update_data.get("client_id", auth_config.client_id) or not update_data.get("client_secret", auth_config.client_secret) or not update_data.get("token_url", auth_config.token_url)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OAuth2 auth requires client_id, client_secret, and token_url"
            )
        
        for key, value in update_data.items():
            setattr(auth_config, key, value)
        
        auth_config.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(auth_config)
        
        return AuthConfigResponse.from_orm(auth_config)
        
    except Exception as e:
        db.rollback()
        raise e


@router.delete("/{auth_config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_auth_config(
    auth_config_id: str,
    db: Session = Depends(get_db)
):
    """Delete an authentication configuration."""
    try:
        auth_config = db.query(AuthConfig).filter(AuthConfig.id == auth_config_id).first()
        
        if not auth_config:
            raise NotFoundError("AuthConfig", auth_config_id)
        
        # Check if auth config is being used by any services
        if auth_config.services:
            service_names = [service.name for service in auth_config.services]
            raise ConflictError(f"Cannot delete auth config. It is being used by services: {', '.join(service_names)}")
        
        db.delete(auth_config)
        db.commit()
        
    except Exception as e:
        db.rollback()
        raise e


@router.get("/types/supported", response_model=List[str])
async def get_supported_auth_types():
    """Get list of supported authentication types."""
    return ["bearer", "api_key", "basic", "oauth2"]
