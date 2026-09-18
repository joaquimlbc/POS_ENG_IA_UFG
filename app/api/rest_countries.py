"""HTTP Client for REST Countries API.

Handles fetching, normalizing, and validating country data from the REST Countries API.
Implements retry logic, timeout handling, and structured logging.
"""

import time
from typing import Any, List, Optional

import requests
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.utils.logger import get_logger

# Import database models for transformation
try:
    from app.database.models import Country, Currency, Language, Timezone
except ImportError:
    # Allow module to be imported without database models present
    Country = None
    Currency = None
    Language = None
    Timezone = None

logger = get_logger(__name__)

API_URL = "https://restcountries.com/v3.1/all"
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3
BACKOFF_FACTOR = 0.5


class CountryResponse(BaseModel):
    """Schema for validating country data from REST Countries API."""

    model_config = ConfigDict(extra="allow")

    name: dict = Field(..., description="Country name (common and official)")
    cca2: str = Field(..., description="ISO 3166-1 alpha-2 code")
    cca3: str = Field(..., description="ISO 3166-1 alpha-3 code")
    region: str = Field(..., description="Continent/region")
    subregion: Optional[str] = Field(None, description="Subregion name")
    population: int = Field(..., description="Population count")
    area: Optional[float] = Field(None, description="Area in km²")
    latlng: Optional[List[float]] = Field(None, description="Latitude and longitude")
    languages: Optional[dict] = Field(None, description="Languages spoken")
    currencies: Optional[dict] = Field(None, description="Currencies used")
    timezones: Optional[List[str]] = Field(None, description="Timezones")


class NormalizedCountry(BaseModel):
    """Normalized country data schema for internal use."""

    name_common: str
    name_official: str
    iso_code_2: str
    iso_code_3: str
    region: str
    subregion: Optional[str] = None
    population: int
    area: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    languages: Optional[List[str]] = None
    currencies: Optional[List[str]] = None
    timezones: Optional[List[str]] = None


