"""Test case management endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.models import TestCase, Service
from app.schemas.schemas import (
    TestCaseCreate,
    TestCaseUpdate,
    TestCaseResponse,
    PaginationParams,
    PaginatedResponse,
    TestSpecBase,
    TestCaseFromCurlCreate
)
from app.core.exceptions import NotFoundError, ConflictError
from app.utils.curl_parser import curl_to_test_spec

router = APIRouter()


@router.post("/", response_model=TestCaseResponse, status_code=status.HTTP_201_CREATED)
async def create_test_case(
    test_case_data: TestCaseCreate,
    db: Session = Depends(get_db)
):
    """Create a new test case."""
    try:
        # Verify service exists
        service = db.query(Service).filter(
            Service.id == test_case_data.service_id,
            Service.is_active == True
        ).first()
        
        if not service:
            raise NotFoundError("Service", str(test_case_data.service_id))
        
        # Check if test case with same name already exists for this service
        existing_test = db.query(TestCase).filter(
            TestCase.name == test_case_data.name,
            TestCase.service_id == test_case_data.service_id,
            TestCase.is_active == True
        ).first()
        
        if existing_test:
            raise ConflictError(f"Test case with name '{test_case_data.name}' already exists for this service")
        
        # Create test case
        test_case = TestCase(
            service_id=test_case_data.service_id,
            name=test_case_data.name,
            description=test_case_data.description,
            test_spec=test_case_data.test_spec.dict(),
            is_active=test_case_data.is_active
        )
        
        db.add(test_case)
        db.commit()
        db.refresh(test_case)
        
        return TestCaseResponse.from_orm(test_case)
        
    except Exception as e:
        db.rollback()
        raise e


@router.post("/from-curl", response_model=TestCaseResponse, status_code=status.HTTP_201_CREATED)
async def create_test_case_from_curl(
    test_data: TestCaseFromCurlCreate,
    db: Session = Depends(get_db)
):
    """Create a test case from a curl command."""
    try:
        # Verify service exists
        service = db.query(Service).filter(
            Service.id == test_data.service_id,
            Service.is_active == True
        ).first()
        
        if not service:
            raise NotFoundError("Service", str(test_data.service_id))
        
        # Convert curl to test spec
        test_spec = curl_to_test_spec(test_data.curl_command, test_data.assertions)
        
        # Check if test case with same name already exists for this service
        existing_test = db.query(TestCase).filter(
            TestCase.name == test_data.name,
            TestCase.service_id == test_data.service_id,
            TestCase.is_active == True
        ).first()
        
        if existing_test:
            raise ConflictError(f"Test case with name '{test_data.name}' already exists for this service")
        
        # Create test case
        test_case = TestCase(
            service_id=test_data.service_id,
            name=test_data.name,
            description=test_data.description,
            test_spec=test_spec.dict(),
            is_active=True
        )
        
        db.add(test_case)
        db.commit()
        db.refresh(test_case)
        
        return TestCaseResponse.from_orm(test_case)
        
    except Exception as e:
        db.rollback()
        raise e


@router.get("/", response_model=PaginatedResponse[TestCaseResponse])
async def list_test_cases(
    service_id: str = None,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db)
):
    """List all test cases with optional service filtering and pagination."""
    try:
        query = db.query(TestCase).filter(TestCase.is_active == True)
        
        # Filter by service if specified
        if service_id:
            query = query.filter(TestCase.service_id == service_id)
        
        # Get total count
        total = query.count()
        
        # Get paginated results
        test_cases = (
            query
            .offset((pagination.page - 1) * pagination.size)
            .limit(pagination.size)
            .all()
        )
        
        # Calculate total pages
        pages = (total + pagination.size - 1) // pagination.size
        
        return PaginatedResponse(
            items=[TestCaseResponse.from_orm(test_case) for test_case in test_cases],
            total=total,
            page=pagination.page,
            size=pagination.size,
            pages=pages
        )
        
    except Exception as e:
        raise e


@router.get("/{test_case_id}", response_model=TestCaseResponse)
async def get_test_case(
    test_case_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific test case by ID."""
    try:
        test_case = db.query(TestCase).filter(
            TestCase.id == test_case_id,
            TestCase.is_active == True
        ).first()
        
        if not test_case:
            raise NotFoundError("Test Case", test_case_id)
        
        return TestCaseResponse.from_orm(test_case)
        
    except Exception as e:
        raise e


