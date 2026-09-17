"""Integration tests for country CRUD operations.

Priority: CRITICAL
Test Suite: Duplicate Country Rejection
Tests business rule that prevents duplicate ISO codes in database.
"""

import pytest

from app.models.task import CountryCreate
from app.service.country_service import CountryService
from app.utils.errors import DuplicateRecordError


class TestCountryCRUD:
    """Test suite for country create, read, update, delete operations."""

    def test_create_country_success(
        self, service: CountryService, sample_country: CountryCreate
    ):
        """Verify country creation succeeds with valid data.

        Business rule: Country with unique ISO codes should be created successfully.
        """
        result = service.create_country(sample_country)

        assert result.id > 0
        assert result.name_common == sample_country.name_common
        assert result.iso_code_2 == sample_country.iso_code_2
        assert result.iso_code_3 == sample_country.iso_code_3
        assert result.created_at is not None
        assert result.updated_at is not None

    def test_create_duplicate_iso2_rejected(
        self, service: CountryService, sample_country: CountryCreate
    ):
        """Verify duplicate ISO2 code is rejected.

        Business rule: Cannot create country with duplicate ISO2 code.
        Expected error: DuplicateRecordError with status 409 Conflict.
        """
        # Create first country
        service.create_country(sample_country)

        # Attempt to create duplicate
        duplicate = CountryCreate(
            name_common="Brazil2",
            name_official="Different Name",
            iso_code_2=sample_country.iso_code_2,  # Duplicate ISO2
            iso_code_3="BRX",  # Different ISO3
            region=sample_country.region,
            population=200000000,
        )

        with pytest.raises(DuplicateRecordError) as exc_info:
            service.create_country(duplicate)

        assert "iso_code_2" in str(exc_info.value).lower()
        assert sample_country.iso_code_2 in str(exc_info.value)

    def test_create_duplicate_iso3_rejected(
        self, service: CountryService, sample_country: CountryCreate
    ):
        """Verify duplicate ISO3 code is rejected.

        Business rule: Cannot create country with duplicate ISO3 code.
        Expected error: DuplicateRecordError with status 409 Conflict.
        """
        # Create first country
        service.create_country(sample_country)

        # Attempt to create duplicate ISO3
        duplicate = CountryCreate(
            name_common="Brazil2",
            name_official="Different Name",
            iso_code_2="BZ",  # Different ISO2
            iso_code_3=sample_country.iso_code_3,  # Duplicate ISO3
            region=sample_country.region,
            population=200000000,
        )

        with pytest.raises(DuplicateRecordError) as exc_info:
            service.create_country(duplicate)

        assert "iso_code_3" in str(exc_info.value).lower()
        assert sample_country.iso_code_3 in str(exc_info.value)

    def test_get_country_by_id_success(
        self, service_with_sample_country: CountryService
    ):
        """Verify retrieving country by ID returns correct data.

        Business rule: Country should be retrievable by ID with all relationships.
        """
        country = service_with_sample_country.get_country(1)

        assert country.id == 1
        assert country.name_common == "Brazil"
        assert country.iso_code_2 == "BR"
        assert country.languages == []  # No languages added yet
        assert country.currencies == []
        assert country.timezones == []

    def test_update_country_success(
        self, service_with_sample_country: CountryService
    ):
        """Verify country update succeeds with valid data.

        Business rule: Mutable fields can be updated without affecting ISO codes.
        """
        from app.models.task import CountryUpdate

        update_data = CountryUpdate(
            population=220000000,
            name_common="Brazil (Updated)",
        )

        result = service_with_sample_country.update_country(1, update_data)

        assert result.id == 1
        assert result.population == 220000000
        assert result.name_common == "Brazil (Updated)"
        assert result.iso_code_2 == "BR"  # ISO codes unchanged
        assert result.iso_code_3 == "BRA"

    def test_update_region_validation(
        self, service_with_sample_country: CountryService
    ):
        """Verify invalid region is rejected on update.

        Business rule: Region must be one of 5 valid regions.
        Expected error: ValidationError from Pydantic.
        """
        from app.models.task import CountryUpdate
        from pydantic import ValidationError

        invalid_update = CountryUpdate(region="Invalid Region")

        with pytest.raises(ValidationError) as exc_info:
            CountryUpdate.model_validate(
                {"region": "Invalid Region"}, from_attributes=True
            )

        error_dict = exc_info.value.errors()[0]
        assert "Region" in error_dict["msg"] or "region" in error_dict["loc"]

    def test_update_population_range_validation(
        self, service_with_sample_country: CountryService
    ):
        """Verify population range is enforced.

        Business rule: Population must be between 0 and 2 billion.
        Expected error: ValidationError from Pydantic.
        """
        from app.models.task import CountryUpdate
        from pydantic import ValidationError

        # Test negative population
        with pytest.raises(ValidationError):
            CountryUpdate(population=-1)

        # Test exceeding 2B limit
        with pytest.raises(ValidationError):
            CountryUpdate(population=2000000001)
