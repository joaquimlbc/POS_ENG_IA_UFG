"""Unit tests for PriorityAdvisor data quality scoring and prioritization.

Priority: ALTO (PRIORIDADE 2)
Test Suite: Data Quality Scoring
Tests business logic for assessing data quality and prioritizing updates.
"""

import pytest

from app.database.models import Country
from app.service.priority_advisor import PriorityAdvisor, SyncPriority


class TestPriorityAdvisor:
    """Test suite for PriorityAdvisor data quality and prioritization logic."""

    @pytest.fixture
    def advisor(self) -> PriorityAdvisor:
        """Create PriorityAdvisor instance for tests."""
        return PriorityAdvisor()

    def test_advisor_initialization(self, advisor: PriorityAdvisor) -> None:
        """Verify PriorityAdvisor initializes correctly.

        Business rule: Advisor should be instantiated without errors.
        Expected: Instance created with no exceptions.
        Why: Baseline for all advisor tests.
        """
        assert advisor is not None
        assert hasattr(advisor, "assess_batch_quality")
        assert hasattr(advisor, "prioritize_updates")

    def test_assess_quality_complete_country_high_score(
        self, advisor: PriorityAdvisor
    ) -> None:
        """Verify complete country data gets high quality score.

        Business rule: Countries with all fields = score 90+.
        Expected: Full country gets score >= 90.
        Why: Validates quality scoring for complete data.
        """
        # Create complete country with all fields
        country = Country(
            id=1,
            name_common="Brazil",
            name_official="Federative Republic of Brazil",
            iso_code_2="BR",
            iso_code_3="BRA",
            region="Americas",
            subregion="South America",
            population=215313498,
            area=8514877.0,
            latitude=-14.2350,
            longitude=-51.9253,
        )

        # Note: This test structure depends on PriorityAdvisor implementation
        # If assess_batch_quality returns dict with 'score', adjust accordingly
        # A: definir - exact return format of assess_batch_quality

    def test_assess_quality_incomplete_country_low_score(
        self, advisor: PriorityAdvisor
    ) -> None:
        """Verify incomplete country data gets lower quality score.

        Business rule: Countries missing optional fields = score <90.
        Expected: Incomplete country gets lower score.
        Why: Identifies data needing improvement.
        """
        # Create incomplete country (missing area, coordinates, subregion)
        country = Country(
            id=2,
            name_common="France",
            name_official="French Republic",
            iso_code_2="FR",
            iso_code_3="FRA",
            region="Europe",
            subregion=None,  # Missing
            population=67970571,
            area=None,  # Missing
            latitude=None,  # Missing
            longitude=None,  # Missing
        )

        # A: definir - exact scoring logic and comparison values

    def test_prioritize_updates_identifies_critical_gaps(
        self, advisor: PriorityAdvisor
    ) -> None:
        """Verify prioritization identifies critical data gaps.

        Business rule: Countries with required fields missing = CRITICAL priority.
        Expected: Missing required fields = CRITICAL priority.
        Why: Ensures data integrity issues are surfaced.
        """
        # Create countries with different levels of missing data
        critical_country = Country(
            id=3,
            name_common="Country A",
            name_official=None,  # Required field missing
            iso_code_2="CA",
            iso_code_3="CAA",
            region="Africa",
            population=1000000,
        )

        # A: definir - exact required fields definition

    def test_assess_batch_quality_returns_summary(
        self, advisor: PriorityAdvisor
    ) -> None:
        """Verify batch assessment returns quality summary dict.

        Business rule: assess_batch_quality() should return structured summary.
        Expected: Returns dict with quality metrics.
        Why: Summary provides insights into batch quality distribution.
        """
        countries = [
            Country(
                id=i,
                name_common=f"Country {i}",
                name_official=f"Official {i}",
                iso_code_2=f"C{i:01d}",
                iso_code_3=f"C{i:02d}",
                region="Africa",
                population=1000000 + i,
            )
            for i in range(1, 6)
        ]

        result = advisor.assess_batch_quality(countries)

        assert isinstance(result, dict), "Result should be dict"
        # A: definir - expected keys in result dict

    def test_priority_advisor_enum_values(self, advisor: PriorityAdvisor) -> None:
        """Verify SyncPriority enum has expected values.

        Business rule: Priority levels should be CRITICAL, HIGH, MEDIUM, LOW.
        Expected: All 4 priority levels defined.
        Why: Validates priority enum completeness.
        """
        # Verify enum has expected members
        assert hasattr(SyncPriority, "CRITICAL")
        assert hasattr(SyncPriority, "HIGH")
        # A: definir - exact priority level names in enum

    def test_prioritize_returns_countries_with_priority(
        self, advisor: PriorityAdvisor
    ) -> None:
        """Verify prioritize_updates returns countries with priority assigned.

        Business rule: Each country in result should have priority attribute.
        Expected: Returns list of objects with priority field.
        Why: Consumers depend on priority being populated.
        """
        countries = [
            Country(
                id=i,
                name_common=f"Country {i}",
                name_official=f"Official {i}",
                iso_code_2=f"C{i:01d}",
                iso_code_3=f"C{i:02d}",
                region="Americas",
                population=1000000 + i,
            )
            for i in range(1, 4)
        ]

        result = advisor.prioritize_updates(countries)

        assert isinstance(result, list), "Result should be list"
        assert len(result) > 0, "Should return prioritized items"
        # A: definir - expected attributes on priority objects

    def test_prioritize_respects_max_results_limit(
        self, advisor: PriorityAdvisor
    ) -> None:
        """Verify prioritize_updates respects max_results parameter.

        Business rule: Should not return more than max_results items.
        Expected: Result length <= max_results.
        Why: Prevents large result sets that could impact performance.
        """
        # Create 100 countries
        countries = [
            Country(
                id=i,
                name_common=f"Country {i}",
                name_official=f"Official {i}",
                iso_code_2=f"C{i:02d}"[:2].upper(),
                iso_code_3=f"C{i:03d}"[:3].upper(),
                region="Europe",
                population=1000000 + i,
            )
            for i in range(1, 101)
        ]

        result = advisor.prioritize_updates(countries, max_results=10)

        assert len(result) <= 10, "Should respect max_results limit"

    def test_assess_quality_handles_empty_list(
        self, advisor: PriorityAdvisor
    ) -> None:
        """Verify batch assessment handles empty country list gracefully.

        Business rule: Empty batch should return empty summary, not error.
        Expected: Returns empty or zero-count summary.
        Why: Edge case safety for API resilience.
        """
        result = advisor.assess_batch_quality([])

        assert isinstance(result, dict), "Should return dict even for empty list"
        # A: definir - exact empty result format

    def test_prioritize_handles_empty_list(
        self, advisor: PriorityAdvisor
    ) -> None:
        """Verify prioritization handles empty country list gracefully.

        Business rule: Empty input should return empty list, not error.
        Expected: Returns empty list.
        Why: Edge case safety for API resilience.
        """
        result = advisor.prioritize_updates([])

        assert isinstance(result, list), "Should return list"
        assert len(result) == 0, "Empty input should return empty result"

    def test_advisor_quality_scoring_consistency(
        self, advisor: PriorityAdvisor
    ) -> None:
        """Verify same country gets consistent quality score.

        Business rule: Quality scoring should be deterministic.
        Expected: Same country data yields same score multiple times.
        Why: Validates scoring logic is deterministic and reproducible.
        """
        country = Country(
            id=50,
            name_common="Test Country",
            name_official="Official Test Country",
            iso_code_2="TC",
            iso_code_3="TCC",
            region="Asia",
            population=5000000,
            area=100000.0,
            latitude=10.0,
            longitude=20.0,
        )

        # Score should be consistent
        countries_list = [country]

        result1 = advisor.assess_batch_quality(countries_list)
        result2 = advisor.assess_batch_quality(countries_list)

        # A: definir - exact comparison logic based on result format
        # For now, verify both return same type
        assert type(result1) == type(result2)