def _create_session_with_retry(
    max_retries: int = MAX_RETRIES, backoff_factor: float = BACKOFF_FACTOR
) -> requests.Session:
    """Create requests session with automatic retry strategy.

    Args:
        max_retries: Maximum number of retry attempts
        backoff_factor: Backoff factor for exponential retry strategy

    Returns:
        Configured requests.Session with retry strategy
    """
    session = requests.Session()

    retry_strategy = Retry(
        total=max_retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session


def fetch_countries(
    timeout: int = DEFAULT_TIMEOUT, url: str = API_URL
) -> List[dict]:
    """Fetch all countries from REST Countries API.

    Implements automatic retry with exponential backoff and timeout handling.

    Args:
        timeout: Request timeout in seconds (default: 30)
        url: API endpoint URL (default: REST Countries API v3.1/all)

    Returns:
        List of country dictionaries from API

    Raises:
        requests.RequestException: If all retry attempts fail
        ValueError: If response is empty or invalid
    """
    session = _create_session_with_retry()
    start_time = time.time()

    try:
        logger.info(f"Fetching countries from {url} (timeout={timeout}s)")

        response = session.get(url, timeout=timeout)
        response.raise_for_status()

        data = response.json()

        if not isinstance(data, list) or len(data) == 0:
            logger.warning("API returned empty or invalid response")
            raise ValueError("API returned empty response")

        elapsed = time.time() - start_time
        logger.info(
            f"Successfully fetched {len(data)} countries in {elapsed:.2f}s "
            f"(status={response.status_code})"
        )

        return data

    except requests.Timeout:
        elapsed = time.time() - start_time
        logger.error(f"Request timeout after {elapsed:.2f}s")
        raise
    except requests.RequestException as e:
        logger.error(f"Failed to fetch countries: {type(e).__name__}: {str(e)}")
        raise
    finally:
        session.close()


def normalize_countries(raw_data: List[dict]) -> tuple[List[NormalizedCountry], List[str]]:
    """Normalize raw API response data to internal schema.

    Validates each country record and handles data extraction/transformation.
    Logs errors for individual countries but continues processing.

    Args:
        raw_data: List of raw country dictionaries from API

    Returns:
        Tuple of (valid normalized countries, list of error messages)
    """
    normalized = []
    errors = []

    logger.info(f"Normalizing {len(raw_data)} countries")

    for idx, raw_country in enumerate(raw_data):
        try:
            # Validate raw data against API schema
            api_schema = CountryResponse(**raw_country)

            # Extract and normalize fields
            name_common = api_schema.name.get("common", "")
            name_official = api_schema.name.get("official", "")

            if not name_common or not name_official:
                raise ValueError(
                    f"Missing name data for country {raw_country.get('cca2', 'UNKNOWN')}"
                )

            # Extract coordinates
            latitude = None
            longitude = None
            if api_schema.latlng and len(api_schema.latlng) >= 2:
                latitude, longitude = api_schema.latlng[0], api_schema.latlng[1]

            # Extract languages
            languages = None
            if api_schema.languages:
                languages = list(api_schema.languages.values())

            # Extract currencies
            currencies = None
            if api_schema.currencies:
                currencies = list(api_schema.currencies.keys())

            # Create normalized record
            normalized_country = NormalizedCountry(
                name_common=name_common,
                name_official=name_official,
                iso_code_2=api_schema.cca2,
                iso_code_3=api_schema.cca3,
                region=api_schema.region,
                subregion=api_schema.subregion,
                population=api_schema.population,
                area=api_schema.area,
                latitude=latitude,
                longitude=longitude,
                languages=languages,
                currencies=currencies,
                timezones=api_schema.timezones,
            )

            normalized.append(normalized_country)
            logger.debug(f"Normalized {name_common} ({api_schema.cca2})")

        except ValidationError as e:
            error_msg = (
                f"Validation error for country {idx}: "
                f"{raw_country.get('name', {}).get('common', 'UNKNOWN')} - {str(e)}"
            )
            logger.warning(error_msg)
            errors.append(error_msg)
        except (KeyError, ValueError) as e:
            error_msg = (
                f"Data extraction error for country {idx}: "
                f"{raw_country.get('name', {}).get('common', 'UNKNOWN')} - {str(e)}"
            )
            logger.warning(error_msg)
            errors.append(error_msg)

    logger.info(
        f"Normalized {len(normalized)}/{len(raw_data)} countries "
        f"({len(errors)} errors)"
    )

    return normalized, errors


def transform_to_country_model(normalized: NormalizedCountry) -> Optional["Country"]:
    """Transform normalized country data to SQLAlchemy Country model.

    Converts Pydantic normalized schema to database Country model with
    related Language, Currency, and Timezone entities.

    Args:
        normalized: NormalizedCountry instance with validated data

    Returns:
        Country model instance with related entities, or None if transformation fails

    Raises:
        ValueError: If required fields are missing or invalid
    """
    if Country is None:
        raise ImportError("Database models not available")

    try:
        # Create country record
        country = Country(
            name_common=normalized.name_common,
            name_official=normalized.name_official,
            iso_code_2=normalized.iso_code_2,
            iso_code_3=normalized.iso_code_3,
            region=normalized.region,
            subregion=normalized.subregion,
            population=normalized.population,
            area=normalized.area,
            latitude=normalized.latitude,
            longitude=normalized.longitude,
        )

        # Add language relationships
        if normalized.languages:
            for lang_name in normalized.languages:
                # Extract language code from name (simplified - assumes ISO 639-1 codes)
                # In production, you'd have a proper mapping
                language = Language(
                    language_name=lang_name,
                    language_code=lang_name[:3].lower(),  # Simplified
                )
                country.languages.append(language)

        # Add currency relationships
        if normalized.currencies:
            for curr_code in normalized.currencies:
                currency = Currency(
                    currency_code=curr_code,
                    currency_name=curr_code,  # Would need mapping in production
                )
                country.currencies.append(currency)

        # Add timezone relationships
        if normalized.timezones:
            for tz_name in normalized.timezones:
                timezone = Timezone(timezone_name=tz_name)
                country.timezones.append(timezone)

        logger.debug(
            f"Transformed {normalized.name_common} to Country model "
            f"with {len(country.languages)} languages, "
            f"{len(country.currencies)} currencies, "
            f"{len(country.timezones)} timezones"
        )

        return country

    except (ValueError, TypeError) as e:
        logger.error(f"Failed to transform {normalized.name_common}: {str(e)}")
        return None


def transform_normalized_countries(
    normalized_countries: List[NormalizedCountry],
) -> tuple[List["Country"], List[str]]:
    """Transform list of normalized countries to SQLAlchemy Country models.

    Args:
        normalized_countries: List of NormalizedCountry instances

    Returns:
        Tuple of (valid Country models, list of error messages)
    """
    if Country is None:
        raise ImportError("Database models not available")

    countries = []
    errors = []

    logger.info(f"Transforming {len(normalized_countries)} normalized countries to models")

    for normalized in normalized_countries:
        try:
            country = transform_to_country_model(normalized)
            if country is not None:
                countries.append(country)
            else:
                errors.append(f"Failed to transform {normalized.name_common}")
        except Exception as e:
            error_msg = f"Transformation error for {normalized.name_common}: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)

    logger.info(
        f"Transformed {len(countries)}/{len(normalized_countries)} countries "
        f"({len(errors)} errors)"
    )

    return countries, errors
