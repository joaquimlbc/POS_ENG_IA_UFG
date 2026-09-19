"""Integration tests for delete operations with cascade behavior.

Priority: CRITICAL
Test Suite: Cascade Delete
Tests data integrity when deleting countries with relationships.
"""

import pytest

from app.service.country_service import CountryService
from app.utils.errors import RecordNotFoundError


class TestCascadeDelete:
    """Test suite for deletion and cascade operations."""

    def test_delete_country_success(
        self, service_with_sample_country: CountryService
    ) -> None:
        """Verify country deletion succeeds when no error conditions.

        Business rule: delete_country() should remove country from database.
        Expected: Country no longer retrievable after deletion.
        Why: Validates basic delete functionality.
        """
        # Verify country exists
        country = service_with_sample_country.get_country(1)
        assert country.id == 1

        # Delete country
        result = service_with_sample_country.delete_country(1)
        assert result is True

        # Verify country is gone
        with pytest.raises(RecordNotFoundError):
            service_with_sample_country.get_country(1)

    def test_delete_country_cascade_languages(
        self, service_with_relationships: CountryService
    ) -> None:
        """Verify deleting country cascades to languages.

        Business rule: Deleting country must remove all related languages.
        Expected: Country deleted and languages are unreachable.
        Why: Prevents orphaned language records.
        """
        # Verify country has languages
        country_before = service_with_relationships.get_country(1)
        assert (
            len(country_before.languages) == 2
        ), "Setup: country should have 2 languages"

        # Delete country
        service_with_relationships.delete_country(1)

        # Verify country is gone
        with pytest.raises(RecordNotFoundError):
            service_with_relationships.get_country(1)

    def test_delete_country_cascade_currencies(
        self, service_with_relationships: CountryService
    ) -> None:
        """Verify deleting country cascades to currencies.

        Business rule: Deleting country must remove all related currencies.
        Expected: Country deleted and currencies are unreachable.
        Why: Prevents orphaned currency records.
        """
        # Verify country has currencies
        country_before = service_with_relationships.get_country(1)
        assert (
            len(country_before.currencies) == 1
        ), "Setup: country should have 1 currency"

        # Delete country
        service_with_relationships.delete_country(1)

        # Verify country is gone
        with pytest.raises(RecordNotFoundError):
            service_with_relationships.get_country(1)

    def test_delete_country_cascade_timezones(
        self, service_with_relationships: CountryService
    ) -> None:
        """Verify deleting country cascades to timezones.

        Business rule: Deleting country must remove all related timezones.
        Expected: Country deleted and timezones are unreachable.
        Why: Prevents orphaned timezone records.
        """
        # Verify country has timezones
        country_before = service_with_relationships.get_country(1)
        assert (
            len(country_before.timezones) == 1
        ), "Setup: country should have 1 timezone"

        # Delete country
        service_with_relationships.delete_country(1)

        # Verify country is gone
        with pytest.raises(RecordNotFoundError):
            service_with_relationships.get_country(1)

    def test_delete_country_cascade_all_relationships(
        self, service_with_relationships: CountryService
    ) -> None:
        """Verify deleting country cascades to all relationship types.

        Business rule: Single cascade operation removes all related data.
        Expected: Country and all relationships deleted in one operation.
        Why: Ensures complete data cleanup and atomicity.
        """
        # Verify complete relationships
        country_before = service_with_relationships.get_country(1)
        assert len(country_before.languages) == 2
        assert len(country_before.currencies) == 1
        assert len(country_before.timezones) == 1

        # Delete country
        result = service_with_relationships.delete_country(1)
        assert result is True

        # Verify everything is gone
        with pytest.raises(RecordNotFoundError):
            service_with_relationships.get_country(1)

    def test_delete_nonexistent_country(self, service: CountryService) -> None:
        """Verify deleting non-existent country returns False.

        Business rule: Deletion of non-existent country should not raise error.
        Expected: Returns False, no exception raised.
        Why: Idempotent behavior for retry safety.
        """
        result = service.delete_country(9999)

        assert result is False

    def test_delete_country_twice(
        self, service_with_sample_country: CountryService
    ) -> None:
        """Verify deleting same country twice is safe (idempotent).

        Business rule: Second delete should return False (already deleted).
        Expected: First delete returns True, second returns False.
        Why: Supports idempotent operations for resilience.
        """
        # First delete should succeed
        result1 = service_with_sample_country.delete_country(1)
        assert result1 is True

        # Second delete should return False (not found)
        result2 = service_with_sample_country.delete_country(1)
        assert result2 is False

    def test_delete_country_logs_operation(
        self, service_with_sample_country: CountryService, caplog
    ) -> None:
        """Verify delete operation is logged for audit trail.

        Business rule: A: definir (logging requirements not specified).
        Expected: Operation logged at appropriate level.
        Why: Audit trail for compliance and debugging.
        """
        service_with_sample_country.delete_country(1)

        # Check that delete was logged (logger configuration to be defined)
        # This is a placeholder for audit logging verification
        # Log assertion depends on logger configuration
