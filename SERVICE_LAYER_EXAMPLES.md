# Exemplos de Uso - Service Layer
## PG genIA MVP-01: REST Countries Dashboard

---

## 1. INTEGRAÇÃO COM FASTAPI

### 1.1 Estrutura de Endpoints com Service Layer

```python
# app/main.py ou app/api/endpoints.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db_session
from app.service import CountryService
from app.models.task import (
    CountryCreate,
    CountryDetailResponse,
    CountryListResponse,
    CountryResponse,
    CountryUpdate,
)
from app.utils.errors import (
    DuplicateRecordError,
    RecordNotFoundError,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1", tags=["countries"])


def get_country_service(session: Session = Depends(get_db_session)) -> CountryService:
    """Dependency to provide service layer."""
    return CountryService(session)


# ============================================================================
# CREATE
# ============================================================================

@router.post("/countries", response_model=CountryResponse, status_code=201)
def create_country(
    country_data: CountryCreate,
    service: CountryService = Depends(get_country_service),
):
    """Create a new country.
    
    Args:
        country_data: Country creation data
        service: Injected service layer
    
    Returns:
        Created country
    
    Raises:
        409: Country already exists (duplicate ISO codes)
        422: Validation error (invalid region, etc)
    """
    try:
        return service.create_country(country_data)
    except DuplicateRecordError as e:
        logger.warning(f"Duplicate country creation attempt: {e.message}")
        raise HTTPException(status_code=409, detail=e.message)
    except Exception as e:
        logger.error(f"Failed to create country: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# READ
# ============================================================================

@router.get("/countries", response_model=CountryListResponse)
def list_countries(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    region: str | None = Query(None),
    service: CountryService = Depends(get_country_service),
):
    """List countries with pagination and filtering.
    
    Query Parameters:
        page: Page number (1-indexed)
        limit: Items per page (max 100)
        region: Optional region filter
    
    Returns:
        Paginated list of countries
    """
    try:
        return service.list_countries(page=page, limit=limit, region=region)
    except Exception as e:
        logger.error(f"Failed to list countries: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/countries/{country_id}", response_model=CountryDetailResponse)
def get_country(
    country_id: int,
    service: CountryService = Depends(get_country_service),
):
    """Get country details by ID.
    
    Args:
        country_id: Country ID
        service: Injected service layer
    
    Returns:
        Country details with relationships
    
    Raises:
        404: Country not found
    """
    try:
        return service.get_country(country_id)
    except RecordNotFoundError as e:
        logger.warning(f"Country not found: {e.message}")
        raise HTTPException(status_code=404, detail=e.message)


@router.get("/countries/iso/{iso_code}", response_model=CountryDetailResponse)
def get_country_by_iso(
    iso_code: str,
    service: CountryService = Depends(get_country_service),
):
    """Get country by ISO code (2 or 3-letter).
    
    Args:
        iso_code: ISO2 (BR) or ISO3 (BRA) code
        service: Injected service layer
    
    Returns:
        Country details
    
    Raises:
        404: Country not found
    """
    try:
        return service.get_country_by_iso(iso_code.upper())
    except RecordNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)


# ============================================================================
# UPDATE
# ============================================================================

@router.put("/countries/{country_id}", response_model=CountryResponse)
def update_country(
    country_id: int,
    country_data: CountryUpdate,
    service: CountryService = Depends(get_country_service),
):
    """Update a country.
    
    Args:
        country_id: Country ID
        country_data: Fields to update (all optional)
        service: Injected service layer
    
    Returns:
        Updated country
    
    Raises:
        404: Country not found
        409: Duplicate (if trying to set field that already exists elsewhere)
    """
    try:
        return service.update_country(country_id, country_data)
    except RecordNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except DuplicateRecordError as e:
        raise HTTPException(status_code=409, detail=e.message)


# ============================================================================
# DELETE
# ============================================================================

@router.delete("/countries/{country_id}", status_code=204)
def delete_country(
    country_id: int,
    service: CountryService = Depends(get_country_service),
):
    """Delete a country (cascade to relationships).
    
    Args:
        country_id: Country ID
        service: Injected service layer
    
    Raises:
        404: Country not found
    """
    if not service.delete_country(country_id):
        raise HTTPException(status_code=404, detail="Country not found")


# ============================================================================
# BATCH OPERATIONS
# ============================================================================

@router.post("/sync")
def trigger_sync(
    service: CountryService = Depends(get_country_service),
):
    """Trigger manual data synchronization from REST Countries API.
    
    This would be called by a background task or scheduler.
    
    Returns:
        Sync operation result with statistics
    """
    # This would typically call an async function that:
    # 1. Fetches from REST Countries API
    # 2. Normalizes the data
    # 3. Calls service.sync_countries_batch()
    
    from app.scripts.ingest import ingest_countries
    
    # Note: In production, this should be a background task
    # For now, running synchronously for simplicity
    
    try:
        # Fetch and normalize countries
        raw_countries = ...  # Fetch from API
        countries_data = ...  # Normalize
        
        result = service.sync_countries_batch(countries_data)
        return service.get_sync_result_response(result)
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        raise HTTPException(status_code=500, detail="Sync operation failed")


# ============================================================================
# STATISTICS
# ============================================================================

@router.get("/statistics")
def get_statistics(
    service: CountryService = Depends(get_country_service),
):
    """Get global statistics about all countries.
    
    Returns:
        Global statistics with regional breakdown
    """
    try:
        return service.get_global_statistics()
    except Exception as e:
        logger.error(f"Failed to fetch statistics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/regions")
def get_regions(
    service: CountryService = Depends(get_country_service),
):
    """Get regional breakdown.
    
    Returns:
        List of regions with aggregated statistics
    """
    try:
        return service.get_regional_breakdown()
    except Exception as e:
        logger.error(f"Failed to fetch regions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# DATA QUALITY & ANALYSIS
# ============================================================================

@router.get("/data-gaps")
def analyze_data_gaps(
    service: CountryService = Depends(get_country_service),
):
    """Identify countries with data quality issues.
    
    Returns:
        Report of countries needing data updates, prioritized
    """
    try:
        return service.identify_data_gaps()
    except Exception as e:
        logger.error(f"Failed to analyze data gaps: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/countries/{country_id}/validate")
def validate_country(
    country_id: int,
    service: CountryService = Depends(get_country_service),
):
    """Validate data integrity and quality of a country.
    
    Args:
        country_id: Country ID
    
    Returns:
        Integrity report with quality score
    
    Raises:
        404: Country not found
    """
    try:
        return service.validate_country_integrity(country_id)
    except RecordNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)


# ============================================================================
# RELATIONSHIPS
# ============================================================================

from app.models.task import LanguageCreate, CurrencyCreate, TimezoneCreate

@router.post("/countries/{country_id}/languages")
def add_languages(
    country_id: int,
    languages: List[LanguageCreate],
    service: CountryService = Depends(get_country_service),
):
    """Add languages to a country.
    
    Args:
        country_id: Country ID
        languages: List of languages to add
    
    Returns:
        Updated country with new languages
    """
    try:
        return service.add_languages(country_id, languages)
    except RecordNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.post("/countries/{country_id}/currencies")
def add_currencies(
    country_id: int,
    currencies: List[CurrencyCreate],
    service: CountryService = Depends(get_country_service),
):
    """Add currencies to a country.
    
    Args:
        country_id: Country ID
        currencies: List of currencies to add
    
    Returns:
        Updated country with new currencies
    """
    try:
        return service.add_currencies(country_id, currencies)
    except RecordNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.post("/countries/{country_id}/timezones")
def add_timezones(
    country_id: int,
    timezones: List[TimezoneCreate],
    service: CountryService = Depends(get_country_service),
):
    """Add timezones to a country.
    
    Args:
        country_id: Country ID
        timezones: List of timezones to add
    
    Returns:
        Updated country with new timezones
    """
    try:
        return service.add_timezones(country_id, timezones)
    except RecordNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
```

