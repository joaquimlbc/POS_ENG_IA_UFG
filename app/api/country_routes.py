"""REST API routes for country operations.

All endpoints use the service layer (CountryService) for business logic.
Dependency injection provides database sessions automatically.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from app.database import get_db_session
from app.models.task import (
    CountryCreate,
    CountryDetailResponse,
    CountryListResponse,
    CountryResponse,
    CountryUpdate,
    CurrencyCreate,
    GlobalStatistics,
    HealthCheckResponse,
    LanguageCreate,
    RegionStatistics,
    SyncLogResponse,
    TimezoneCreate,
)
from app.scripts.ingest import ingest_countries
from app.service import CountryService
from app.utils.errors import (
    DuplicateRecordError,
    RecordNotFoundError,
    ValidationError,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["countries"])


def get_country_service(session: Session = Depends(get_db_session)) -> CountryService:
    """Dependency to provide CountryService with database session."""
    return CountryService(session)


# ============================================================================
# CREATE - POST
# ============================================================================


@router.post(
    "/countries",
    response_model=CountryResponse,
    status_code=201,
    summary="Create country",
    responses={
        201: {"description": "Country created successfully"},
        409: {"description": "Country already exists (duplicate ISO codes)"},
        422: {"description": "Validation error"},
    },
)
def create_country(
    country_data: CountryCreate,
    service: CountryService = Depends(get_country_service),
) -> CountryResponse:
    """Create a new country.

    **Request body:**
    - name_common: Name commonly used
    - name_official: Official name
    - iso_code_2: ISO 2-letter code (e.g., BR)
    - iso_code_3: ISO 3-letter code (e.g., BRA)
    - region: Region (Africa, Americas, Asia, Europe, Oceania)
    - population: Total population
    - area: Area in km² (optional)
    - latitude: Latitude (optional)
    - longitude: Longitude (optional)
    - subregion: Subregion (optional)
    """
    try:
        return service.create_country(country_data)
    except DuplicateRecordError as e:
        logger.warning(f"Duplicate country: {e.message}")
        raise HTTPException(status_code=409, detail=e.message)
    except ValidationError as e:
        logger.warning(f"Validation error creating country: {e.message}")
        raise HTTPException(status_code=422, detail=e.message)
    except Exception as e:
        logger.error(f"Failed to create country: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# READ - GET
# ============================================================================


@router.get(
    "/countries",
    response_model=CountryListResponse,
    summary="List countries",
    responses={
        200: {"description": "Paginated list of countries"},
    },
)
def list_countries(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    region: Optional[str] = Query(
        None,
        description="Filter by region (Africa, Americas, Asia, Europe, Oceania)",
    ),
    service: CountryService = Depends(get_country_service),
) -> CountryListResponse:
    """List all countries with pagination and optional region filtering.

    **Query parameters:**
    - page: Page number (default 1)
    - limit: Items per page (default 20, max 100)
    - region: Optional region filter
    """
    try:
        return service.list_countries(page=page, limit=limit, region=region)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.message)
    except Exception as e:
        logger.error(f"Failed to list countries: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/countries/{country_id}",
    response_model=CountryDetailResponse,
    summary="Get country by ID",
    responses={
        200: {"description": "Country details with relationships"},
        404: {"description": "Country not found"},
    },
)
def get_country(
    country_id: int = Path(..., gt=0, description="Country ID"),
    service: CountryService = Depends(get_country_service),
) -> CountryDetailResponse:
    """Get detailed information about a country by ID.

    Includes: languages, currencies, timezones.
    """
    try:
        return service.get_country(country_id)
    except RecordNotFoundError as e:
        logger.warning(f"Country not found: {e.message}")
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        logger.error(f"Failed to get country: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/countries/iso/{iso_code}",
    response_model=CountryDetailResponse,
    summary="Get country by ISO code",
    responses={
        200: {"description": "Country details"},
        404: {"description": "Country not found"},
    },
)
def get_country_by_iso(
    iso_code: str = Path(..., description="ISO2 (BR) or ISO3 (BRA) code"),
    service: CountryService = Depends(get_country_service),
) -> CountryDetailResponse:
    """Get country by ISO 2-letter or 3-letter code.

    **Example:** /countries/iso/BR or /countries/iso/BRA
    """
    try:
        return service.get_country_by_iso(iso_code.upper())
    except RecordNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        logger.error(f"Failed to get country by ISO: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# UPDATE - PUT
# ============================================================================


@router.put(
    "/countries/{country_id}",
    response_model=CountryResponse,
    summary="Update country",
    responses={
        200: {"description": "Country updated successfully"},
        404: {"description": "Country not found"},
        409: {"description": "Duplicate field value"},
    },
)
def update_country(
    country_id: int = Path(..., gt=0, description="Country ID"),
    country_data: Optional[CountryUpdate] = None,
    service: CountryService = Depends(get_country_service),
) -> CountryResponse:
    """Update country fields (all optional).

    Only provided fields will be updated.
    """
    try:
        # mypy (without the pydantic plugin, which is incompatible with the
        # pinned mypy/pydantic versions here) can't see that every
        # CountryUpdate field has a Field(None, ...) default, so it treats
        # a no-arg construction as missing required arguments. Valid at
        # runtime: all fields are Optional with real defaults.
        empty_update = country_data or CountryUpdate()  # type: ignore[call-arg]
        return service.update_country(country_id, empty_update)
    except RecordNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except DuplicateRecordError as e:
        raise HTTPException(status_code=409, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.message)
    except Exception as e:
        logger.error(f"Failed to update country: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# DELETE
# ============================================================================


@router.delete(
    "/countries/{country_id}",
    status_code=204,
    summary="Delete country",
    responses={
        204: {"description": "Country deleted successfully"},
        404: {"description": "Country not found"},
    },
)
def delete_country(
    country_id: int = Path(..., gt=0, description="Country ID"),
    service: CountryService = Depends(get_country_service),
) -> None:
    """Delete a country (cascade deletes relationships).

    Deletes: languages, currencies, timezones.
    """
    if not service.delete_country(country_id):
        raise HTTPException(status_code=404, detail="Country not found")

    logger.info(f"Country deleted: id={country_id}")


# ============================================================================
# RELATIONSHIPS
# ============================================================================


@router.post(
    "/countries/{country_id}/languages",
    response_model=CountryDetailResponse,
    status_code=201,
    summary="Add languages to country",
    responses={
        201: {"description": "Languages added successfully"},
        404: {"description": "Country not found"},
        422: {"description": "Validation error"},
    },
)
def add_languages(
    country_id: int = Path(..., gt=0),
    languages: Optional[List[LanguageCreate]] = None,
    service: CountryService = Depends(get_country_service),
) -> CountryDetailResponse:
    """Add languages to a country.

    Request body should contain a list of language objects with:
    - language_code: ISO 639-1 or 639-3 language code (e.g., "pt", "en")
    - language_name: Language name (e.g., "Portuguese", "English")
    """
    try:
        return service.add_languages(country_id, languages or [])
    except RecordNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.message)
    except Exception as e:
        logger.error(f"Failed to add languages: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/countries/{country_id}/currencies",
    response_model=CountryDetailResponse,
    status_code=201,
    summary="Add currencies to country",
    responses={
        201: {"description": "Currencies added successfully"},
        404: {"description": "Country not found"},
        422: {"description": "Validation error"},
    },
)
def add_currencies(
    country_id: int = Path(..., gt=0),
    currencies: Optional[List[CurrencyCreate]] = None,
    service: CountryService = Depends(get_country_service),
) -> CountryDetailResponse:
    """Add currencies to a country.

    Request body should contain a list of currency objects with:
    - currency_code: ISO 4217 currency code (e.g., "USD", "BRL", "EUR")
    - currency_name: Currency name (e.g., "US Dollar", "Brazilian Real")
    """
    try:
        return service.add_currencies(country_id, currencies or [])
    except RecordNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.message)
    except Exception as e:
        logger.error(f"Failed to add currencies: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/countries/{country_id}/timezones",
    response_model=CountryDetailResponse,
    status_code=201,
    summary="Add timezones to country",
    responses={
        201: {"description": "Timezones added successfully"},
        404: {"description": "Country not found"},
        422: {"description": "Validation error"},
    },
)
def add_timezones(
    country_id: int = Path(..., gt=0),
    timezones: Optional[List[TimezoneCreate]] = None,
    service: CountryService = Depends(get_country_service),
) -> CountryDetailResponse:
    """Add timezones to a country.

    Request body should contain a list of timezone objects with:
    - timezone_name: IANA timezone name (e.g., "America/Sao_Paulo", "Europe/London")
    """
    try:
        return service.add_timezones(country_id, timezones or [])
    except RecordNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.message)
    except Exception as e:
        logger.error(f"Failed to add timezones: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# BATCH OPERATIONS
# ============================================================================


_INGEST_STATUS_TO_SYNC_STATUS = {
    "success": "success",
    "partial_failure": "partial",
    "failure": "failed",
}


@router.post(
    "/sync",
    response_model=SyncLogResponse,
    summary="Trigger data synchronization",
    responses={
        200: {"description": "Sync operation initiated"},
        500: {"description": "Sync operation failed"},
    },
)
def trigger_sync(
    service: CountryService = Depends(get_country_service),
) -> SyncLogResponse:
    """Trigger synchronization from the REST Countries API.

    Runs the same pipeline as `python -m app.scripts.ingest` (fetch ->
    normalize -> persist), reusing this request's database session:
    1. Fetches countries from REST Countries API
    2. Normalizes and validates data
    3. Performs batch upsert (insert new, update existing)

    Note: this runs synchronously in the request; for very large syncs a
    background task/queue would be preferable, but the REST Countries
    dataset (~250 countries) completes in a few seconds.
    """
    sync_id = f"sync_{uuid.uuid4().hex[:12]}"
    try:
        logger.info(f"Sync operation triggered manually: {sync_id}")
        report = ingest_countries(session=service.session)

        return SyncLogResponse(
            sync_id=sync_id,
            status=_INGEST_STATUS_TO_SYNC_STATUS[report.status],
            timestamp=datetime.now(timezone.utc),
            countries_inserted=report.inserted,
            countries_updated=report.updated,
            countries_skipped=(
                report.failed
                + len(report.normalization_errors)
                + len(report.transformation_errors)
            ),
            message=report.message,
        )
    except Exception as e:
        logger.error(f"Sync operation {sync_id} failed: {e}")
        raise HTTPException(status_code=500, detail="Sync operation failed")


# ============================================================================
# STATISTICS & ANALYTICS
# ============================================================================


@router.get(
    "/statistics",
    response_model=GlobalStatistics,
    summary="Get global statistics",
    responses={
        200: {
            "description": "Global statistics with regional breakdown",
            "content": {
                "application/json": {
                    "example": {
                        "total_countries": 250,
                        "total_population": 8000000000,
                        "total_area": 510000000.0,
                        "average_population": 32000000.0,
                        "average_area": 2040000.0,
                        "regions": [
                            {
                                "region": "Americas",
                                "total_countries": 35,
                                "total_population": 1023456789,
                                "total_area": 42165000.0,
                            }
                        ],
                    }
                }
            },
        },
    },
)
def get_statistics(
    service: CountryService = Depends(get_country_service),
) -> GlobalStatistics:
    """Get global statistics about all countries.

    Includes:
    - Total countries
    - Total population
    - Total area
    - Average population and area
    - Regional breakdown with aggregations
    """
    try:
        return service.get_global_statistics()
    except Exception as e:
        logger.error(f"Failed to fetch statistics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/regions",
    response_model=List[RegionStatistics],
    summary="Get regional breakdown",
    responses={
        200: {
            "description": "Statistics by region",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "region": "Americas",
                            "total_countries": 35,
                            "total_population": 1023456789,
                            "total_area": 42165000.0,
                        },
                        {
                            "region": "Europe",
                            "total_countries": 50,
                            "total_population": 750000000,
                            "total_area": 10500000.0,
                        },
                    ]
                }
            },
        },
    },
)
def get_regions(
    service: CountryService = Depends(get_country_service),
) -> List[RegionStatistics]:
    """Get statistics breakdown by region.

    Returns: Total countries, population, and area per region.
    """
    try:
        return service.get_regional_breakdown()
    except Exception as e:
        logger.error(f"Failed to fetch regions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/data-gaps",
    summary="Identify data quality issues",
    responses={
        200: {
            "description": "Countries with data quality issues",
            "content": {
                "application/json": {
                    "example": {
                        "CRITICAL": [
                            {
                                "country_id": 5,
                                "name": "Example Country",
                                "issues": ["Missing ISO code"],
                            }
                        ],
                        "HIGH": [],
                        "MEDIUM": [
                            {
                                "country_id": 10,
                                "name": "Another Country",
                                "issues": ["Missing area", "Missing timezone"],
                            }
                        ],
                        "LOW": [
                            {
                                "country_id": 1,
                                "name": "Brazil",
                                "issues": [],
                            }
                        ],
                    }
                }
            },
        },
    },
)
def analyze_data_gaps(
    service: CountryService = Depends(get_country_service),
) -> dict[str, Any]:
    """Identify countries with data quality issues.

    Returns: Countries prioritized by quality assessment:
    - CRITICAL: Invalid or incomplete required data
    - HIGH: Missing important fields
    - MEDIUM: Partial data
    - LOW: Complete data

    Useful for data cleanup and prioritization.
    """
    try:
        return service.identify_data_gaps()
    except Exception as e:
        logger.error(f"Failed to analyze data gaps: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/countries/{country_id}/validate",
    summary="Validate country data quality",
    responses={
        200: {"description": "Data quality validation report"},
        404: {"description": "Country not found"},
    },
)
def validate_country(
    country_id: int = Path(..., gt=0, description="Country ID"),
    service: CountryService = Depends(get_country_service),
) -> dict[str, Any]:
    """Validate data integrity and quality of a country.

    Returns:
    - Quality score (0-100)
    - Quality level (COMPLETE, PARTIAL, INCOMPLETE, INVALID)
    - Priority (CRITICAL, HIGH, MEDIUM, LOW)
    - Missing fields
    - Relationship counts
    """
    try:
        return service.validate_country_integrity(country_id)
    except RecordNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        logger.error(f"Failed to validate country: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# HEALTH CHECK
# ============================================================================


@router.get(
    "/health",
    summary="Health check endpoint",
    responses={
        200: {"description": "Service is healthy"},
    },
)
def health_check() -> HealthCheckResponse:
    """Health check endpoint for monitoring and orchestrators.

    Returns: Status, version, and timestamp.
    """
    return HealthCheckResponse(
        status="ok",
        version="1.0.0",
        timestamp=datetime.now(timezone.utc),
    )
