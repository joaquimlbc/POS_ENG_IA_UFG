"""Priority advisor for data synchronization and processing decisions.

Provides heuristics and decision logic for prioritizing which data
to synchronize, update, or process based on business rules and data quality.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List

from app.database.models import Country
from app.utils.logger import get_logger

logger = get_logger(__name__)


class SyncPriority(str, Enum):
    """Data synchronization priority levels."""

    CRITICAL = "critical"  # Missing or invalid data
    HIGH = "high"          # Significant changes detected
    MEDIUM = "medium"      # Minor updates
    LOW = "low"           # No changes detected


class DataQuality(str, Enum):
    """Data quality assessment levels."""

    COMPLETE = "complete"      # All fields present and valid
    PARTIAL = "partial"        # Some fields missing but valid
    INCOMPLETE = "incomplete"  # Multiple missing fields
    INVALID = "invalid"        # Data validation failed


@dataclass
class CountryQualityScore:
    """Quality score for a country record."""

    country_id: int
    name: str
    quality_level: DataQuality
    score: float  # 0-100
    missing_fields: List[str]
    priority: SyncPriority
    reason: str


class PriorityAdvisor:
    """Advisor for determining sync and processing priorities.

    Uses business rules to determine which data should be prioritized
    for synchronization, update, or processing operations.
    """

    # Required fields for complete data
    REQUIRED_FIELDS = {
        "name_common",
        "name_official",
        "iso_code_2",
        "iso_code_3",
        "region",
        "population",
    }

    # Optional fields (still important for quality)
    QUALITY_FIELDS = {
        "area",
        "latitude",
        "longitude",
        "subregion",
    }

    # Population thresholds
    MIN_POPULATION = 0
    MAX_POPULATION = 2_000_000_000  # ~2 billion

    # Area thresholds (km²)
    MIN_AREA = 0.1
    MAX_AREA = 200_000_000  # Larger than Earth

    def assess_quality(self, country: Country) -> CountryQualityScore:
        """Assess data quality of a country record.

        Args:
            country: Country model instance

        Returns:
            Quality score with assessment details
        """
        missing_fields = []
        score = 100.0

        # Check required fields
        for field in self.REQUIRED_FIELDS:
            value = getattr(country, field, None)
            if not value or (isinstance(value, str) and not value.strip()):
                missing_fields.append(field)
                score -= 20

        # Check quality fields
        for field in self.QUALITY_FIELDS:
            value = getattr(country, field, None)
            if not value:
                missing_fields.append(field)
                score -= 10

        # Validate numeric ranges
        if country.population and not (
            self.MIN_POPULATION <= country.population <= self.MAX_POPULATION
        ):
            missing_fields.append("population (out of range)")
            score -= 15

        if country.area and not (self.MIN_AREA <= country.area <= self.MAX_AREA):
            missing_fields.append("area (out of range)")
            score -= 10

        # Validate coordinates
        if country.latitude is not None and not (-90 <= country.latitude <= 90):
            missing_fields.append("latitude (out of range)")
            score -= 10

        if country.longitude is not None and not (-180 <= country.longitude <= 180):
            missing_fields.append("longitude (out of range)")
            score -= 10

        # Determine quality level
        if score >= 90:
            quality_level = DataQuality.COMPLETE
        elif score >= 70:
            quality_level = DataQuality.PARTIAL
        elif score >= 50:
            quality_level = DataQuality.INCOMPLETE
        else:
            quality_level = DataQuality.INVALID

        # Determine priority
        priority = self._determine_priority(
            quality_level, missing_fields, len(country.languages) > 0
        )

        reason = self._generate_reason(quality_level, missing_fields)

        return CountryQualityScore(
            country_id=country.id,
            name=country.name_common,
            quality_level=quality_level,
            score=max(0, score),
            missing_fields=missing_fields,
            priority=priority,
            reason=reason,
        )

    def _determine_priority(
        self,
        quality_level: DataQuality,
        missing_fields: List[str],
        has_relationships: bool,
    ) -> SyncPriority:
        """Determine sync priority based on quality and completeness.

        Args:
            quality_level: Overall quality assessment
            missing_fields: List of missing or invalid fields
            has_relationships: Whether country has relationships (languages, etc)

        Returns:
            Priority level for synchronization
        """
        if quality_level == DataQuality.INVALID:
            return SyncPriority.CRITICAL

        if quality_level == DataQuality.INCOMPLETE:
            return SyncPriority.HIGH

        # If has geographic data and relationships, low priority
        if has_relationships and "area" not in missing_fields:
            return SyncPriority.LOW

        # Partial data without relationships = medium
        if quality_level == DataQuality.PARTIAL:
            return SyncPriority.MEDIUM

        return SyncPriority.LOW

    def _generate_reason(
        self, quality_level: DataQuality, missing_fields: List[str]
    ) -> str:
        """Generate human-readable reason for quality assessment.

        Args:
            quality_level: Quality level
            missing_fields: Missing fields list

        Returns:
            Human-readable reason
        """
        if quality_level == DataQuality.COMPLETE:
            return "All required and quality fields present"

        if quality_level == DataQuality.INVALID:
            return f"Invalid data: {', '.join(missing_fields[:3])}"

        if missing_fields:
            return f"Missing: {', '.join(missing_fields[:3])}"

        return "Quality assessment completed"

    def prioritize_updates(
        self, countries: List[Country], max_results: int = 50
    ) -> List[CountryQualityScore]:
        """Prioritize countries for update based on quality.

        Args:
            countries: List of country records
            max_results: Maximum number to return

        Returns:
            Prioritized list of countries needing updates
        """
        scores = [self.assess_quality(country) for country in countries]

        # Sort by priority and score
        priority_order = {
            SyncPriority.CRITICAL: 0,
            SyncPriority.HIGH: 1,
            SyncPriority.MEDIUM: 2,
            SyncPriority.LOW: 3,
        }

        sorted_scores = sorted(
            scores,
            key=lambda x: (
                priority_order[x.priority],
                -x.score,  # Descending score
            ),
        )

        logger.info(
            f"Prioritized {len(sorted_scores)} countries for update, "
            f"top {max_results} selected"
        )

        return sorted_scores[:max_results]

    def assess_batch_quality(self, countries: List[Country]) -> dict:
        """Assess quality of entire batch of countries.

        Args:
            countries: List of countries to assess

        Returns:
            Summary statistics about batch quality
        """
        scores = [self.assess_quality(country) for country in countries]

        quality_counts = {
            DataQuality.COMPLETE: 0,
            DataQuality.PARTIAL: 0,
            DataQuality.INCOMPLETE: 0,
            DataQuality.INVALID: 0,
        }

        for score in scores:
            quality_counts[score.quality_level] += 1

        avg_score = sum(s.score for s in scores) / len(scores) if scores else 0

        return {
            "total_countries": len(countries),
            "average_quality_score": avg_score,
            "quality_distribution": {
                level.value: count for level, count in quality_counts.items()
            },
            "critical_updates_needed": sum(
                1 for s in scores if s.priority == SyncPriority.CRITICAL
            ),
            "high_priority": sum(
                1 for s in scores if s.priority == SyncPriority.HIGH
            ),
        }

    def should_update_country(self, country: Country, new_data: dict) -> bool:
        """Determine if a country record should be updated based on data quality.

        Args:
            country: Existing country record
            new_data: New data to potentially merge

        Returns:
            True if update is recommended, False otherwise
        """
        current_score = self.assess_quality(country)

        # Always update if current data is invalid or incomplete
        if current_score.quality_level in (
            DataQuality.INVALID,
            DataQuality.INCOMPLETE,
        ):
            return True

        # Check if new data is better
        if new_data.get("area") and not country.area:
            return True

        if (
            new_data.get("latitude") is not None
            and country.latitude is None
        ):
            return True

        # Update if population changed significantly (>5%)
        if new_data.get("population") and country.population:
            change_pct = abs(
                (new_data["population"] - country.population) / country.population
            )
            if change_pct > 0.05:
                return True

        return False
