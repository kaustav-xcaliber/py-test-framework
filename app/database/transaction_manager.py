"""
Enhanced database session management with better transaction handling
"""

from typing import Generator
from sqlalchemy.orm import Session
from contextlib import contextmanager
from app.database.database import SessionLocal
import logging

logger = logging.getLogger(__name__)

@contextmanager
def managed_transaction(db: Session):
    """
    Context manager for better transaction handling.
    Only rolls back if an exception occurs, avoiding unnecessary rollbacks.
    """
    try:
        # Ensure we start with a clean transaction state
        if db.in_transaction():
            logger.warning("Session already in transaction, committing first")
            db.commit()
        
        yield db
        
        # If we get here, no exception occurred, so commit
        db.commit()
        logger.debug("Transaction committed successfully")
        
    except Exception as e:
        logger.warning(f"Transaction failed, rolling back: {e}")
        try:
            db.rollback()
        except Exception as rollback_error:
            logger.error(f"Error during rollback: {rollback_error}")
        raise


def get_db_with_transaction() -> Generator[Session, None, None]:
    """
    Alternative dependency that handles transactions automatically.
    Use this for endpoints where you want automatic transaction management.
    """
    db = SessionLocal()
    try:
        with managed_transaction(db):
            yield db
    finally:
        db.close()


@contextmanager
def background_db_session():
    """
    Context manager specifically designed for background tasks.
    Creates a new session and handles all cleanup properly.
    """
    db = SessionLocal()
    try:
        logger.debug("Created new database session for background task")
        yield db
    except Exception as e:
        logger.error(f"Error in background database session: {e}")
        try:
            db.rollback()
        except Exception as rollback_error:
            logger.error(f"Error during rollback in background session: {rollback_error}")
        raise
    finally:
        try:
            db.close()
            logger.debug("Closed background database session")
        except Exception as close_error:
            logger.error(f"Error closing background database session: {close_error}")


# Example usage in an endpoint:
"""
@router.post("/", response_model=ServiceResponse)
async def create_service(
    service_data: ServiceCreate,
    db: Session = Depends(get_db_with_transaction)  # Use the new dependency
):
    # No need for explicit commit/rollback - handled automatically
    # Just do your database operations
    existing_service = db.query(Service).filter(
        Service.name == service_data.name
    ).first()
    
    if existing_service:
        raise ConflictError(f"Service already exists")
    
    service = Service(**service_data.model_dump())
    db.add(service)
    # Transaction is committed automatically if no exception
    # Rolled back automatically if exception occurs
    
    return ServiceResponse.from_service(service)
"""
