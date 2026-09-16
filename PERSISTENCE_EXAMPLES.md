# Exemplos Práticos - Camada de Persistência
## PG genIA MVP-01: REST Countries Dashboard

---

## 1. INICIALIZAÇÃO DA APLICAÇÃO

### 1.1 Setup no `app/main.py`

```python
"""Main FastAPI application with database initialization."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy.orm import Session

from app.database import init_db, dispose_db, get_db_session
from app.utils.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown."""
    # Startup
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("Closing database connections...")
    dispose_db()
    logger.info("Database connections closed")


# Create FastAPI instance
app = FastAPI(
    title="REST Countries API",
    description="API para gestão de dados de países",
    version="1.0.0",
    lifespan=lifespan,
)


# Health check endpoint
from app.models.task import HealthCheckResponse
from datetime import datetime, timezone

@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint with database status."""
    return HealthCheckResponse(
        status="ok",
        version="1.0.0",
        timestamp=datetime.now(timezone.utc)
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## 2. CRIAR PAÍS (CREATE)

### 2.1 Endpoint POST

```python
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db_session, CountryRepository
from app.database.schemas import CountryCreate, CountryResponse
from app.utils.errors import DuplicateRecordError

app = FastAPI()


@app.post("/api/v1/countries", response_model=CountryResponse, status_code=201)
def create_country(
    country_data: CountryCreate,
    session: Session = Depends(get_db_session)
):
    """Create a new country.
    
    Args:
        country_data: Country data from request body
        session: Database session (injected)
    
    Returns:
        Created country with ID and timestamps
    
    Raises:
        409: Country already exists (duplicate ISO code or name)
        422: Validation error (invalid region, etc)
    """
    repo = CountryRepository(session)
    
    try:
        country = repo.create(country_data)
        return CountryResponse.model_validate(country)
    except DuplicateRecordError as e:
        logger.warning(f"Duplicate country: {e.message}")
        raise HTTPException(
            status_code=409,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Failed to create country: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


# Example request:
# POST /api/v1/countries
# {
#     "name_common": "Brazil",
#     "name_official": "Federative Republic of Brazil",
#     "iso_code_2": "BR",
#     "iso_code_3": "BRA",
#     "region": "Americas",
#     "subregion": "South America",
#     "population": 215000000,
#     "area": 8514876.5,
#     "latitude": -14.235,
#     "longitude": -51.9253
# }
```

---

## 3. LISTAR PAÍSES (READ)

### 3.1 Get All com Paginação

```python
from fastapi import Query
from app.database.schemas import CountryListResponse

@app.get("/api/v1/countries", response_model=CountryListResponse)
def list_countries(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    region: str | None = Query(None),
    session: Session = Depends(get_db_session)
):
    """List countries with pagination and optional filtering.
    
    Args:
        page: Page number (1-indexed)
        limit: Items per page (1-100)
        region: Optional region filter (Africa, Americas, Asia, Europe, Oceania)
        session: Database session (injected)
    
    Returns:
        Paginated list response with metadata
    
    Example:
        GET /api/v1/countries?page=1&limit=20&region=Europe
    """
    repo = CountryRepository(session)
    return repo.get_paginated(page=page, limit=limit, region=region)


# Example response:
# {
#     "items": [
#         {
#             "id": 1,
#             "name_common": "Brazil",
#             "name_official": "Federative Republic of Brazil",
#             "iso_code_2": "BR",
#             "iso_code_3": "BRA",
#             "region": "Americas",
#             "population": 215000000,
#             "area": 8514876.5,
#             "created_at": "2026-09-16T10:30:00Z",
#             "updated_at": "2026-09-16T10:30:00Z"
#         },
#         ...
#     ],
#     "total": 250,
#     "page": 1,
#     "limit": 20,
#     "pages": 13
# }
```

### 3.2 Get by ID

```python
from app.database.schemas import CountryDetailResponse
from app.utils.errors import RecordNotFoundError

@app.get("/api/v1/countries/{country_id}", response_model=CountryDetailResponse)
def get_country_details(
    country_id: int,
    session: Session = Depends(get_db_session)
):
    """Get detailed information about a country including relationships.
    
    Args:
        country_id: Country ID
        session: Database session (injected)
    
    Returns:
        Country with languages, currencies, timezones
    
    Raises:
        404: Country not found
    """
    repo = CountryRepository(session)
    country = repo.get_by_id(country_id)
    
    if not country:
        raise HTTPException(
            status_code=404,
            detail=f"Country with id={country_id} not found"
        )
    
    return CountryDetailResponse.model_validate(country)


# Example response (com relacionamentos):
# {
#     "id": 1,
#     "name_common": "Brazil",
#     "...": "...",
#     "languages": [
#         {"id": 1, "language_code": "pt", "language_name": "Portuguese"}
#     ],
#     "currencies": [
#         {"id": 1, "currency_code": "BRL", "currency_name": "Brazilian Real"}
#     ],
#     "timezones": [
#         {"id": 1, "timezone_name": "America/Sao_Paulo"},
#         {"id": 2, "timezone_name": "America/Bahia"}
#     ]
# }
```

### 3.3 Get by ISO Code

```python
@app.get("/api/v1/countries/iso/{iso_code}", response_model=CountryDetailResponse)
def get_country_by_iso(
    iso_code: str,
    session: Session = Depends(get_db_session)
):
    """Get country by ISO 2 or 3-letter code.
    
    Args:
        iso_code: ISO2 (BR) or ISO3 (BRA) code
        session: Database session (injected)
    
    Returns:
        Country details
    
    Raises:
        404: Country not found
    """
    repo = CountryRepository(session)
    
    # Try ISO2 first, then ISO3
    country = repo.get_by_iso2(iso_code)
    if not country:
        country = repo.get_by_iso3(iso_code)
    
    if not country:
        raise HTTPException(
            status_code=404,
            detail=f"Country with iso_code={iso_code} not found"
        )
    
    return CountryDetailResponse.model_validate(country)
```

---

## 4. ATUALIZAR PAÍS (UPDATE)

### 4.1 Endpoint PUT

```python
from app.database.schemas import CountryUpdate

@app.put("/api/v1/countries/{country_id}", response_model=CountryResponse)
def update_country(
    country_id: int,
    country_data: CountryUpdate,
    session: Session = Depends(get_db_session)
):
    """Update an existing country.
    
    Args:
        country_id: Country ID
        country_data: Fields to update (all optional)
        session: Database session (injected)
    
    Returns:
        Updated country
    
    Raises:
        404: Country not found
        409: Duplicate (if trying to set name/iso that already exists)
    """
    repo = CountryRepository(session)
    
    try:
        country = repo.update(country_id, country_data)
        return CountryResponse.model_validate(country)
    except RecordNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except DuplicateRecordError as e:
        raise HTTPException(status_code=409, detail=e.message)
    except Exception as e:
        logger.error(f"Failed to update country: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Example request (partial update):
# PUT /api/v1/countries/1
# {
#     "population": 216000000,
#     "area": 8515000.0
# }
# (other fields não precisam ser inclusos)
```

---

## 5. DELETAR PAÍS (DELETE)

### 5.1 Endpoint DELETE

```python
@app.delete("/api/v1/countries/{country_id}", status_code=204)
def delete_country(
    country_id: int,
    session: Session = Depends(get_db_session)
):
    """Delete a country and all its relationships (cascade).
    
    Args:
        country_id: Country ID
        session: Database session (injected)
    
    Raises:
        404: Country not found
    
    Note:
        Deleting a country also deletes:
        - All languages (country_languages rows)
        - All currencies (country_currencies rows)
        - All timezones (country_timezones rows)
    """
    repo = CountryRepository(session)
    
    if not repo.delete(country_id):
        raise HTTPException(
            status_code=404,
            detail=f"Country with id={country_id} not found"
        )
    
    logger.info(f"Country deleted: id={country_id}")
    # No response body (204 No Content)
```

---

## 6. INGESTÃO EM LOTE (BATCH UPSERT)

### 6.1 Script de Ingestão Manual

```python
# app/scripts/ingest.py

import asyncio
import sys
from datetime import datetime

from app.database import SessionLocal, CountryRepository
from app.models.task import CountryCreate
from app.utils.logger import get_logger
from app.utils.errors import BatchProcessError

logger = get_logger(__name__)


async def fetch_from_rest_countries_api():
    """Fetch countries from external API."""
    import httpx
    
    async with httpx.AsyncClient() as client:
        response = await client.get("https://restcountries.com/v3.1/all", timeout=30.0)
        response.raise_for_status()
        return response.json()


def normalize_countries(raw_data: list[dict]) -> list[CountryCreate]:
    """Normalize API data to CountryCreate schemas.
    
    Args:
        raw_data: Raw JSON from REST Countries API
    
    Returns:
        List of validated CountryCreate objects
    """
    normalized = []
    
    for country_data in raw_data:
        try:
            # Extract relevant fields from raw API response
            normalized_data = CountryCreate(
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
            )
            normalized.append(normalized_data)
        except Exception as e:
            logger.warning(
                f"Failed to normalize country {country_data.get('name', {}).get('common')}: {e}"
            )
            continue
    
    return normalized


async def ingest_countries():
    """Main ingestion workflow."""
    logger.info("Starting country ingestion...")
    start_time = datetime.now()
    
    try:
        # 1. Fetch from API
        logger.info("Fetching countries from REST Countries API...")
        raw_countries = await fetch_from_rest_countries_api()
        logger.info(f"Fetched {len(raw_countries)} countries from API")
        
        # 2. Normalize
        logger.info("Normalizing country data...")
        countries_data = normalize_countries(raw_countries)
        logger.info(f"Normalized {len(countries_data)} countries")
        
        # 3. Batch upsert
        logger.info("Upserting to database...")
        session = SessionLocal()
        repo = CountryRepository(session)
        
        try:
            total, inserted, updated = repo.upsert_batch(countries_data)
            logger.info(
                f"Upsert completed: {total} processed, "
                f"{inserted} inserted, {updated} updated"
            )
        finally:
            session.close()
        
        # Summary
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(
            f"Ingestion completed in {elapsed:.2f}s\n"
            f"  Total: {total}\n"
            f"  Inserted: {inserted}\n"
            f"  Updated: {updated}"
        )
        
        return {
            "status": "success",
            "total": total,
            "inserted": inserted,
            "updated": updated,
            "elapsed_seconds": elapsed,
        }
        
    except BatchProcessError as e:
        logger.error(
            f"Batch ingestion failed: {e.successful}/{e.total} succeeded\n"
            f"  Errors: {e.errors}"
        )
        sys.exit(1)
    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    # Run async ingestion
    result = asyncio.run(ingest_countries())
    print(result)
```

### 6.2 Usar via FastAPI Endpoint

```python
from fastapi import BackgroundTasks
from app.models.task import SyncLogResponse

@app.post("/api/v1/sync", response_model=SyncLogResponse)
async def trigger_sync(
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_db_session)
):
    """Trigger manual data synchronization.
    
    Args:
        background_tasks: FastAPI background task queue
        session: Database session
    
    Returns:
        Sync operation ID
    
    Note:
        Ingestion runs in background task, não bloqueia resposta
    """
    sync_id = f"sync_{datetime.now().timestamp()}"
    
    async def sync_task():
        from app.scripts.ingest import ingest_countries
        try:
            result = await ingest_countries()
            logger.info(f"Sync {sync_id} completed: {result}")
        except Exception as e:
            logger.error(f"Sync {sync_id} failed: {e}")
    
    background_tasks.add_task(sync_task)
    
    return SyncLogResponse(
        sync_id=sync_id,
        status="pending",
        timestamp=datetime.now(timezone.utc),
        countries_inserted=0,
        countries_updated=0,
        countries_skipped=0,
        message="Sync started in background"
    )
```

---

## 7. ESTATÍSTICAS (AGGREGATIONS)

### 7.1 Endpoints de Estatísticas

```python
from app.database import StatisticsRepository
from app.models.task import GlobalStatistics

@app.get("/api/v1/statistics", response_model=GlobalStatistics)
def get_statistics(session: Session = Depends(get_db_session)):
    """Get global statistics about all countries.
    
    Returns:
        Total countries, population, area, averages, regional breakdown
    """
    stats_repo = StatisticsRepository(session)
    
    global_stats = stats_repo.get_global_stats()
    regional_stats = stats_repo.get_regional_stats()
    
    return GlobalStatistics(
        **global_stats,
        regions=regional_stats
    )


# Example response:
# {
#     "total_countries": 250,
#     "total_population": 8000000000,
#     "total_area": 510100000,
#     "average_population": 32000000,
#     "average_area": 2040400,
#     "regions": [
#         {
#             "region": "Africa",
#             "total_countries": 54,
#             "total_population": 1400000000,
#             "total_area": 30370000
#         },
#         ...
#     ]
# }


@app.get("/api/v1/regions")
def get_regional_stats(session: Session = Depends(get_db_session)):
    """Get statistics by region.
    
    Returns:
        Breakdown of countries by region with aggregations
    """
    stats_repo = StatisticsRepository(session)
    return stats_repo.get_regional_stats()
```

---

## 8. TRATAMENTO DE ERROS

### 8.1 Exception Handlers

```python
from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.utils.errors import (
    DuplicateRecordError,
    RecordNotFoundError,
    BatchProcessError,
    ValidationError,
)
from app.models.task import ErrorResponse


@app.exception_handler(DuplicateRecordError)
async def handle_duplicate_error(request: Request, exc: DuplicateRecordError):
    logger.warning(f"Duplicate record: {exc.message}")
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=ErrorResponse(
            detail=exc.message,
            error_code=exc.error_code
        ).model_dump()
    )


