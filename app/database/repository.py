"""Repository pattern implementation for data access layer.

Provides abstraction for database operations with CRUD operations,
batch processing, and error handling for Country and related entities.
"""

from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError as SQLAlchemyIntegrityError
from sqlalchemy.orm import Session

from app.database.models import Country, Currency, Language, Timezone
from app.models.task import (
    CountryCreate,
    CountryDetailResponse,
    CountryListResponse,
    CountryResponse,
    CountryUpdate,
    CurrencyCreate,
    LanguageCreate,
    RegionStatistics,
    TimezoneCreate,
)
from app.utils.errors import (
    BatchProcessError,
    DuplicateRecordError,
    IntegrityError,
    RecordNotFoundError,
    TransactionError,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class CountryRepository:
    """Repository for Country entity operations."""

    def __init__(self, session: Session):
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy Session instance
        """
        self.session = session

    def create(self, country_data: CountryCreate) -> Country:
        """Create a new country record.

        Args:
            country_data: Country creation schema

        Returns:
            Created Country model instance

        Raises:
            DuplicateRecordError: If country with same name or ISO codes exists
            IntegrityError: If database constraint is violated
        """
        try:
            country = Country(**country_data.model_dump())
            self.session.add(country)
            self.session.commit()
            self.session.refresh(country)
            logger.info(f"Country created: {country.name_common} ({country.iso_code_2})")
            return country
        except SQLAlchemyIntegrityError as e:
            self.session.rollback()
            if "UNIQUE constraint failed" in str(e) or "unique" in str(e).lower():
                raise DuplicateRecordError("Country", "name_common", country_data.name_common)
            raise IntegrityError("Failed to create country", str(e))

    def get_by_id(self, country_id: int) -> Optional[Country]:
        """Get country by ID.

        Args:
            country_id: Country primary key

        Returns:
            Country instance or None if not found
        """
        return self.session.query(Country).filter(Country.id == country_id).first()

    def get_by_iso2(self, iso_code: str) -> Optional[Country]:
        """Get country by ISO 2-letter code.

        Args:
            iso_code: ISO 2-letter code (e.g., 'BR')

        Returns:
            Country instance or None if not found
        """
        return self.session.query(Country).filter(Country.iso_code_2 == iso_code.upper()).first()

    def get_by_iso3(self, iso_code: str) -> Optional[Country]:
        """Get country by ISO 3-letter code.

        Args:
            iso_code: ISO 3-letter code (e.g., 'BRA')

        Returns:
            Country instance or None if not found
        """
        return self.session.query(Country).filter(Country.iso_code_3 == iso_code.upper()).first()

    def get_all(self, limit: int = 100, offset: int = 0) -> List[Country]:
        """Get all countries with pagination.

        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of Country instances
        """
        return (
            self.session.query(Country)
            .order_by(Country.name_common)
            .limit(limit)
            .offset(offset)
            .all()
        )

    def get_by_region(self, region: str, limit: int = 100, offset: int = 0) -> List[Country]:
        """Get countries by region with pagination.

        Args:
            region: Region name (e.g., 'Europe', 'Americas')
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of Country instances for the region
        """
        return (
            self.session.query(Country)
            .filter(Country.region == region)
            .order_by(Country.name_common)
            .limit(limit)
            .offset(offset)
            .all()
        )

    def get_paginated(
        self, page: int = 1, limit: int = 20, region: Optional[str] = None
    ) -> CountryListResponse:
        """Get paginated list of countries.

        Args:
            page: Page number (1-indexed)
            limit: Items per page (1-100)
            region: Optional region filter

        Returns:
            CountryListResponse with pagination metadata
        """
        query = self.session.query(Country)

        if region:
            query = query.filter(Country.region == region)

        total = query.count()
        offset = (page - 1) * limit

        countries = query.order_by(Country.name_common).limit(limit).offset(offset).all()

        return CountryListResponse(
            items=[CountryResponse.model_validate(c) for c in countries],
            total=total,
            page=page,
            limit=limit,
            pages=(total + limit - 1) // limit,
        )

    def update(self, country_id: int, country_data: CountryUpdate) -> Country:
        """Update an existing country.

        Args:
            country_id: Country ID
            country_data: Country update schema

        Returns:
            Updated Country instance

        Raises:
            RecordNotFoundError: If country not found
            IntegrityError: If database constraint is violated
        """
        country = self.get_by_id(country_id)
        if not country:
            raise RecordNotFoundError("Country", f"id={country_id}")

        try:
            update_data = country_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(country, field, value)

            self.session.commit()
            self.session.refresh(country)
            logger.info(f"Country updated: {country.name_common}")
            return country
        except SQLAlchemyIntegrityError as e:
            self.session.rollback()
            raise IntegrityError("Failed to update country", str(e))

    def delete(self, country_id: int) -> bool:
        """Delete a country and its related entities (cascade).

        Args:
            country_id: Country ID

        Returns:
            True if deleted, False if not found

        Raises:
            TransactionError: If deletion fails
        """
        try:
            country = self.get_by_id(country_id)
            if not country:
                return False

            self.session.delete(country)
            self.session.commit()
            logger.info(f"Country deleted: id={country_id}")
            return True
        except SQLAlchemyIntegrityError as e:
            self.session.rollback()
            raise TransactionError("delete", str(e))

    def count_all(self) -> int:
        """Get total count of countries.

        Returns:
            Total number of countries in database
        """
        return self.session.query(func.count(Country.id)).scalar() or 0

    def count_by_region(self) -> dict[str, int]:
        """Get count of countries by region.

        Returns:
            Dictionary with region names as keys and counts as values
        """
        result = (
            self.session.query(Country.region, func.count(Country.id))
            .group_by(Country.region)
            .all()
        )
        return {region: count for region, count in result}

    def upsert_batch(self, countries_data: List[CountryCreate]) -> Tuple[int, int, int]:
        """Batch insert or update countries (upsert operation).

        Uses SQLite INSERT OR REPLACE or equivalent for other databases.

        Args:
            countries_data: List of CountryCreate schemas

        Returns:
            Tuple of (total, inserted, updated) counts

        Raises:
            BatchProcessError: If batch operation partially fails
        """
        inserted = 0
        updated = 0
        failed = 0
        errors = []

        try:
            for country_data in countries_data:
                try:
                    existing = self.session.query(Country).filter(
                        (Country.iso_code_2 == country_data.iso_code_2)
                        | (Country.iso_code_3 == country_data.iso_code_3)
                    ).first()

                    if existing:
                        # Update existing
                        for field, value in country_data.model_dump().items():
                            setattr(existing, field, value)
                        updated += 1
                    else:
                        # Insert new
                        country = Country(**country_data.model_dump())
                        self.session.add(country)
                        inserted += 1

                except Exception as e:
                    failed += 1
                    errors.append({
                        "country": country_data.name_common,
                        "error": str(e),
                    })
                    logger.warning(
                        f"Failed to upsert country {country_data.name_common}: {e}"
                    )

            self.session.commit()
            logger.info(
                f"Batch upsert completed: {inserted} inserted, {updated} updated, "
                f"{failed} failed out of {len(countries_data)}"
            )

            if failed > 0:
                raise BatchProcessError(
                    total=len(countries_data),
                    successful=inserted + updated,
                    failed=failed,
                    errors=errors,
                )

            return len(countries_data), inserted, updated

        except BatchProcessError:
            raise
        except Exception as e:
            self.session.rollback()
            raise BatchProcessError(
                total=len(countries_data),
                successful=inserted + updated,
                failed=failed or 1,
                errors=errors or [{"error": str(e)}],
            )


class StatisticsRepository:
    """Repository for statistics and aggregations."""

    def __init__(self, session: Session):
        self.session = session

    def get_global_stats(self) -> dict:
        """Get global statistics across all countries.

        Returns:
            Dictionary with global stats
        """
        total_countries: int = self.session.query(func.count(Country.id)).scalar() or 0
        total_population: int = self.session.query(func.sum(Country.population)).scalar() or 0
        total_area: float = self.session.query(func.sum(Country.area)).scalar() or 0.0

        avg_population: float = 0.0
        avg_area: float = 0.0
        if total_countries > 0:
            avg_population = total_population / total_countries
            avg_area = total_area / total_countries if total_area else 0.0

        return {
            "total_countries": total_countries,
            "total_population": total_population,
            "total_area": float(total_area),
            "average_population": float(avg_population),
            "average_area": float(avg_area),
        }

    def get_regional_stats(self) -> List[RegionStatistics]:
        """Get statistics by region.

        Returns:
            List of RegionStatistics
        """
        result = self.session.query(
            Country.region,
            func.count(Country.id).label("total_countries"),
            func.sum(Country.population).label("total_population"),
            func.sum(Country.area).label("total_area"),
        ).group_by(Country.region).all()

        return [
            RegionStatistics(
                region=region,
                total_countries=count,
                total_population=population or 0,
                total_area=float(area or 0),
            )
            for region, count, population, area in result
        ]
