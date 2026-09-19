"""Unit tests for PriorityAdvisor data quality scoring and prioritization.

Priority: ALTO (PRIORIDADE 2)
Test Suite: Data Quality Scoring
Tests business logic for assessing data quality and prioritizing updates.
"""

import pytest

from app.database.models import Country, Language
from app.service.priority_advisor import DataQuality, PriorityAdvisor, SyncPriority


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

        result = advisor.assess_quality(country)

        assert result.score >= 90
        assert result.missing_fields == []

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

        result = advisor.assess_quality(country)

        assert result.score < 90
        assert "area" in result.missing_fields
        assert "latitude" in result.missing_fields
        assert "longitude" in result.missing_fields

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

        result = advisor.assess_quality(critical_country)

        assert result.priority == SyncPriority.CRITICAL
        assert "name_official" in result.missing_fields

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
        assert result["total_countries"] == 5
        assert set(result["quality_distribution"].keys()) == {
            "complete",
            "partial",
            "incomplete",
            "invalid",
        }
        assert "average_quality_score" in result
        assert "critical_updates_needed" in result
        assert "high_priority" in result

    def test_priority_advisor_enum_values(self, advisor: PriorityAdvisor) -> None:
        """Verify SyncPriority enum has expected values.

        Business rule: Priority levels should be CRITICAL, HIGH, MEDIUM, LOW.
        Expected: All 4 priority levels defined.
        Why: Validates priority enum completeness.
        """
        # Verify enum has expected members
        assert hasattr(SyncPriority, "CRITICAL")
        assert hasattr(SyncPriority, "HIGH")
        assert {p.value for p in SyncPriority} == {"critical", "high", "medium", "low"}

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
        for item in result:
            assert item.priority in SyncPriority
            assert item.country_id is not None
            assert item.name.startswith("Country")

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

    def test_assess_quality_handles_empty_list(self, advisor: PriorityAdvisor) -> None:
        """Verify batch assessment handles empty country list gracefully.

        Business rule: Empty batch should return empty summary, not error.
        Expected: Returns empty or zero-count summary.
        Why: Edge case safety for API resilience.
        """
        result = advisor.assess_batch_quality([])

        assert isinstance(result, dict), "Should return dict even for empty list"
        assert result["total_countries"] == 0
        assert result["average_quality_score"] == 0
        assert result["critical_updates_needed"] == 0

    def test_prioritize_handles_empty_list(self, advisor: PriorityAdvisor) -> None:
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

        assert isinstance(result1, dict)
        assert result1 == result2


class TestOutOfRangeValidation:
    """Tests for numeric-range validation branches in assess_quality."""

    @pytest.fixture
    def advisor(self) -> PriorityAdvisor:
        return PriorityAdvisor()

    def _complete_country(self, **overrides: object) -> Country:
        """A country with every field populated, so only `overrides` deviate."""
        defaults = dict(
            id=1,
            name_common="Testland",
            name_official="Republic of Testland",
            iso_code_2="TL",
            iso_code_3="TLD",
            region="Europe",
            subregion="Western Europe",
            population=1_000_000,
            area=50_000.0,
            latitude=10.0,
            longitude=20.0,
        )
        defaults.update(overrides)
        return Country(**defaults)

    def test_population_out_of_range_is_flagged(self, advisor: PriorityAdvisor) -> None:
        """Verify a population above MAX_POPULATION is flagged and penalized."""
        country = self._complete_country(population=3_000_000_000)

        result = advisor.assess_quality(country)

        assert "population (out of range)" in result.missing_fields

    def test_area_out_of_range_is_flagged(self, advisor: PriorityAdvisor) -> None:
        """Verify an area above MAX_AREA (larger than Earth) is flagged."""
        country = self._complete_country(area=300_000_000.0)

        result = advisor.assess_quality(country)

        assert "area (out of range)" in result.missing_fields

    def test_latitude_out_of_range_is_flagged(self, advisor: PriorityAdvisor) -> None:
        """Verify a latitude outside [-90, 90] is flagged.

        Why: Pydantic schemas validate this on API input, but PriorityAdvisor
        runs directly against ORM rows, which could come from any source
        (e.g. a future bulk-import path) without that guard.
        """
        country = self._complete_country(latitude=95.0)

        result = advisor.assess_quality(country)

        assert "latitude (out of range)" in result.missing_fields

    def test_longitude_out_of_range_is_flagged(self, advisor: PriorityAdvisor) -> None:
        """Verify a longitude outside [-180, 180] is flagged."""
        country = self._complete_country(longitude=200.0)

        result = advisor.assess_quality(country)

        assert "longitude (out of range)" in result.missing_fields

    def test_partial_quality_without_relationships_is_medium_priority(
        self, advisor: PriorityAdvisor
    ) -> None:
        """Verify a PARTIAL-quality country with no relationships gets MEDIUM.

        Why: Pins the specific quality_level == PARTIAL -> MEDIUM branch,
        distinct from the has_relationships and INVALID/INCOMPLETE branches.
        """
        # Population out of range alone costs 15 points (100 -> 85): PARTIAL band.
        country = self._complete_country(population=3_000_000_000)
        assert len(country.languages) == 0  # no relationships attached

        result = advisor.assess_quality(country)

        assert result.quality_level == DataQuality.PARTIAL
        assert result.priority == SyncPriority.MEDIUM

    def test_country_with_relationships_and_area_gets_low_priority(
        self, advisor: PriorityAdvisor
    ) -> None:
        """Verify a country with relationships and area data gets LOW priority,
        even though it's otherwise a mid-quality record.

        Why: Pins the has_relationships branch specifically (as opposed to
        the unrelated fallback that also returns LOW at the end of the
        method) by using a country with a language attached.
        """
        country = self._complete_country(population=3_000_000_000)
        country.languages.append(Language(language_code="en", language_name="English"))

        result = advisor.assess_quality(country)

        assert "area" not in result.missing_fields
        assert result.priority == SyncPriority.LOW