---

## 2. USANDO SERVICE EM SCRIPTS/CLI

### 2.1 Ingestão Manual

```python
# app/scripts/ingest.py

import asyncio
from datetime import datetime

from app.database import SessionLocal
from app.service import CountryService
from app.models.task import CountryCreate
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def fetch_countries_from_api():
    """Fetch countries from REST Countries API."""
    import httpx
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://restcountries.com/v3.1/all",
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()


def normalize_countries(raw_data: list[dict]) -> list[CountryCreate]:
    """Normalize API data to CountryCreate schemas."""
    normalized = []
    
    for country_data in raw_data:
        try:
            normalized.append(CountryCreate(
                name_common=country_data.get("name", {}).get("common", ""),
                name_official=country_data.get("name", {}).get("official", ""),
                iso_code_2=country_data.get("cca2", ""),
                iso_code_3=country_data.get("cca3", ""),
                region=country_data.get("region", ""),
                subregion=country_data.get("subregion"),
                population=country_data.get("population", 0),
                area=country_data.get("area"),
                latitude=float(country_data.get("latlng", [0, 0])[0]),
                longitude=float(country_data.get("latlng", [0, 0])[1]),
            ))
        except Exception as e:
            logger.warning(f"Failed to normalize country: {e}")
            continue
    
    return normalized


async def main():
    """Main ingestion workflow using service layer."""
    logger.info("Starting country ingestion...")
    start = datetime.now()
    
    # Fetch from API
    logger.info("Fetching countries from REST Countries API...")
    raw_countries = await fetch_countries_from_api()
    logger.info(f"Fetched {len(raw_countries)} countries")
    
    # Normalize
    logger.info("Normalizing country data...")
    countries_data = normalize_countries(raw_countries)
    logger.info(f"Normalized {len(countries_data)} countries")
    
    # Persist using service layer
    logger.info("Persisting to database...")
    session = SessionLocal()
    
    try:
        service = CountryService(session)
        result = service.sync_countries_batch(countries_data)
        
        logger.info(
            f"Ingestion completed:\n"
            f"  Total: {result.total_processed}\n"
            f"  Inserted: {result.inserted}\n"
            f"  Updated: {result.updated}\n"
            f"  Failed: {result.failed}"
        )
        
        # Quality summary
        if result.quality_summary:
            logger.info(
                f"Quality summary:\n"
                f"  Complete: {result.quality_summary.get('quality_distribution', {}).get('complete', 0)}\n"
                f"  Partial: {result.quality_summary.get('quality_distribution', {}).get('partial', 0)}\n"
                f"  Incomplete: {result.quality_summary.get('quality_distribution', {}).get('incomplete', 0)}\n"
                f"  Invalid: {result.quality_summary.get('quality_distribution', {}).get('invalid', 0)}"
            )
        
        elapsed = (datetime.now() - start).total_seconds()
        logger.info(f"Completed in {elapsed:.2f}s")
        
    finally:
        session.close()


if __name__ == "__main__":
    asyncio.run(main())
```

