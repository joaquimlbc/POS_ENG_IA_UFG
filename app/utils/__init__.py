"""Utilities module for the application.

Provides logging, error handling, and common helper functions.
"""

from app.utils.errors import (
    ApplicationError,
    BatchProcessError,
    ConfigurationError,
    DatabaseError,
    DuplicateRecordError,
    ExternalAPIError,
    IntegrityError,
    RecordNotFoundError,
    TransactionError,
    ValidationError,
)
from app.utils.logger import get_logger

__all__ = [
    # Logger
    "get_logger",
    # Errors
    "ApplicationError",
    "DatabaseError",
    "DuplicateRecordError",
    "RecordNotFoundError",
    "IntegrityError",
    "ValidationError",
    "BatchProcessError",
    "ExternalAPIError",
    "ConfigurationError",
    "TransactionError",
]
