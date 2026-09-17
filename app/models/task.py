"""Pydantic v2 data models for REST Countries API domain entities.

This module defines the core data models used throughout the application
for validation, serialization, and API contracts.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


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

    model_config = ConfigDict(from_attributes=True)


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

    model_config = ConfigDict(from_attributes=True)


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

    model_config = ConfigDict(from_attributes=True)


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

    model_config = ConfigDict(from_attributes=True)


class CountryDetailResponse(CountryResponse):
    """Country response with related entities (languages, currencies, timezones)."""

    languages: List[LanguageResponse] = Field(default_factory=list)
    currencies: List[CurrencyResponse] = Field(default_factory=list)
    timezones: List[TimezoneResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class CountryListResponse(BaseModel):
    """Paginated list response for countries."""

    items: List[CountryResponse] = Field(default_factory=list)
    total: int = Field(..., ge=0)
    page: int = Field(..., ge=1)
    limit: int = Field(..., ge=1, le=100)
    pages: int = Field(..., ge=0)

    @field_validator("pages", mode="before")
    @classmethod
    def calculate_pages(cls, v: int, info) -> int:
        """Auto-calculate total pages if not provided."""
        if v == 0 and "total" in info.data and "limit" in info.data:
            import math
            return math.ceil(info.data["total"] / info.data["limit"])
        return v

    model_config = ConfigDict(str_strip_whitespace=True)


class RegionStatistics(BaseModel):
    """Statistics aggregated by region."""

    region: str = Field(..., min_length=1, max_length=50)
    total_countries: int = Field(..., ge=0)
    total_population: int = Field(..., ge=0)
    total_area: float = Field(..., ge=0)

    model_config = ConfigDict(from_attributes=True)


class GlobalStatistics(BaseModel):
    """Global statistics across all countries."""

    total_countries: int = Field(..., ge=0)
    total_population: int = Field(..., ge=0)
    total_area: float = Field(..., ge=0)
    average_population: float = Field(..., ge=0)
    average_area: float = Field(..., ge=0)
    regions: List[RegionStatistics] = Field(default_factory=list)

    model_config = ConfigDict(str_strip_whitespace=True)


class HealthCheckResponse(BaseModel):
    """API health check response model."""

    status: str = Field(..., pattern="^(ok|error)$")
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(str_strip_whitespace=True)


class ErrorResponse(BaseModel):
    """Standard error response model."""

    detail: str = Field(...)
    error_code: Optional[str] = Field(None)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(str_strip_whitespace=True)


class SyncLogResponse(BaseModel):
    """Data synchronization log response."""

    sync_id: str = Field(...)
    status: str = Field(..., pattern="^(success|failed|partial)$")
    timestamp: datetime
    countries_inserted: int = Field(..., ge=0)
    countries_updated: int = Field(..., ge=0)
    countries_skipped: int = Field(..., ge=0)
    message: Optional[str] = Field(None)

    model_config = ConfigDict(from_attributes=True)
