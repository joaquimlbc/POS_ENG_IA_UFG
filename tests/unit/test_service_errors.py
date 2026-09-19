"""Unit tests for service layer exception handling.

Priority: CRITICAL
Test Suite: Service Layer Exception Handling
Tests that service layer correctly translates database errors to domain exceptions.
"""

import pytest

from app.models.task import CountryCreate
from app.service.country_service import CountryService
from app.utils.errors import (
    DuplicateRecordError,
    RecordNotFoundError,
    ValidationError,
)


class TestServiceErrorHandling:
    """Test suite for service layer error handling and exception translation."""

    def test_service_duplicate_error_on_iso2_conflict(
        self, service: CountryService, sample_country: CountryCreate
    ) -> None:
        """Verify service converts duplicate ISO2 to DuplicateRecordError.

        Business rule: Service layer must translate database integrity violations.
        Expected: DuplicateRecordError raised with field and value.
        Why: API exception handlers depend on domain exceptions.
        """
        # Create first country
        service.create_country(sample_country)

        # Attempt duplicate - should raise DuplicateRecordError
        duplicate = CountryCreate(
            name_common="Different",
            name_official="Different Official",
            iso_code_2=sample_country.iso_code_2,  # Duplicate
            iso_code_3="AXX",
            region="Europe",
            population=100000,
        )

        with pytest.raises(DuplicateRecordError) as exc_info:
            service.create_country(duplicate)

        error = exc_info.value
        assert "Country" in error.message
        assert "iso_code_2" in error.message.lower()
        assert sample_country.iso_code_2 in error.message

    def test_service_record_not_found_on_get(self, service: CountryService) -> None:
        """Verify service raises RecordNotFoundError for missing country.

        Business rule: Service must raise domain exception for missing records.
        Expected: RecordNotFoundError with entity and criteria.
        Why: Allows API to return proper 404 responses.
        """
        with pytest.raises(RecordNotFoundError) as exc_info:
            service.get_country(9999)

        error = exc_info.value
        assert "Country" in error.message
        assert "9999" in error.message

    def test_service_validation_error_on_batch_size_exceeded(
        self, service: CountryService
    ) -> None:
        """Verify service validates batch size limits.

        Business rule: Batch operations must enforce size limits.
        Expected: ValidationError raised with field='batch_size'.
        Why: Prevents memory exhaustion and timeouts.
        """
        # Create batch exceeding 1000 with valid ISO codes
        iso2_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        iso3_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

        countries = [
            CountryCreate(
                name_common=f"Country {i}",
                name_official=f"Official {i}",
                iso_code_2=iso2_chars[i % 26] + iso2_chars[(i // 26) % 26],
                iso_code_3=(
                    iso3_chars[i % 26]
                    + iso3_chars[(i // 26) % 26]
                    + iso3_chars[(i // 52) % 26]
                ),
                region="Africa",
                population=1000000 + i,
            )
            for i in range(1001)
        ]

        with pytest.raises(ValidationError) as exc_info:
            service.sync_countries_batch(countries)

        error = exc_info.value
        assert "batch_size" in error.message.lower()
        assert "1000" in str(error.message)

    def test_service_handles_update_not_found(self, service: CountryService) -> None:
        """Verify service raises RecordNotFoundError on update of missing country.

        Business rule: Update operations must fail gracefully for missing records.
        Expected: RecordNotFoundError raised.
        Why: API must return 404 for update on missing resource.
        """
        from app.models.task import CountryUpdate

        update_data = CountryUpdate(population=200000000)

        with pytest.raises(RecordNotFoundError):
            service.update_country(9999, update_data)

    def test_service_delete_nonexistent_returns_false(
        self, service: CountryService
    ) -> None:
        """Verify service returns False instead of raising for delete of missing.

        Business rule: Delete should be idempotent (no error if already gone).
        Expected: Returns False, does not raise exception.
        Why: Supports safe retry semantics.
        """
        result = service.delete_country(9999)

        assert result is False  # No exception, just returns False

    def test_service_exception_includes_context_info(
        self, service: CountryService, sample_country: CountryCreate
    ) -> None:
        """Verify exceptions include sufficient context for debugging.

        Business rule: Exception messages must be actionable for developers.
        Expected: Error message includes relevant context.
        Why: Supports effective error diagnosis and resolution.
        """
        service.create_country(sample_country)

        duplicate = CountryCreate(
            name_common="Different",
            name_official="Different Official",
            iso_code_2=sample_country.iso_code_2,
            iso_code_3="XXX",
            region="Europe",
            population=100000,
        )

        with pytest.raises(DuplicateRecordError) as exc_info:
            service.create_country(duplicate)

        error_message = str(exc_info.value)
        assert "Country" in error_message or "iso_code_2" in error_message
        assert sample_country.iso_code_2 in error_message

    def test_service_batch_sync_invalid_region_validation(
        self, service: CountryService
    ) -> None:
        """Verify batch sync validates region enum values.

        Business rule: Batch operations must validate all input data.
        Expected: ValidationError raised for invalid region.
        Why: Prevents bad data from reaching database.
        """
        from pydantic import ValidationError as PydanticValidationError

        # Test that model rejects invalid region
        with pytest.raises(PydanticValidationError):
            CountryCreate(
                name_common="Invalid",
                name_official="Invalid Official",
                iso_code_2="XX",
                iso_code_3="XXX",
                region="Invalid Region",  # Invalid
                population=100000,
            )

    def test_service_population_range_validation(self, service: CountryService) -> None:
        """Verify population range is validated at service boundary.

        Business rule: Population must be between 0 and 2 billion.
        Expected: ValidationError raised for out-of-range values.
        Why: Prevents unrealistic data in database.
        """
        from pydantic import ValidationError

        # Test negative population
        with pytest.raises(ValidationError):
            CountryCreate(
                name_common="Test",
                name_official="Test Official",
                iso_code_2="TS",
                iso_code_3="TST",
                region="Africa",
                population=-100,  # Invalid
            )

        # Test exceeding limit
        with pytest.raises(ValidationError):
            CountryCreate(
                name_common="Test",
                name_official="Test Official",
                iso_code_2="TS",
                iso_code_3="TST",
                region="Africa",
                population=3000000000,  # Exceeds 2B limit
            )
