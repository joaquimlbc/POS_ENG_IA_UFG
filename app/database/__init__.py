"""Database module for REST Countries API application.

Provides ORM models, connection management, repository patterns,
and schemas for data persistence and API contracts.
"""

from app.database.connection import (
    SessionLocal,
    dispose_db,
    get_db_session,
    get_engine,
    init_db,
)
from app.database.models import Country, Currency, Language, Timezone
from app.database.repository import CountryRepository, StatisticsRepository
from app.database.schemas import (
    CountryCreate,
    CountryDetailResponse,
    CountryListResponse,
    CountryResponse,
    CountryUpdate,
    CurrencyCreate,
    CurrencyResponse,
    ErrorResponse,
    GlobalStatistics,
    HealthCheckResponse,
    LanguageCreate,
    LanguageResponse,
    RegionStatistics,
    SyncLogResponse,
    TimezoneCreate,
    TimezoneResponse,
)

__all__ = [
    # Connection
    "SessionLocal",
    "init_db",
    "get_db_session",
    "get_engine",
    "dispose_db",
    # Models
    "Country",
    "Language",
    "Currency",
    "Timezone",
    # Repository
    "CountryRepository",
    "StatisticsRepository",
    # Schemas
    "LanguageCreate",
    "LanguageResponse",
    "CurrencyCreate",
    "CurrencyResponse",
    "TimezoneCreate",
    "TimezoneResponse",
    "CountryCreate",
    "CountryUpdate",
    "CountryResponse",
    "CountryDetailResponse",
    "CountryListResponse",
    "RegionStatistics",
    "GlobalStatistics",
    "HealthCheckResponse",
    "ErrorResponse",
    "SyncLogResponse",
]
