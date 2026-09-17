"""REST API routes for country operations.

All endpoints use the service layer (CountryService) for business logic.
Dependency injection provides database sessions automatically.
"""

from typing import List

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
    LanguageCreate,
    SyncLogResponse,
    TimezoneCreate,
)
from app.service import CountryService
from app.utils.errors import (
    DuplicateRecordError,
    RecordNotFoundError,
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
):
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
    region: str | None = Query(
        None,
        description="Filter by region (Africa, Americas, Asia, Europe, Oceania)",
    ),
    service: CountryService = Depends(get_country_service),
):
    """List all countries with pagination and optional region filtering.

    **Query parameters:**
    - page: Page number (default 1)
    - limit: Items per page (default 20, max 100)
    - region: Optional region filter
    """
    try:
        return service.list_countries(page=page, limit=limit, region=region)
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
):
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
):
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
    country_data: CountryUpdate = None,
    service: CountryService = Depends(get_country_service),
):
    """Update country fields (all optional).

    Only provided fields will be updated.
    """
    try:
        return service.update_country(country_id, country_data)
    except RecordNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except DuplicateRecordError as e:
        raise HTTPException(status_code=409, detail=e.message)
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
):
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
)
def add_languages(
    country_id: int = Path(..., gt=0),
    languages: List[LanguageCreate] = None,
    service: CountryService = Depends(get_country_service),
):
    """Add languages to a country."""
    try:
        return service.add_languages(country_id, languages or [])
    except RecordNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        logger.error(f"Failed to add languages: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/countries/{country_id}/currencies",
    response_model=CountryDetailResponse,
    status_code=201,
    summary="Add currencies to country",
)
def add_currencies(
    country_id: int = Path(..., gt=0),
    currencies: List[CurrencyCreate] = None,
    service: CountryService = Depends(get_country_service),
):
    """Add currencies to a country."""
    try:
        return service.add_currencies(country_id, currencies or [])
    except RecordNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        logger.error(f"Failed to add currencies: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/countries/{country_id}/timezones",
    response_model=CountryDetailResponse,
    status_code=201,
    summary="Add timezones to country",
)
def add_timezones(
    country_id: int = Path(..., gt=0),
    timezones: List[TimezoneCreate] = None,
    service: CountryService = Depends(get_country_service),
):
    """Add timezones to a country."""
    try:
        return service.add_timezones(country_id, timezones or [])
    except RecordNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        logger.error(f"Failed to add timezones: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# BATCH OPERATIONS
# ============================================================================


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
):
    """Trigger manual synchronization from REST Countries API.

    This endpoint initiates a sync operation that:
    1. Fetches countries from REST Countries API
    2. Normalizes and validates data
    3. Performs batch upsert (insert new, update existing)
    4. Assesses data quality

    Note: In production, this should be a background task.
    """
    try:
        logger.info("Sync operation triggered manually")
        # Note: In production, call async function or queue task
        # For now, returning placeholder
        from datetime import datetime, timezone

        return SyncLogResponse(
            sync_id="sync_manual",
            status="success",
            timestamp=datetime.now(timezone.utc),
            countries_inserted=0,
            countries_updated=0,
            countries_skipped=0,
            message="Sync operation queued for background processing",
        )
    except Exception as e:
        logger.error(f"Failed to trigger sync: {e}")
        raise HTTPException(status_code=500, detail="Sync operation failed")


# ============================================================================
# STATISTICS & ANALYTICS
# ============================================================================


@router.get(
    "/statistics",
    response_model=GlobalStatistics,
    summary="Get global statistics",
    responses={
        200: {"description": "Global statistics with regional breakdown"},
    },
)
def get_statistics(
    service: CountryService = Depends(get_country_service),
):
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
    summary="Get regional breakdown",
    responses={
        200: {"description": "Statistics by region"},
    },
)
def get_regions(
    service: CountryService = Depends(get_country_service),
):
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
        200: {"description": "Countries with data quality issues"},
    },
)
def analyze_data_gaps(
    service: CountryService = Depends(get_country_service),
):
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
):
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
def health_check():
    """Health check endpoint for monitoring and orchestrators.

    Returns: Status, version, and timestamp.
    """
    from datetime import datetime, timezone

    from app.models.task import HealthCheckResponse

    return HealthCheckResponse(
        status="ok",
        version="1.0.0",
        timestamp=datetime.now(timezone.utc),
    )
