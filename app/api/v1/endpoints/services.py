"""Service management endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone

from app.database.database import get_db
from app.models.models import Service, AuthConfig
from app.schemas.schemas import (
    ServiceCreate,
    ServiceUpdate,
    ServiceResponse,
    PaginationParams,
    PaginatedResponse
)
from app.core.exceptions import NotFoundError, ConflictError

router = APIRouter()


@router.post("/", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
async def create_service(
    service_data: ServiceCreate,
    db: Session = Depends(get_db)
):
    """Create a new service."""
    try:
        # Check if service with same name already exists (only active services)
        existing_service = db.query(Service).filter(
            Service.name == service_data.name,
            Service.is_active == True
        ).first()
        if existing_service:
            raise ConflictError(f"Service with name '{service_data.name}' already exists")
        
        # Create auth config if provided
        auth_config = None
        if service_data.auth_config:
            auth_config = AuthConfig(**service_data.auth_config.dict())
            db.add(auth_config)
            db.flush()  # Get the ID
        
        # Create service
        service = Service(
            name=service_data.name,
            description=service_data.description,
            base_url=str(service_data.base_url),
            auth_config_id=auth_config.id if auth_config else None,
            is_active=service_data.is_active
        )
        
        db.add(service)
        db.commit()
        db.refresh(service)
        
        return ServiceResponse.from_orm(service)
        
    except Exception as e:
        db.rollback()
        raise e


@router.get("/", response_model=PaginatedResponse[ServiceResponse])
async def list_services(
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db)
):
    """List all services with pagination."""
    try:
        # Single query to get both count and paginated results
        base_query = db.query(Service).filter(Service.is_active == True)
        
        # Get total count using a subquery to avoid separate count query
        
        services_with_count = (
            db.query(Service, func.count().over().label('total_count'))
            .filter(Service.is_active == True)
            .offset((pagination.page - 1) * pagination.size)
            .limit(pagination.size)
            .all()
        )
        
        if not services_with_count:
            # If no results, we still need the total count
            total = base_query.count()
            services = []
        else:
            services = [row[0] for row in services_with_count]
            total = services_with_count[0][1]
        
        # Calculate total pages
        pages = (total + pagination.size - 1) // pagination.size
        
        return PaginatedResponse(
            items=[ServiceResponse.model_validate(service) for service in services],
            total=total,
            page=pagination.page,
            size=pagination.size,
            pages=pages
        )
        
    except Exception as e:
        raise e


@router.get("/{service_id}", response_model=ServiceResponse)
async def get_service(
    service_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific service by ID."""
    try:
        service = db.query(Service).filter(
            Service.id == service_id,
            Service.is_active == True
        ).first()
        
        if not service:
            raise NotFoundError("Service", service_id)
        
        return ServiceResponse.from_orm(service)
        
    except Exception as e:
        raise e


@router.put("/{service_id}", response_model=ServiceResponse)
async def update_service(
    service_id: str,
    service_data: ServiceUpdate,
    db: Session = Depends(get_db)
):
    """Update a service."""
    try:
        service = db.query(Service).filter(
            Service.id == service_id,
            Service.is_active == True
        ).first()
        
        if not service:
            raise NotFoundError("Service", service_id)
        
        # Update fields if provided
        if service_data.name is not None:
            # Check if new name conflicts with existing service (only active services)
            if service_data.name != service.name:
                existing = db.query(Service).filter(
                    Service.name == service_data.name,
                    Service.id != service_id,
                    Service.is_active == True
                ).first()
                if existing:
                    raise ConflictError(f"Service with name '{service_data.name}' already exists")
            service.name = service_data.name
        
        if service_data.description is not None:
            service.description = service_data.description
        
        if service_data.base_url is not None:
            service.base_url = str(service_data.base_url)
        
        if service_data.is_active is not None:
            service.is_active = service_data.is_active
        
        # Update auth config if provided
        if service_data.auth_config is not None:
            if service.auth_config:
                # Update existing auth config
                for key, value in service_data.auth_config.dict(exclude_unset=True).items():
                    setattr(service.auth_config, key, value)
            else:
                # Create new auth config
                auth_config = AuthConfig(**service_data.auth_config.dict())
                db.add(auth_config)
                db.flush()
                service.auth_config_id = auth_config.id
        
        db.commit()
        db.refresh(service)
        
        return ServiceResponse.from_orm(service)
        
    except Exception as e:
        db.rollback()
        raise e


@router.delete("/{service_id}", status_code=status.HTTP_200_OK)
async def delete_service(
    service_id: str,
    db: Session = Depends(get_db)
):
    """Delete a service (soft delete)."""
    try:
        service = db.query(Service).filter(
            Service.id == service_id,
            Service.is_active == True
        ).first()
        
        if not service:
            raise NotFoundError("Service", service_id)
        
        # Soft delete
        service.is_active = False
        db.commit()
        
        return {
            "status": "success",
            "service_id": service_id,
            "message": "Service deleted successfully",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        db.rollback()
        raise e


@router.post("/{service_id}/activate", response_model=ServiceResponse)
async def activate_service(
    service_id: str,
    db: Session = Depends(get_db)
):
    """Activate a deactivated service."""
    try:
        service = db.query(Service).filter(Service.id == service_id).first()
        
        if not service:
            raise NotFoundError("Service", service_id)
        
        if service.is_active:
            raise ConflictError("Service is already active")
        
        service.is_active = True
        db.commit()
        db.refresh(service)
        
        return ServiceResponse.from_orm(service)
        
    except Exception as e:
        db.rollback()
        raise e