@app.exception_handler(RecordNotFoundError)
async def handle_not_found_error(request: Request, exc: RecordNotFoundError):
    logger.warning(f"Record not found: {exc.message}")
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=ErrorResponse(
            detail=exc.message,
            error_code=exc.error_code
        ).model_dump()
    )


@app.exception_handler(BatchProcessError)
async def handle_batch_error(request: Request, exc: BatchProcessError):
    logger.error(f"Batch operation failed: {exc.message}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "detail": exc.message,
            "error_code": exc.error_code,
            "total": exc.total,
            "successful": exc.successful,
            "failed": exc.failed,
            "errors": exc.errors[:10]  # Limit error details
        }
    )
```

---

## 9. TESTES UNITÁRIOS

### 9.1 Fixture de Teste

```python
# tests/conftest.py

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.models import Base
from app.database.repository import CountryRepository


@pytest.fixture(scope="function")
def test_db():
    """Create in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()
    engine.dispose()


@pytest.fixture
def country_repo(test_db):
    """Create repository with test database."""
    return CountryRepository(test_db)
```

### 9.2 Testes do Repository

```python
# tests/test_repository.py

from app.models.task import CountryCreate
from app.utils.errors import DuplicateRecordError, RecordNotFoundError


def test_create_country(country_repo):
    """Test creating a new country."""
    data = CountryCreate(
        name_common="Test Country",
        name_official="Test Country Official",
        iso_code_2="TC",
        iso_code_3="TST",
        region="Europe",
        population=1000000,
        area=50000.0,
        latitude=45.0,
        longitude=15.0,
    )
    
    country = country_repo.create(data)
    
    assert country.id is not None
    assert country.name_common == "Test Country"
    assert country.iso_code_2 == "TC"


def test_create_duplicate_country(country_repo):
    """Test that duplicate countries raise error."""
    data = CountryCreate(
        name_common="Test",
        name_official="Test",
        iso_code_2="TS",
        iso_code_3="TST",
        region="Europe",
        population=1000,
        area=1000.0,
        latitude=0.0,
        longitude=0.0,
    )
    
    country_repo.create(data)
    
    with pytest.raises(DuplicateRecordError):
        country_repo.create(data)


def test_get_by_id(country_repo):
    """Test retrieving country by ID."""
    data = CountryCreate(
        name_common="Test",
        name_official="Test",
        iso_code_2="TS",
        iso_code_3="TST",
        region="Europe",
        population=1000,
        area=1000.0,
        latitude=0.0,
        longitude=0.0,
    )
    
    created = country_repo.create(data)
    retrieved = country_repo.get_by_id(created.id)
    
    assert retrieved is not None
    assert retrieved.id == created.id


def test_update_country(country_repo):
    """Test updating a country."""
    data = CountryCreate(
        name_common="Original",
        name_official="Original",
        iso_code_2="OR",
        iso_code_3="ORI",
        region="Europe",
        population=1000000,
        area=50000.0,
        latitude=0.0,
        longitude=0.0,
    )
    
    created = country_repo.create(data)
    
    from app.models.task import CountryUpdate
    update_data = CountryUpdate(population=2000000)
    updated = country_repo.update(created.id, update_data)
    
    assert updated.population == 2000000


def test_upsert_batch(country_repo):
    """Test batch upsert operation."""
    countries = [
        CountryCreate(
            name_common=f"Country {i}",
            name_official=f"Country {i} Official",
            iso_code_2=f"C{i}",
            iso_code_3=f"COU{i}",
            region="Europe",
            population=1000000 + i,
            area=50000.0,
            latitude=0.0,
            longitude=0.0,
        )
        for i in range(5)
    ]
    
    total, inserted, updated = country_repo.upsert_batch(countries)
    
    assert total == 5
    assert inserted == 5
    assert updated == 0
```

---

## 10. INTEGRAÇÃO COM STREAMLIT (Dashboard)

### 10.1 Carregar dados para dashboard

```python
# app/streamlit/app.py

import streamlit as st
import pandas as pd
import requests

# Configure page
st.set_page_config(
    page_title="REST Countries Dashboard",
    page_icon="🌍",
    layout="wide"
)

# API base URL
API_URL = "http://localhost:8000/api/v1"


@st.cache_data(ttl=3600)  # Cache 1 hour
def load_countries(region: str | None = None, page: int = 1):
    """Load countries from API."""
    params = {"page": page, "limit": 100}
    if region and region != "All":
        params["region"] = region
    
    response = requests.get(f"{API_URL}/countries", params=params)
    response.raise_for_status()
    return response.json()


@st.cache_data(ttl=3600)
def load_statistics():
    """Load global statistics."""
    response = requests.get(f"{API_URL}/statistics")
    response.raise_for_status()
    return response.json()


# Streamlit app
st.title("🌍 REST Countries Dashboard")

# Sidebar
st.sidebar.header("Filters")
region = st.sidebar.selectbox(
    "Select Region",
    ["All", "Africa", "Americas", "Asia", "Europe", "Oceania"]
)

# Load data
try:
    data = load_countries(region if region != "All" else None)
    stats = load_statistics()
    
    # Display KPIs
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Countries", stats["total_countries"])
    
    with col2:
        st.metric("Total Population", f"{stats['total_population']:,}")
    
    with col3:
        st.metric("Total Area (km²)", f"{stats['total_area']:,.0f}")
    
    with col4:
        st.metric("Average Population", f"{stats['average_population']:,.0f}")
    
    # Display countries table
    st.header("Countries")
    df = pd.DataFrame(data["items"])
    st.dataframe(df, use_container_width=True)
    
except Exception as e:
    st.error(f"Failed to load data: {e}")
```

---

## Conclusão

Estes exemplos cobrem todos os CRUD operations, batch processing, error handling, testes e integração com FastAPI/Streamlit.

Para mais detalhes, consulte `documentacoes/PERSISTENCE.md`.
