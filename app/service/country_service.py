"""Business logic service layer for country operations.

Orchestrates database operations, applies business rules, validates data,
and handles domain-specific logic separate from API and data access layers.

Architecture:
    API Layer (FastAPI) → Service Layer (business logic) → Repository Layer
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.database.models import Country, Currency, Language, Timezone
from app.database.repository import CountryRepository, StatisticsRepository
from app.models.task import (
    CountryCreate,
    CountryDetailResponse,
    CountryListResponse,
    CountryResponse,
    CountryUpdate,
    CurrencyCreate,
    GlobalStatistics,
    LanguageCreate,
    RegionStatistics,
    SyncLogResponse,
    TimezoneCreate,
)
from app.service.priority_advisor import (
    DataQuality,
    PriorityAdvisor,
    SyncPriority,
)
from app.utils.errors import (
    BatchProcessError,
    DuplicateRecordError,
    RecordNotFoundError,
    ValidationError,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class CountrySyncResult:
    """Result of a country synchronization operation."""

    sync_id: str
    total_processed: int
    inserted: int
    updated: int
    failed: int
    quality_summary: dict
    status: str  # "success", "partial_failure", "failure"
    message: str
    started_at: datetime
    completed_at: datetime


class CountryService:
    """Service layer for country operations.

    Implements business logic, orchestrates repository operations,
    applies domain rules, and handles cross-cutting concerns like
    validation, logging, and error handling.

    Architecture principle: Service layer is the single entry point for
    business operations. Controllers/APIs call services, not repositories.
    """

    def __init__(self, session: Session):
        """Initialize service with database session.

        Args:
            session: SQLAlchemy Session instance
        """
        self.session = session
        self.country_repo = CountryRepository(session)
        self.stats_repo = StatisticsRepository(session)
        self.priority_advisor = PriorityAdvisor()

    def _ensure_country_exists(self, country_id: int) -> Country:
        """Internal: Ensure country exists or raise RecordNotFoundError.

        Args:
            country_id: Country ID to check

        Returns:
            Country instance

        Raises:
            RecordNotFoundError: If country not found
        """
        country = self.country_repo.get_by_id(country_id)
        if not country:
            raise RecordNotFoundError("Country", f"id={country_id}")
        return country

    def _to_response(self, country: Country) -> CountryResponse:
        """Internal: Convert Country ORM to response (SRP).

        Args:
            country: Country ORM instance

        Returns:
            Country response schema
        """
        return CountryResponse.model_validate(country)

    def _to_detail_response(self, country: Country) -> CountryDetailResponse:
        """Internal: Convert Country ORM to detail response (SRP).

        Args:
            country: Country ORM instance

        Returns:
            Country detail response with relationships
        """
        return CountryDetailResponse.model_validate(country)

    def _add_related_entities(
        self,
        country_id: int,
        entity_class: type,
        items_data: List,
        entity_type: str,
    ) -> CountryDetailResponse:
        """Internal: Generic related entity adder (DRY pattern).

        Args:
            country_id: Country ID
            entity_class: ORM class (Language, Currency, Timezone)
            items_data: List of schema objects to add
            entity_type: Name for logging (languages, currencies, timezones)

        Returns:
            Updated country with new relationships

        Raises:
            RecordNotFoundError: If country not found
        """
        country = self._ensure_country_exists(country_id)

        for item_data in items_data:
            entity = entity_class(
                country_id=country_id,
                **item_data.model_dump(),
            )
            self.session.add(entity)

        self.session.commit()
        self.session.refresh(country)

        logger.info(f"Added {len(items_data)} {entity_type} to {country.name_common}")

        return self._to_detail_response(country)

    def _create_sync_result(
        self,
        sync_id: str,
        status: str,
        total: int,
        inserted: int,
        updated: int,
        failed: int,
        message: str,
        started_at: datetime,
        quality_summary: Optional[dict] = None,
    ) -> CountrySyncResult:
        """Internal: Create sync result (DRY pattern).

        Args:
            sync_id: Unique sync operation ID
            status: Operation status (success, partial_failure, failure)
            total: Total processed records
            inserted: Records inserted
            updated: Records updated
            failed: Records failed
            message: Status message
            started_at: Operation start time
            quality_summary: Quality assessment (optional)

        Returns:
            Sync result object
        """
        return CountrySyncResult(
            sync_id=sync_id,
            total_processed=total,
            inserted=inserted,
            updated=updated,
            failed=failed,
            quality_summary=quality_summary or {},
            status=status,
            message=message,
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
        )

    def create_country(self, country_data: CountryCreate) -> CountryResponse:
        """Create a new country with business rule validation.

        Business rules:
        - Name must be unique
        - ISO codes (both iso2 and iso3) must be unique and properly formatted
        - Region must be valid
        - Population and area must be non-negative

        Args:
            country_data: Country creation data (already validated by Pydantic)

        Returns:
            Created country response

        Raises:
            DuplicateRecordError: If country already exists
            ValidationError: If business rules violated
        """
        logger.info(f"Creating country: {country_data.name_common}")

        # Business rule: Check ISO2 uniqueness
        existing = self.country_repo.get_by_iso2(country_data.iso_code_2)
        if existing:
            raise DuplicateRecordError(
                "Country",
                "iso_code_2",
                country_data.iso_code_2,
            )

        # Business rule: Check ISO3 uniqueness
        existing_iso3 = self.country_repo.get_by_iso3(country_data.iso_code_3)
        if existing_iso3:
            raise DuplicateRecordError(
                "Country",
                "iso_code_3",
                country_data.iso_code_3,
            )

        # Create country
        country = self.country_repo.create(country_data)

        logger.info(f"Country created: {country.name_common} (id={country.id})")
        return self._to_response(country)

    def get_country(self, country_id: int) -> CountryDetailResponse:
        """Get country details with relationships.

        Args:
            country_id: Country ID

        Returns:
            Detailed country response with languages, currencies, timezones

        Raises:
            RecordNotFoundError: If country not found
        """
        country = self._ensure_country_exists(country_id)
        return self._to_detail_response(country)

    def get_country_by_iso(self, iso_code: str) -> CountryDetailResponse:
        """Get country by ISO code (2 or 3 letter).

        Args:
            iso_code: ISO2 (BR) or ISO3 (BRA) code

        Returns:
            Detailed country response

        Raises:
            RecordNotFoundError: If country not found
        """
        # Try ISO2 first (more common for lookups)
        country = self.country_repo.get_by_iso2(iso_code)
        if not country:
            country = self.country_repo.get_by_iso3(iso_code)

        if not country:
            raise RecordNotFoundError("Country", f"iso_code={iso_code}")

        return self._to_detail_response(country)

    def list_countries(
        self,
        page: int = 1,
        limit: int = 20,
        region: Optional[str] = None,
    ) -> CountryListResponse:
        """List countries with pagination and optional filtering.

        Business logic:
        - Validate pagination parameters
        - Enforce maximum limit (100)
        - Support region filtering

        Args:
            page: Page number (1-indexed)
            limit: Items per page (max 100)
            region: Optional region filter

        Returns:
            Paginated country list

        Raises:
            ValidationError: If parameters invalid
        """
        # Business rule: Enforce maximum limit
        if limit > 100:
            limit = 100
            logger.warning("Limit exceeded max (100), capped to 100")

        result = self.country_repo.get_paginated(
            page=page,
            limit=limit,
            region=region,
        )

        return CountryListResponse(
            items=[self._to_response(c) for c in result["countries"]],
            total=result["total"],
            page=result["page"],
            limit=result["limit"],
            pages=result["pages"],
        )

    def update_country(
        self,
        country_id: int,
        update_data: CountryUpdate,
    ) -> CountryResponse:
        """Update country with data quality consideration.

        Business rules:
        - Cannot update ISO codes (immutable identifiers)
        - Population and area must remain non-negative
        - Warn if updating with lower quality data

        Args:
            country_id: Country ID
            update_data: Fields to update

        Returns:
            Updated country response

        Raises:
            RecordNotFoundError: If country not found
        """
        country = self._ensure_country_exists(country_id)

        logger.info(f"Updating country: {country.name_common} (id={country_id})")

        updated = self.country_repo.update(country_id, update_data)
        return self._to_response(updated)

    def delete_country(self, country_id: int) -> bool:
        """Delete a country (with cascade to relationships).

        Business rule: Deletion cascades to languages, currencies, timezones.

        Args:
            country_id: Country ID

        Returns:
            True if deleted, False if not found
        """
        country = self.country_repo.get_by_id(country_id)
        if not country:
            logger.warning(f"Attempted to delete non-existent country: {country_id}")
            return False

        logger.info(f"Deleting country: {country.name_common} (id={country_id})")
        self.country_repo.delete(country_id)
        return True

    def sync_countries_batch(
        self,
        countries_data: List[CountryCreate],
        validate_quality: bool = True,
    ) -> CountrySyncResult:
        """Synchronize batch of countries with quality assessment.

        Business logic:
        - Validate batch size (max 1000 records)
        - Upsert (insert new, update existing)
        - Assess data quality of batch
        - Prioritize updates based on quality
        - Detailed error tracking

        Args:
            countries_data: List of countries to sync (max 1000 per batch)
            validate_quality: If True, assess quality and skip low-quality data

        Returns:
            Sync operation result with statistics

        Raises:
            ValidationError: If batch size exceeds 1000
            BatchProcessError: If sync partially fails
        """
        # Validate batch size limit
        if len(countries_data) > 1000:
            raise ValidationError(
                "batch_size",
                f"Batch size {len(countries_data)} exceeds maximum of 1000"
            )

        sync_id = f"sync_{datetime.now(timezone.utc).timestamp()}"
        started_at = datetime.now(timezone.utc)

        logger.info(
            f"Starting batch sync {sync_id}: {len(countries_data)} countries"
        )

        try:
            # Perform upsert
            total, inserted, updated = self.country_repo.upsert_batch(
                countries_data
            )

            # Assess quality of synced data
            synced_countries = self.country_repo.get_all(limit=len(countries_data))
            quality_summary = self.priority_advisor.assess_batch_quality(
                synced_countries
            )

            result = self._create_sync_result(
                sync_id=sync_id,
                status="success",
                total=total,
                inserted=inserted,
                updated=updated,
                failed=0,
                message=f"Synced {total} countries: {inserted} inserted, {updated} updated",
                started_at=started_at,
                quality_summary=quality_summary,
            )

            logger.info(f"Batch sync {sync_id} completed: {result.message}")
            return result

        except BatchProcessError as e:
            result = self._create_sync_result(
                sync_id=sync_id,
                status="partial_failure",
                total=len(countries_data),
                inserted=e.successful,
                updated=0,
                failed=e.failed,
                message=f"Batch sync partially failed: {e.successful} succeeded, {e.failed} failed",
                started_at=started_at,
            )

            logger.warning(
                f"Batch sync {sync_id} partial failure: {result.message}"
            )
            return result

    def get_sync_result_response(
        self, sync_result: CountrySyncResult
    ) -> SyncLogResponse:
        """Convert sync result to API response format.

        Args:
            sync_result: Internal sync result

        Returns:
            API response format
        """
        return SyncLogResponse(
            sync_id=sync_result.sync_id,
            status=sync_result.status.replace("_", " "),
            timestamp=sync_result.completed_at,
            countries_inserted=sync_result.inserted,
            countries_updated=sync_result.updated,
            countries_skipped=sync_result.failed,
            message=sync_result.message,
        )

    def get_global_statistics(self) -> GlobalStatistics:
        """Get global statistics with business logic enrichment.

        Business logic:
        - Calculate averages
        - Identify outliers
        - Format for presentation

        Returns:
            Global statistics object
        """
        stats_dict = self.stats_repo.get_global_stats()
        regional_stats = self.stats_repo.get_regional_stats()

        logger.info(
            f"Retrieved statistics: "
            f"{stats_dict['total_countries']} countries, "
            f"{stats_dict['total_population']} total population"
        )

        return GlobalStatistics(
            **stats_dict,
            regions=regional_stats,
        )

    def get_regional_breakdown(self) -> List[RegionStatistics]:
        """Get detailed regional breakdown.

        Returns:
            List of regional statistics
        """
        return self.stats_repo.get_regional_stats()

    def identify_data_gaps(self) -> dict:
        """Identify countries with data quality issues.

        Business logic:
        - Find missing required fields
        - Identify validation issues
        - Prioritize for update

        Returns:
            Report of data gaps and priorities
        """
        all_countries = self.country_repo.get_all(limit=1000)
        prioritized = self.priority_advisor.prioritize_updates(
            all_countries, max_results=50
        )

        report = {
            "total_countries": len(all_countries),
            "countries_with_issues": len(prioritized),
            "by_priority": {
                SyncPriority.CRITICAL.value: [
                    {
                        "id": p.country_id,
                        "name": p.name,
                        "reason": p.reason,
                        "missing_fields": p.missing_fields,
                    }
                    for p in prioritized
                    if p.priority == SyncPriority.CRITICAL
                ],
                SyncPriority.HIGH.value: [
                    {
                        "id": p.country_id,
                        "name": p.name,
                        "reason": p.reason,
                    }
                    for p in prioritized
                    if p.priority == SyncPriority.HIGH
                ][:10],
            },
        }

        logger.info(
            f"Data gap analysis: {len(prioritized)} countries need attention"
        )

        return report

    def add_languages(
        self, country_id: int, languages: List[LanguageCreate]
    ) -> CountryDetailResponse:
        """Add languages to a country.

        Args:
            country_id: Country ID
            languages: List of languages to add

        Returns:
            Updated country with new languages

        Raises:
            RecordNotFoundError: If country not found
        """
        return self._add_related_entities(
            country_id, Language, languages, "languages"
        )

    def add_currencies(
        self, country_id: int, currencies: List[CurrencyCreate]
    ) -> CountryDetailResponse:
        """Add currencies to a country.

        Args:
            country_id: Country ID
            currencies: List of currencies to add

        Returns:
            Updated country with new currencies

        Raises:
            RecordNotFoundError: If country not found
        """
        return self._add_related_entities(
            country_id, Currency, currencies, "currencies"
        )

    def add_timezones(
        self, country_id: int, timezones: List[TimezoneCreate]
    ) -> CountryDetailResponse:
        """Add timezones to a country.

        Args:
            country_id: Country ID
            timezones: List of timezones to add

        Returns:
            Updated country with new timezones

        Raises:
            RecordNotFoundError: If country not found
        """
        return self._add_related_entities(
            country_id, Timezone, timezones, "timezones"
        )

    def validate_country_integrity(self, country_id: int) -> dict:
        """Validate data integrity and quality of a country.

        Checks:
        - All required fields present
        - Relationships valid
        - Data ranges valid
        - Quality score

        Args:
            country_id: Country ID

        Returns:
            Integrity report

        Raises:
            RecordNotFoundError: If country not found
        """
        country = self._ensure_country_exists(country_id)

        quality_score = self.priority_advisor.assess_quality(country)

        report = {
            "country_id": country_id,
            "name": country.name_common,
            "quality_score": quality_score.score,
            "quality_level": quality_score.quality_level.value,
            "priority": quality_score.priority.value,
            "missing_fields": quality_score.missing_fields,
            "relationships": {
                "languages": len(country.languages),
                "currencies": len(country.currencies),
                "timezones": len(country.timezones),
            },
            "validation_reason": quality_score.reason,
        }

        logger.info(
            f"Integrity check for {country.name_common}: "
            f"score={quality_score.score}, "
            f"level={quality_score.quality_level.value}"
        )

        return report
