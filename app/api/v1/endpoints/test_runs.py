"""Test execution and test run management endpoints."""

import time
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.models import TestRun, TestCase, TestResult, Service
from app.schemas.schemas import (
    TestRunCreate,
    TestRunUpdate,
    TestRunResponse,
    TestResultCreate,
    TestResultUpdate,
    TestResultResponse,
    PaginationParams,
    PaginatedResponse,
    TestSpecBase
)
from app.core.exceptions import NotFoundError, ConflictError, TestExecutionError
from app.testrunner.executor import TestExecutor

router = APIRouter()


@router.post("/", response_model=TestRunResponse, status_code=status.HTTP_201_CREATED)
async def create_test_run(
    test_run_data: TestRunCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create a new test run and optionally execute tests."""
    try:
        # Create test run
        test_run = TestRun(
            name=test_run_data.name,
            status="running",
            total_tests=0,
            passed_tests=0,
            failed_tests=0,
            execution_time_ms=0
        )
        
        db.add(test_run)
        db.commit()
        db.refresh(test_run)
        
        # If test case IDs are provided, execute them
        if hasattr(test_run_data, 'test_case_ids') and test_run_data.test_case_ids:
            print(f"Starting background execution for test run {test_run.id} with {len(test_run_data.test_case_ids)} test cases")
            background_tasks.add_task(
                execute_test_run_background,
                str(test_run.id),
                test_run_data.test_case_ids
            )
        else:
            print(f"No test case IDs provided for test run {test_run.id}")
        
        return TestRunResponse.from_orm(test_run)
        
    except Exception as e:
        db.rollback()
        raise e


@router.post("/execute", response_model=TestRunResponse, status_code=status.HTTP_201_CREATED)
async def execute_test_run(
    test_case_ids: List[str],
    test_run_name: str = None,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """Execute a test run with specified test cases."""
    try:
        # Create test run
        test_run = TestRun(
            name=test_run_name or f"Test Run - {int(datetime.now(timezone.utc).timestamp())}",
            status="running",
            total_tests=len(test_case_ids),
            passed_tests=0,
            failed_tests=0,
            execution_time_ms=0
        )
        
        db.add(test_run)
        db.commit()
        db.refresh(test_run)
        
        # Execute tests in background if background tasks are available
        if background_tasks:
            background_tasks.add_task(
                execute_test_run_background,
                str(test_run.id),
                test_case_ids
            )
        else:
            # Execute tests synchronously
            execute_test_run_background(str(test_run.id), test_case_ids, db)
        
        return TestRunResponse.from_orm(test_run)
        
    except Exception as e:
        db.rollback()
        raise e


def execute_test_run_background(test_run_id: str, test_case_ids: List[str]):
    """Execute test run in background."""
    print(f"Starting test execution for test run {test_run_id} with {len(test_case_ids)} test cases")
    
    # Use the new background session manager
    from app.database.transaction_manager import background_db_session, managed_transaction
    
    try:
        start_time = time.time()
        
        with background_db_session() as db:
            with managed_transaction(db):
                # Get test run
                test_run = db.query(TestRun).filter(TestRun.id == test_run_id).first()
                if not test_run:
                    print(f"Test run {test_run_id} not found")
                    return
        
                # Get test cases
                test_cases = db.query(TestCase).filter(
                    TestCase.id.in_(test_case_ids),
                    TestCase.is_active == True
                ).all()
                
                passed_tests = 0
                failed_tests = 0
                
                # Execute each test case
                for test_case in test_cases:
                    try:
                        # Get service
                        service = db.query(Service).filter(
                            Service.id == test_case.service_id,
                            Service.is_active == True
                        ).first()
                        
                        if not service:
                            # Mark test as failed
                            test_result = TestResult(
                                test_run_id=test_run_id,
                                test_case_id=test_case.id,
                                test_name=test_case.name,
                                status="failed",
                                error_message=f"Service {test_case.service_id} not found or inactive",
                                start_time=datetime.now(timezone.utc),
                                end_time=datetime.now(timezone.utc),
                                duration_ms=0,
                                request_size=0,
                                response_size=0,
                                response_time_ms=0
                            )
                            db.add(test_result)
                            failed_tests += 1
                            continue
                        
                        # Create test executor with authentication
                        auth_config = None
                        if service.auth_config:
                            auth_config = service.auth_config.to_dict(redact_secrets=False)
                        
                        with TestExecutor(service.base_url, auth_config=auth_config) as executor:
                            # Convert test spec back to TestSpecBase
                            test_spec = TestSpecBase(**test_case.test_spec)
                            
                            # Execute test
                            result = executor.execute_test(test_spec)
                            
                            # Create test result
                            test_result = TestResult(
                                test_run_id=test_run_id,
                                test_case_id=test_case.id,
                                test_name=result.test_name,
                                status=result.status,
                                error_message=result.error_message,
                                response_data=result.response_data,
                                assertion_results=result.assertion_results,
                                start_time=datetime.now(timezone.utc),
                                end_time=datetime.now(timezone.utc),
                                duration_ms=0,  # Will be calculated
                                request_size=0,  # Will be calculated
                                response_size=0,  # Will be calculated
                                response_time_ms=0  # Will be calculated
                            )
                            
                            db.add(test_result)
                            
                            if result.status == "passed":
                                passed_tests += 1
                            else:
                                failed_tests += 1
                        
                    except Exception as e:
                        # Mark test as failed due to execution error
                        test_result = TestResult(
                            test_run_id=test_run_id,
                            test_case_id=test_case.id,
                            test_name=test_case.name,
                            status="failed",
                            error_message=str(e),
                            start_time=datetime.now(timezone.utc),
                            end_time=datetime.now(timezone.utc),
                            duration_ms=0,
                            request_size=0,
                            response_size=0,
                            response_time_ms=0
                        )
                        db.add(test_result)
                        failed_tests += 1
                        print(f"Error executing test case {test_case.id}: {e}")
                
                # Update test run
                end_time = time.time()
                execution_time_ms = int((end_time - start_time) * 1000)
                
                test_run.passed_tests = passed_tests
                test_run.failed_tests = failed_tests
                test_run.execution_time_ms = execution_time_ms
                test_run.status = "completed"
                test_run.completed_at = datetime.now(timezone.utc)
                
                print(f"Completed test run {test_run_id}: {passed_tests} passed, {failed_tests} failed")
        
    except Exception as e:
        # Handle errors with proper transaction rollback
        print(f"Error executing test run {test_run_id}: {e}")
        
        # Try to update test run status to failed in a separate session
        try:
            with background_db_session() as error_db:
                with managed_transaction(error_db):
                    test_run = error_db.query(TestRun).filter(TestRun.id == test_run_id).first()
                    if test_run:
                        test_run.status = "failed"
                        test_run.completed_at = datetime.now(timezone.utc)
        except Exception as update_error:
            print(f"Failed to update test run status: {update_error}")


@router.get("/", response_model=PaginatedResponse[TestRunResponse])
async def list_test_runs(
    status: str = None,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db)
):
    """List all test runs with optional status filtering and pagination."""
    try:
        query = db.query(TestRun)
        
        # Filter by status if specified
        if status:
            query = query.filter(TestRun.status == status)
        
        # Get total count
        total = query.count()
        
        # Get paginated results
        test_runs = (
            query
            .order_by(TestRun.started_at.desc())
            .offset((pagination.page - 1) * pagination.size)
            .limit(pagination.size)
            .all()
        )
        
        # Calculate total pages
        pages = (total + pagination.size - 1) // pagination.size
        
        return PaginatedResponse(
            items=[TestRunResponse.from_orm(test_run) for test_run in test_runs],
            total=total,
            page=pagination.page,
            size=pagination.size,
            pages=pages
        )
        
    except Exception as e:
        raise e


@router.get("/{test_run_id}", response_model=TestRunResponse)
async def get_test_run(
    test_run_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific test run by ID."""
    try:
        test_run = db.query(TestRun).filter(TestRun.id == test_run_id).first()
        
        if not test_run:
            raise NotFoundError("Test Run", test_run_id)
        
        return TestRunResponse.from_orm(test_run)
        
    except Exception as e:
        raise e


@router.put("/{test_run_id}", response_model=TestRunResponse)
async def update_test_run(
    test_run_id: str,
    test_run_data: TestRunUpdate,
    db: Session = Depends(get_db)
):
    """Update a test run."""
    try:
        test_run = db.query(TestRun).filter(TestRun.id == test_run_id).first()
        
        if not test_run:
            raise NotFoundError("Test Run", test_run_id)
        
        # Update fields if provided
        if test_run_data.name is not None:
            test_run.name = test_run_data.name
        
        if test_run_data.status is not None:
            test_run.status = test_run_data.status
        
        if test_run_data.completed_at is not None:
            test_run.completed_at = test_run_data.completed_at
        
        db.commit()
        db.refresh(test_run)
        
        return TestRunResponse.from_orm(test_run)
        
    except Exception as e:
        db.rollback()
        raise e


@router.delete("/{test_run_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_test_run(
    test_run_id: str,
    db: Session = Depends(get_db)
):
    """Delete a test run and all its results."""
    try:
        test_run = db.query(TestRun).filter(TestRun.id == test_run_id).first()
        
        if not test_run:
            raise NotFoundError("Test Run", test_run_id)
        
        # Delete test results first (cascade should handle this)
        db.delete(test_run)
        db.commit()
        
    except Exception as e:
        db.rollback()
        raise e


@router.get("/{test_run_id}/results", response_model=List[TestResultResponse])
async def get_test_run_results(
    test_run_id: str,
    db: Session = Depends(get_db)
):
    """Get all test results for a specific test run."""
    try:
        # Verify test run exists
        test_run = db.query(TestRun).filter(TestRun.id == test_run_id).first()
        if not test_run:
            raise NotFoundError("Test Run", test_run_id)
        
        # Get test results
        test_results = db.query(TestResult).filter(
            TestResult.test_run_id == test_run_id
        ).all()
        
        return [TestResultResponse.from_orm(result) for result in test_results]
        
    except Exception as e:
        raise e


@router.post("/{test_run_id}/cancel", response_model=TestRunResponse)
async def cancel_test_run(
    test_run_id: str,
    db: Session = Depends(get_db)
):
    """Cancel a running test run."""
    try:
        test_run = db.query(TestRun).filter(TestRun.id == test_run_id).first()
        
        if not test_run:
            raise NotFoundError("Test Run", test_run_id)
        
        if test_run.status != "running":
            raise ConflictError("Test run is not running")
        
        test_run.status = "cancelled"
        test_run.completed_at = datetime.utcnow()
        
        db.commit()
        db.refresh(test_run)
        
        return TestRunResponse.from_orm(test_run)
        
    except Exception as e:
        db.rollback()
        raise e


@router.post("/{test_run_id}/retry", response_model=TestRunResponse, status_code=status.HTTP_201_CREATED)
async def retry_test_run(
    test_run_id: str,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """Retry a failed test run."""
    try:
        # Get original test run
        original_test_run = db.query(TestRun).filter(TestRun.id == test_run_id).first()
        if not original_test_run:
            raise NotFoundError("Test Run", test_run_id)
        
        # Get test case IDs from original run
        test_results = db.query(TestResult).filter(
            TestResult.test_run_id == test_run_id
        ).all()
        
        test_case_ids = [result.test_case_id for result in test_results]
        
        # Create new test run
        new_test_run = TestRun(
            name=f"Retry: {original_test_run.name}",
            status="running",
            total_tests=len(test_case_ids),
            passed_tests=0,
            failed_tests=0,
            execution_time_ms=0
        )
        
        db.add(new_test_run)
        db.commit()
        db.refresh(new_test_run)
        
        # Execute tests in background
        if background_tasks:
            background_tasks.add_task(
                execute_test_run_background,
                str(new_test_run.id),
                test_case_ids
            )
        else:
            execute_test_run_background(str(new_test_run.id), test_case_ids, db)
        
        return TestRunResponse.from_orm(new_test_run)
        
    except Exception as e:
        db.rollback()
        raise e