@router.put("/{test_case_id}", response_model=TestCaseResponse)
async def update_test_case(
    test_case_id: str,
    test_case_data: TestCaseUpdate,
    db: Session = Depends(get_db)
):
    """Update a test case."""
    try:
        test_case = db.query(TestCase).filter(
            TestCase.id == test_case_id,
            TestCase.is_active == True
        ).first()
        
        if not test_case:
            raise NotFoundError("Test Case", test_case_id)
        
        # Update fields if provided
        if test_case_data.name is not None:
            # Check if new name conflicts with existing test case
            if test_case_data.name != test_case.name:
                existing = db.query(TestCase).filter(
                    TestCase.name == test_case_data.name,
                    TestCase.service_id == test_case.service_id,
                    TestCase.id != test_case_id,
                    TestCase.is_active == True
                ).first()
                if existing:
                    raise ConflictError(f"Test case with name '{test_case_data.name}' already exists for this service")
            test_case.name = test_case_data.name
        
        if test_case_data.description is not None:
            test_case.description = test_case_data.description
        
        if test_case_data.test_spec is not None:
            test_case.test_spec = test_case_data.test_spec.dict()
        
        if test_case_data.is_active is not None:
            test_case.is_active = test_case_data.is_active
        
        # Update service if provided
        if test_case_data.service_id is not None:
            # Verify new service exists
            service = db.query(Service).filter(
                Service.id == test_case_data.service_id,
                Service.is_active == True
            ).first()
            
            if not service:
                raise NotFoundError("Service", str(test_case_data.service_id))
            
            test_case.service_id = test_case_data.service_id
        
        db.commit()
        db.refresh(test_case)
        
        return TestCaseResponse.from_orm(test_case)
        
    except Exception as e:
        db.rollback()
        raise e


@router.delete("/{test_case_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_test_case(
    test_case_id: str,
    db: Session = Depends(get_db)
):
    """Delete a test case (soft delete)."""
    try:
        test_case = db.query(TestCase).filter(
            TestCase.id == test_case_id,
            TestCase.is_active == True
        ).first()
        
        if not test_case:
            raise NotFoundError("Test Case", test_case_id)
        
        # Soft delete
        test_case.is_active = False
        db.commit()
        
    except Exception as e:
        db.rollback()
        raise e


@router.post("/{test_case_id}/activate", response_model=TestCaseResponse)
async def activate_test_case(
    test_case_id: str,
    db: Session = Depends(get_db)
):
    """Activate a deactivated test case."""
    try:
        test_case = db.query(TestCase).filter(TestCase.id == test_case_id).first()
        
        if not test_case:
            raise NotFoundError("Test Case", test_case_id)
        
        if test_case.is_active:
            raise ConflictError("Test case is already active")
        
        test_case.is_active = True
        db.commit()
        db.refresh(test_case)
        
        return TestCaseResponse.from_orm(test_case)
        
    except Exception as e:
        db.rollback()
        raise e


@router.get("/{test_case_id}/spec", response_model=TestSpecBase)
async def get_test_spec(
    test_case_id: str,
    db: Session = Depends(get_db)
):
    """Get the test specification for a test case."""
    try:
        test_case = db.query(TestCase).filter(
            TestCase.id == test_case_id,
            TestCase.is_active == True
        ).first()
        
        if not test_case:
            raise NotFoundError("Test Case", test_case_id)
        
        return TestSpecBase(**test_case.test_spec)
        
    except Exception as e:
        raise e
