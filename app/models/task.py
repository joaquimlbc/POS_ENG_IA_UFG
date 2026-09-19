"""Pydantic v2 data models for REST Countries API domain entities.

This module defines the core data models used throughout the application
for validation, serialization, and API contracts.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator


class LanguageBase(BaseModel):
    """Base model for language data."""

    language_code: str = Field(..., min_length=2, max_length=10)
    language_name: str = Field(..., min_length=1, max_length=100)

    model_config = ConfigDict(str_strip_whitespace=True)


class LanguageCreate(LanguageBase):
    """Model for creating language records."""

    pass


class LanguageResponse(LanguageBase):
    """Language response model with database ID."""

    id: int = Field(..., gt=0)

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "language_code": "pt",
                "language_name": "Portuguese",
            }
        },
    )


class CurrencyBase(BaseModel):
    """Base model for currency data."""

    currency_code: str = Field(..., min_length=3, max_length=3)
    currency_name: str = Field(..., min_length=1, max_length=100)

    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator("currency_code")
    @classmethod
    def validate_currency_code(cls, v: str) -> str:
        """Validate currency code format (uppercase ISO 4217)."""
        return v.upper()


class CurrencyCreate(CurrencyBase):
    """Model for creating currency records."""

    pass


class CurrencyResponse(CurrencyBase):
    """Currency response model with database ID."""

    id: int = Field(..., gt=0)

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "currency_code": "BRL",
                "currency_name": "Brazilian Real",
            }
        },
    )


class TimezoneBase(BaseModel):
    """Base model for timezone data."""

    timezone_name: str = Field(..., min_length=1, max_length=100)

    model_config = ConfigDict(str_strip_whitespace=True)


class TimezoneCreate(TimezoneBase):
    """Model for creating timezone records."""

    pass


class TimezoneResponse(TimezoneBase):
    """Timezone response model with database ID."""

    id: int = Field(..., gt=0)

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "timezone_name": "America/Sao_Paulo",
            }
        },
    )


class CountryBase(BaseModel):
    """Base model for country data without relationships."""

    name_common: str = Field(..., min_length=1, max_length=255)
    name_official: str = Field(..., min_length=1, max_length=255)
    iso_code_2: str = Field(..., min_length=2, max_length=2)
    iso_code_3: str = Field(..., min_length=3, max_length=3)
    region: str = Field(..., min_length=1, max_length=50)
    subregion: Optional[str] = Field(None, max_length=50)
    population: int = Field(..., ge=0, le=2000000000)
    area: Optional[float] = Field(None, ge=0)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)

    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator("iso_code_2", "iso_code_3")
    @classmethod
    def validate_iso_codes(cls, v: str) -> str:
        """Validate ISO codes format (uppercase alphanumeric)."""
        if not v.isalpha():
            raise ValueError("ISO codes must contain only alphabetic characters")
        return v.upper()

    @field_validator("region")
    @classmethod
    def validate_region(cls, v: str) -> str:
        """Validate region is one of the known regions."""
        valid_regions = {"Africa", "Americas", "Asia", "Europe", "Oceania"}
        if v not in valid_regions:
            raise ValueError(f"Region must be one of {valid_regions}")
        return v


class CountryCreate(CountryBase):
    """Model for creating country records."""

    pass


class CountryUpdate(BaseModel):
    """Model for updating country records."""

    name_common: Optional[str] = Field(None, min_length=1, max_length=255)
    name_official: Optional[str] = Field(None, min_length=1, max_length=255)
    region: Optional[str] = Field(None, min_length=1, max_length=50)
    subregion: Optional[str] = Field(None, max_length=50)
    population: Optional[int] = Field(None, ge=0, le=2000000000)
    area: Optional[float] = Field(None, ge=0)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)

    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator("region")
    @classmethod
    def validate_region(cls, v: str) -> str:
        """Validate region is one of the known regions."""
        if v is None:
            return v
        valid_regions = {"Africa", "Americas", "Asia", "Europe", "Oceania"}
        if v not in valid_regions:
            raise ValueError(f"Region must be one of {valid_regions}")
        return v


class CountryResponse(CountryBase):
    """Country response model with database ID and timestamps."""

    id: int = Field(..., gt=0)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "name_common": "Brazil",
                "name_official": "Federative Republic of Brazil",
                "iso_code_2": "BR",
                "iso_code_3": "BRA",
                "region": "Americas",
                "subregion": "South America",
                "population": 215313498,
                "area": 8514877.0,
                "latitude": -14.2350,
                "longitude": -51.9253,
                "created_at": "2026-09-15T10:30:00",
                "updated_at": "2026-09-15T10:30:00",
            }
        },
    )


class CountryDetailResponse(CountryResponse):
    """Country response with related entities (languages, currencies, timezones)."""

    languages: List[LanguageResponse] = Field(default_factory=list)
    currencies: List[CurrencyResponse] = Field(default_factory=list)
    timezones: List[TimezoneResponse] = Field(default_factory=list)

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "name_common": "Brazil",
                "name_official": "Federative Republic of Brazil",
                "iso_code_2": "BR",
                "iso_code_3": "BRA",
                "region": "Americas",
                "subregion": "South America",
                "population": 215313498,
                "area": 8514877.0,
                "latitude": -14.2350,
                "longitude": -51.9253,
                "created_at": "2026-09-15T10:30:00",
                "updated_at": "2026-09-15T10:30:00",
                "languages": [
                    {"id": 1, "language_code": "pt", "language_name": "Portuguese"}
                ],
                "currencies": [
                    {"id": 1, "currency_code": "BRL", "currency_name": "Brazilian Real"}
                ],
                "timezones": [
                    {"id": 1, "timezone_name": "America/Sao_Paulo"}
                ],
            }
        },
    )


class CountryListResponse(BaseModel):
    """Paginated list response for countries."""

    items: List[CountryResponse] = Field(default_factory=list)
    total: int = Field(..., ge=0)
    page: int = Field(..., ge=1)
    limit: int = Field(..., ge=1, le=100)
    pages: int = Field(..., ge=0)

    @field_validator("pages", mode="before")
    @classmethod
    def calculate_pages(cls, v: int, info: ValidationInfo) -> int:
        """Auto-calculate total pages if not provided."""
        if v == 0 and "total" in info.data and "limit" in info.data:
            import math

            return int(math.ceil(info.data["total"] / info.data["limit"]))
        return v

    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "id": 1,
                        "name_common": "Brazil",
                        "name_official": "Federative Republic of Brazil",
                        "iso_code_2": "BR",
                        "iso_code_3": "BRA",
                        "region": "Americas",
                        "subregion": "South America",
                        "population": 215313498,
                        "area": 8514877.0,
                        "latitude": -14.2350,
                        "longitude": -51.9253,
                        "created_at": "2026-09-15T10:30:00",
                        "updated_at": "2026-09-15T10:30:00",
                    }
                ],
                "total": 250,
                "page": 1,
                "limit": 20,
                "pages": 13,
            }
        },
    )


class RegionStatistics(BaseModel):
    """Statistics aggregated by region."""

    region: str = Field(..., min_length=1, max_length=50)
    total_countries: int = Field(..., ge=0)
    total_population: int = Field(..., ge=0)
    total_area: float = Field(..., ge=0)

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "region": "Americas",
                "total_countries": 35,
                "total_population": 1023456789,
                "total_area": 42165000.0,
            }
        },
    )


class GlobalStatistics(BaseModel):
    """Global statistics across all countries."""

    total_countries: int = Field(..., ge=0)
    total_population: int = Field(..., ge=0)
    total_area: float = Field(..., ge=0)
    average_population: float = Field(..., ge=0)
    average_area: float = Field(..., ge=0)
    regions: List[RegionStatistics] = Field(default_factory=list)

    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
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
                    },
                    {
                        "region": "Europe",
                        "total_countries": 50,
                        "total_population": 750000000,
                        "total_area": 10500000.0,
                    },
                ],
            }
        },
    )


class HealthCheckResponse(BaseModel):
    """API health check response model."""

    status: str = Field(..., pattern="^(ok|error)$")
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "status": "ok",
                "version": "1.0.0",
                "timestamp": "2026-09-15T10:30:00",
            }
        },
    )


class ErrorResponse(BaseModel):
    """Standard error response model."""

    detail: str = Field(...)
    error_code: Optional[str] = Field(None)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "detail": "Country not found",
                "error_code": "RECORD_NOT_FOUND",
                "timestamp": "2026-09-15T10:30:00",
            }
        },
    )


class SyncLogResponse(BaseModel):
    """Data synchronization log response."""

    sync_id: str = Field(...)
    status: str = Field(..., pattern="^(success|failed|partial)$")
    timestamp: datetime
    countries_inserted: int = Field(..., ge=0)
    countries_updated: int = Field(..., ge=0)
    countries_skipped: int = Field(..., ge=0)
    message: Optional[str] = Field(None)

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "sync_id": "sync_a1b2c3d4e5f6",
                "status": "success",
                "timestamp": "2026-09-15T10:30:00",
                "countries_inserted": 50,
                "countries_updated": 200,
                "countries_skipped": 0,
                "message": "Successfully synchronized 250 countries from REST Countries API",
            }
        },
    )
