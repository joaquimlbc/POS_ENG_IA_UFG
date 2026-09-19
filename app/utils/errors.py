"""Custom exception classes for the application.

Defines domain-specific exceptions for handling errors at different layers
of the application with clear error messaging and context.
"""


class ApplicationError(Exception):
    """Base exception for all application errors."""

    def __init__(self, message: str, error_code: str = "INTERNAL_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class DatabaseError(ApplicationError):
    """Base exception for database-related errors."""

    def __init__(self, message: str, error_code: str = "DB_ERROR"):
        super().__init__(message, error_code)


class DuplicateRecordError(DatabaseError):
    """Raised when attempting to insert a duplicate record.

    Example:
        Country with same iso_code_2 already exists.
    """

    def __init__(self, entity: str, field: str, value: str):
        message = f"Duplicate record: {entity} with {field}='{value}' already exists"
        super().__init__(message, "DUPLICATE_RECORD")


class RecordNotFoundError(DatabaseError):
    """Raised when a record is not found in database.

    Example:
        Attempting to update a country that doesn't exist.
    """

    def __init__(self, entity: str, identifier: str):
        message = f"{entity} not found: {identifier}"
        super().__init__(message, "NOT_FOUND")


class IntegrityError(DatabaseError):
    """Raised when database integrity constraint is violated.

    Example:
        Foreign key constraint failure, unique constraint violation.
    """

    def __init__(self, message: str, details: str | None = None):
        full_message = f"Integrity constraint violation: {message}"
        if details:
            full_message += f" (Details: {details})"
        super().__init__(full_message, "INTEGRITY_ERROR")


class ValidationError(ApplicationError):
    """Raised when data validation fails.

    Example:
        Invalid region, invalid ISO code format.
    """

    def __init__(self, field: str, message: str, value: str | None = None):
        if value:
            full_message = f"Validation error in '{field}': {message} (Value: {value})"
        else:
            full_message = f"Validation error in '{field}': {message}"
        super().__init__(full_message, "VALIDATION_ERROR")


class BatchProcessError(ApplicationError):
    """Raised when batch processing encounters errors.

    Example:
        Partial failure during bulk insert of countries.
    """

    def __init__(
        self,
        total: int,
        successful: int,
        failed: int,
        errors: list[dict[str, str]] | None = None,
    ):
        message = (
            f"Batch operation failed: {successful}/{total} succeeded, {failed} failed"
        )
        super().__init__(message, "BATCH_ERROR")
        self.total = total
        self.successful = successful
        self.failed = failed
        self.errors = errors or []


class ExternalAPIError(ApplicationError):
    """Raised when external API call fails.

    Example:
        REST Countries API is unavailable or returns error.
    """

    def __init__(
        self, api_name: str, status_code: int | None = None, details: str | None = None
    ):
        message = f"External API error: {api_name}"
        if status_code:
            message += f" (Status: {status_code})"
        if details:
            message += f" - {details}"
        super().__init__(message, "EXTERNAL_API_ERROR")


class ConfigurationError(ApplicationError):
    """Raised when configuration is invalid or missing.

    Example:
        DATABASE_URL environment variable not set.
    """

    def __init__(
        self, config_key: str, message: str = "Configuration missing or invalid"
    ):
        full_message = f"Configuration error: {config_key} - {message}"
        super().__init__(full_message, "CONFIG_ERROR")


class TransactionError(DatabaseError):
    """Raised when a database transaction fails.

    Example:
        Rollback occurred due to constraint violation.
    """

    def __init__(self, operation: str, reason: str):
        message = f"Transaction failed during '{operation}': {reason}"
        super().__init__(message, "TRANSACTION_ERROR")