---

## 3. USANDO SERVICE EM TESTES

### 3.1 Teste Unitário com Mocks

```python
# tests/unit/test_country_service.py

import pytest
from unittest.mock import Mock, MagicMock
from sqlalchemy.orm import Session

from app.service import CountryService
from app.models.task import CountryCreate
from app.utils.errors import DuplicateRecordError, RecordNotFoundError


@pytest.fixture
def mock_session():
    """Create mock session."""
    return Mock(spec=Session)


@pytest.fixture
def service(mock_session):
    """Create service with mock dependencies."""
    return CountryService(mock_session)


def test_create_country_success(service):
    """Test successful country creation."""
    # Mock repository
    mock_country = Mock(id=1, name_common="Test")
    service.country_repo.get_by_iso2 = Mock(return_value=None)
    service.country_repo.create = Mock(return_value=mock_country)
    
    # Create country
    data = CountryCreate(
        name_common="Test",
        name_official="Test Official",
        iso_code_2="TS",
        iso_code_3="TST",
        region="Europe",
        population=1000000,
        area=50000.0,
        latitude=45.0,
        longitude=15.0,
    )
    
    result = service.create_country(data)
    
    # Assertions
    assert result.id == 1
    assert result.name_common == "Test"
    service.country_repo.create.assert_called_once()


def test_create_country_duplicate(service):
    """Test duplicate country rejection."""
    # Mock: country already exists
    service.country_repo.get_by_iso2 = Mock(return_value=Mock())
    
    data = CountryCreate(
        name_common="Test",
        name_official="Test Official",
        iso_code_2="TS",
        iso_code_3="TST",
        region="Europe",
        population=1000000,
        area=50000.0,
        latitude=45.0,
        longitude=15.0,
    )
    
    # Should raise DuplicateRecordError
    with pytest.raises(DuplicateRecordError):
        service.create_country(data)


def test_get_country_not_found(service):
    """Test get non-existent country."""
    service.country_repo.get_by_id = Mock(return_value=None)
    
    with pytest.raises(RecordNotFoundError):
        service.get_country(999)


def test_list_countries(service):
    """Test listing countries with pagination."""
    mock_response = Mock(items=[Mock()] * 20, total=100, page=1, limit=20)
    service.country_repo.get_paginated = Mock(return_value=mock_response)
    
    result = service.list_countries(page=1, limit=20)
    
    assert result.page == 1
    assert result.limit == 20
    assert result.total == 100
```

### 3.2 Teste de Integração

