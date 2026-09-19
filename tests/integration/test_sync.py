"""Integration tests for country synchronization operations.

Priority: CRITICAL
Test Suite: Batch Upsert Consistency
Tests high-volume data ingestion from REST Countries API.
"""

import pytest

from app.models.task import CountryCreate
from app.service.country_service import CountryService, CountrySyncResult
from app.utils.errors import ValidationError


class TestCountrySync:
    """Test suite for batch synchronization operations."""

    def test_sync_batch_250_countries_success(self, service: CountryService) -> None:
        """Verify batch sync of 250 countries completes successfully.

        Business rule: Batch sync should upsert all records without errors.
        Expected: 250 inserted, 0 failed, status='success'.
        Why: Validates complete data ingestion from REST Countries API.
        """
        countries = []
        regions = ["Africa", "Americas", "Asia", "Europe", "Oceania"]
        iso2_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        iso3_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

        for i in range(250):
            region = regions[i % 5]
            iso2 = iso2_chars[i % 26] + iso2_chars[(i // 26) % 26]
            iso3 = (
                iso3_chars[i % 26]
                + iso3_chars[(i // 26) % 26]
                + iso3_chars[(i // 52) % 26]
            )
            country = CountryCreate(
                name_common=f"Country {i}",
                name_official=f"Official Country {i}",
                iso_code_2=iso2,
                iso_code_3=iso3,
                region=region,
                subregion=f"Subregion {i}",
                population=1000000 + i * 1000,
                area=10000.0 + i,
                latitude=-90 + (i % 180),
                longitude=-180 + (i % 360),
            )
            countries.append(country)

        result = service.sync_countries_batch(countries, validate_quality=False)

        assert isinstance(result, CountrySyncResult)
        assert result.total_processed == 250
        assert result.inserted == 250
        assert result.failed == 0
        assert result.status == "success"
        assert "250 countries" in result.message.lower()

    def test_sync_batch_upsert_updates_existing(
        self, service_with_sample_country: CountryService
    ) -> None:
        """Verify batch sync updates existing countries correctly.

        Business rule: Upsert should update if country exists, insert if new.
        Expected: 1 updated (existing country), 1 inserted (new country).
        Why: Validates idempotent sync behavior for API updates.
        """
        # Prepare: 1 existing (Brazil) + 1 new (France)
        existing_update = CountryCreate(
            name_common="Brazil",
            name_official="Federative Republic of Brazil (Updated)",
            iso_code_2="BR",
            iso_code_3="BRA",
            region="Americas",
            population=220000000,  # Updated population
        )

        new_country = CountryCreate(
            name_common="France",
            name_official="French Republic",
            iso_code_2="FR",
            iso_code_3="FRA",
            region="Europe",
            population=67970571,
        )

        result = service_with_sample_country.sync_countries_batch(
            [existing_update, new_country], validate_quality=False
        )

        assert result.total_processed == 2
        assert result.inserted == 1  # France
        assert result.updated == 1  # Brazil

    def test_sync_batch_exceeds_limit_rejected(self, service: CountryService) -> None:
        """Verify batch size limit (1000) is enforced.

        Business rule: Batch must not exceed 1000 records to prevent memory issues.
        Expected: ValidationError with batch_size field.
        Why: Prevents timeout and memory exhaustion on large syncs.
        """
        countries = []
        regions = ["Africa", "Americas", "Asia", "Europe", "Oceania"]
        iso2_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        iso3_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

        for i in range(1001):  # Exceeds limit by 1
            region = regions[i % 5]
            iso2 = iso2_chars[i % 26] + iso2_chars[(i // 26) % 26]
            iso3 = (
                iso3_chars[i % 26]
                + iso3_chars[(i // 26) % 26]
                + iso3_chars[(i // 52) % 26]
            )
            country = CountryCreate(
                name_common=f"Country {i}",
                name_official=f"Official Country {i}",
                iso_code_2=iso2,
                iso_code_3=iso3,
                region=region,
                population=1000000 + i,
            )
            countries.append(country)

        with pytest.raises(ValidationError) as exc_info:
            service.sync_countries_batch(countries)

        assert "batch_size" in str(exc_info.value).lower()
        assert "1000" in str(exc_info.value)

    def test_sync_batch_exactly_1000_allowed(self, service: CountryService) -> None:
        """Verify batch size limit of exactly 1000 is allowed.

        Business rule: Batch size limit is exactly 1000, not less.
        Expected: sync succeeds with 1000 records.
        Why: Validates boundary condition at maximum allowed batch.
        """
        countries = []
        regions = ["Africa", "Americas", "Asia", "Europe", "Oceania"]
        iso2_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        iso3_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

        for i in range(1000):
            region = regions[i % 5]
            iso2 = iso2_chars[i % 26] + iso2_chars[(i // 26) % 26]
            iso3 = (
                iso3_chars[i % 26]
                + iso3_chars[(i // 26) % 26]
                + iso3_chars[(i // 52) % 26]
            )
            country = CountryCreate(
                name_common=f"Country {i}",
                name_official=f"Official Country {i}",
                iso_code_2=iso2,
                iso_code_3=iso3,
                region=region,
                population=1000000 + i,
            )
            countries.append(country)

        result = service.sync_countries_batch(countries, validate_quality=False)

        assert result.total_processed == 1000
        assert result.status == "success"

    def test_sync_batch_empty_list(self, service: CountryService) -> None:
        """Verify empty batch is handled gracefully.

        Business rule: A: definir (empty batch behavior undefined).
        Expected: Either status='success' with 0 processed, or specific error.
        Why: Edge case handling for API robustness.
        """
        result = service.sync_countries_batch([], validate_quality=False)

        assert result.total_processed == 0
        assert result.inserted == 0
        assert result.status == "success"

    def test_sync_batch_generates_unique_sync_id(self, service: CountryService) -> None:
        """Verify each sync operation gets unique sync_id.

        Business rule: Every sync must have unique ID for tracking.
        Expected: Different sync_id for sequential syncs.
        Why: Ensures audit trail and prevents collision in logs.
        """
        country1 = CountryCreate(
            name_common="Country 1",
            name_official="Official 1",
            iso_code_2="AA",
            iso_code_3="AAA",
            region="Africa",
            population=1000000,
        )

        country2 = CountryCreate(
            name_common="Country 2",
            name_official="Official 2",
            iso_code_2="AB",
            iso_code_3="AAB",
            region="Americas",
            population=2000000,
        )

        result1 = service.sync_countries_batch([country1], validate_quality=False)
        result2 = service.sync_countries_batch([country2], validate_quality=False)

        assert result1.sync_id != result2.sync_id
        assert "sync_" in result1.sync_id
        assert "sync_" in result2.sync_id