class TestGenerateReasonFallback:
    """Tests for the defensive fallback branch in _generate_reason."""

    def test_fallback_used_when_no_missing_fields_and_not_complete(self) -> None:
        """Verify the generic fallback message for a non-COMPLETE, non-INVALID
        quality level with no missing fields.

        Why: assess_quality() always populates missing_fields alongside any
        score deduction, so this branch is unreachable through the public
        API today; it exists as a defensive catch-all. Exercised directly
        against the private helper to keep it covered and correct if that
        invariant ever changes.
        """
        advisor = PriorityAdvisor()

        reason = advisor._generate_reason(DataQuality.PARTIAL, [])

        assert reason == "Quality assessment completed"


class TestShouldUpdateCountry:
    """Tests for should_update_country's merge-worthiness heuristics."""

    @pytest.fixture
    def advisor(self) -> PriorityAdvisor:
        return PriorityAdvisor()

    def _complete_country(self, **overrides: object) -> Country:
        defaults = dict(
            id=1,
            name_common="Testland",
            name_official="Republic of Testland",
            iso_code_2="TL",
            iso_code_3="TLD",
            region="Europe",
            subregion="Western Europe",
            population=1_000_000,
            area=50_000.0,
            latitude=10.0,
            longitude=20.0,
        )
        defaults.update(overrides)
        return Country(**defaults)

    def test_invalid_current_data_always_recommends_update(
        self, advisor: PriorityAdvisor
    ) -> None:
        """Verify an INVALID/INCOMPLETE current record always recommends update."""
        country = self._complete_country(name_official=None, area=None, latitude=None)

        assert advisor.should_update_country(country, {}) is True

    def test_new_area_fills_a_gap(self, advisor: PriorityAdvisor) -> None:
        """Verify offering an area value when the country has none recommends update."""
        country = self._complete_country(area=None)

        assert advisor.should_update_country(country, {"area": 12345.0}) is True

    def test_new_latitude_fills_a_gap(self, advisor: PriorityAdvisor) -> None:
        """Verify offering a latitude value when the country has none recommends update."""
        country = self._complete_country(latitude=None)

        assert advisor.should_update_country(country, {"latitude": 5.0}) is True

    def test_significant_population_change_recommends_update(
        self, advisor: PriorityAdvisor
    ) -> None:
        """Verify a >5% population change recommends update."""
        country = self._complete_country(population=1_000_000)

        assert advisor.should_update_country(country, {"population": 1_100_000}) is True

    def test_minor_population_change_does_not_recommend_update(
        self, advisor: PriorityAdvisor
    ) -> None:
        """Verify a <5% population change does not recommend update."""
        country = self._complete_country(population=1_000_000)

        assert (
            advisor.should_update_country(country, {"population": 1_010_000}) is False
        )

    def test_no_new_data_and_complete_country_does_not_recommend_update(
        self, advisor: PriorityAdvisor
    ) -> None:
        """Verify a complete country with no better new data needs no update."""
        country = self._complete_country()

        assert advisor.should_update_country(country, {}) is False