```python
# tests/integration/test_country_service_integration.py

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.models import Base
from app.service import CountryService
from app.models.task import CountryCreate


@pytest.fixture(scope="function")
def test_db():
    """Create in-memory test database."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()


@pytest.fixture
def service(test_db):
    """Create service with test database."""
    return CountryService(test_db)


def test_create_and_retrieve_country(service):
    """Test creating and retrieving a country."""
    # Create
    data = CountryCreate(
        name_common="Brazil",
        name_official="Federative Republic of Brazil",
        iso_code_2="BR",
        iso_code_3="BRA",
        region="Americas",
        population=215000000,
        area=8514876.5,
        latitude=-14.235,
        longitude=-51.9253,
    )
    
    response = service.create_country(data)
    assert response.id is not None
    
    # Retrieve
    retrieved = service.get_country(response.id)
    assert retrieved.name_common == "Brazil"
    assert retrieved.iso_code_2 == "BR"


def test_batch_sync(service):
    """Test batch synchronization."""
    countries = [
        CountryCreate(
            name_common=f"Country {i}",
            name_official=f"Country {i} Official",
            iso_code_2=f"C{i:02d}",
            iso_code_3=f"C{i:02d}T",
            region="Europe",
            population=1000000 + i * 100000,
            area=50000.0,
            latitude=45.0,
            longitude=15.0,
        )
        for i in range(10)
    ]
    
    result = service.sync_countries_batch(countries)
    
    assert result.total_processed == 10
    assert result.inserted == 10
    assert result.status == "success"


def test_statistics(service):
    """Test statistics retrieval."""
    # Create some countries
    for i in range(5):
        data = CountryCreate(
            name_common=f"Country {i}",
            name_official=f"Country {i}",
            iso_code_2=f"C{i}",
            iso_code_3=f"C{i}T",
            region="Europe",
            population=1000000,
            area=50000.0,
            latitude=0.0,
            longitude=0.0,
        )
        service.create_country(data)
    
    # Get statistics
    stats = service.get_global_statistics()
    
    assert stats.total_countries == 5
    assert stats.total_population == 5000000
    assert len(stats.regions) > 0
```

---

## 4. PADRÃO DE DEPENDENCY INJECTION

### 4.1 Provendo Service em Endpoints

```python
# Opção 1: Inline dependency
@app.get("/countries")
def list_countries(session: Session = Depends(get_db_session)):
    service = CountryService(session)
    return service.list_countries()


# Opção 2: Service dependency
def get_service(session: Session = Depends(get_db_session)) -> CountryService:
    return CountryService(session)

@app.get("/countries")
def list_countries(service: CountryService = Depends(get_service)):
    return service.list_countries()


# Opção 3: Service factory (recomendado)
def get_country_service(session: Session = Depends(get_db_session)) -> CountryService:
    return CountryService(session)

@app.get("/countries")
def list_countries(service: CountryService = Depends(get_country_service)):
    return service.list_countries()
```

### 4.2 Testando com Mock Service

```python
def test_endpoint_with_mock():
    """Test endpoint with mocked service."""
    from fastapi.testclient import TestClient
    
    app = FastAPI()
    
    # Mock service
    mock_service = Mock(spec=CountryService)
    mock_service.list_countries.return_value = Mock(items=[], total=0)
    
    @app.get("/countries")
    def list_countries(service: CountryService = Depends(lambda: mock_service)):
        return service.list_countries()
    
    client = TestClient(app)
    response = client.get("/countries")
    
    assert response.status_code == 200
```

---

## 5. ERROR HANDLING PATTERN

```python
@app.post("/countries")
def create_country(data: CountryCreate, service: CountryService = Depends(...)):
    """Endpoint with comprehensive error handling."""
    try:
        return service.create_country(data)
    
    # Domain errors (service layer)
    except DuplicateRecordError as e:
        logger.warning(f"Duplicate: {e.message}")
        raise HTTPException(status_code=409, detail=e.message)
    
    except RecordNotFoundError as e:
        logger.warning(f"Not found: {e.message}")
        raise HTTPException(status_code=404, detail=e.message)
    
    except ValidationError as e:
        logger.warning(f"Validation error: {e.message}")
        raise HTTPException(status_code=422, detail=e.message)
    
    # Database errors
    except IntegrityError as e:
        logger.error(f"Database integrity error: {e.message}")
        raise HTTPException(status_code=400, detail="Database constraint violation")
    
    # Unexpected errors
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
```

---

## Conclusão

O Service Layer é a camada de orquestração e lógica de negócio. Todos os CRUD operations, validações de negócio, e decisões devem passar por aqui, nunca diretamente do API para Repository.

**Benefícios:**
- ✅ Separação clara de responsabilidades
- ✅ Reutilização entre endpoints
- ✅ Testabilidade (mock service)
- ✅ Manutenibilidade (mudanças centralizadas)
- ✅ Escalabilidade (adicionar features sem impactar API)
