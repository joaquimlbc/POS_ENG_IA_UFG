"""HTTP Client for REST Countries API.

Handles fetching, normalizing, and validating country data from the REST
Countries API (v5, https://api.restcountries.com). Implements retry logic,
pagination, timeout handling, and structured logging.

The v5 API requires an API key (Bearer token), read from the
REST_COUNTRIES_API_KEY environment variable, and paginates results
(free-tier plans are capped at 100 objects per request).
"""

import os
import time
from typing import Any, List, Optional

import requests
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.database.models import Country, Currency, Language, Timezone
from app.utils.errors import ConfigurationError
from app.utils.logger import get_logger

load_dotenv()

logger = get_logger(__name__)

API_URL = "https://api.restcountries.com/countries/v5"
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3
BACKOFF_FACTOR = 0.5
PAGE_LIMIT = 100  # Maximum objects per request allowed on the free plan
MAX_PAGES = 50  # Safety cap against pathological pagination loops


class CountryNames(BaseModel):
    """Name block of a REST Countries API v5 country object."""

    model_config = ConfigDict(extra="allow")

    common: str = Field(..., description="Common country name")
    official: str = Field(..., description="Official country name")


class CountryCodes(BaseModel):
    """ISO code block of a REST Countries API v5 country object."""

    model_config = ConfigDict(extra="allow")

    alpha_2: str = Field(..., description="ISO 3166-1 alpha-2 code")
    alpha_3: str = Field(..., description="ISO 3166-1 alpha-3 code")


class CountryArea(BaseModel):
    """Area block of a REST Countries API v5 country object."""

    model_config = ConfigDict(extra="allow")

    kilometers: Optional[float] = Field(None, description="Area in km²")


class CountryCoordinates(BaseModel):
    """Coordinates block of a REST Countries API v5 country object."""

    model_config = ConfigDict(extra="allow")

    lat: Optional[float] = Field(None, description="Latitude")
    lng: Optional[float] = Field(None, description="Longitude")


class CountryLanguageItem(BaseModel):
    """Single language entry of a REST Countries API v5 country object."""

    model_config = ConfigDict(extra="allow")

    name: str = Field(..., description="Language name")


class CountryCurrencyItem(BaseModel):
    """Single currency entry of a REST Countries API v5 country object."""

    model_config = ConfigDict(extra="allow")

    code: str = Field(..., description="ISO 4217 currency code")
    name: Optional[str] = Field(None, description="Currency name")


class CountryResponse(BaseModel):
    """Schema for validating a single country object from REST Countries API v5."""

    model_config = ConfigDict(extra="allow")

    names: CountryNames = Field(..., description="Country name (common and official)")
    codes: CountryCodes = Field(..., description="ISO 3166-1 alpha codes")
    region: str = Field(..., description="Continent/region")
    subregion: Optional[str] = Field(None, description="Subregion name")
    population: int = Field(..., description="Population count")
    area: Optional[CountryArea] = Field(None, description="Area in km²")
    coordinates: Optional[CountryCoordinates] = Field(
        None, description="Latitude and longitude"
    )
    languages: Optional[List[CountryLanguageItem]] = Field(
        None, description="Languages spoken"
    )
    currencies: Optional[List[CountryCurrencyItem]] = Field(
        None, description="Currencies used"
    )
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


def _get_api_key(api_key: Optional[str] = None) -> str:
    """Resolve the REST Countries API key from argument or environment.

    Args:
        api_key: Explicit API key, takes precedence over the environment.

    Returns:
        The resolved API key.

    Raises:
        ConfigurationError: If no API key is provided or configured.
    """
    resolved = api_key or os.getenv("REST_COUNTRIES_API_KEY")
    if not resolved:
        raise ConfigurationError(
            "REST_COUNTRIES_API_KEY",
            "Required to authenticate with the REST Countries API v5. "
            "Set it in your .env file.",
        )
    return resolved


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
    timeout: int = DEFAULT_TIMEOUT,
    url: str = API_URL,
    api_key: Optional[str] = None,
    page_limit: int = PAGE_LIMIT,
) -> List[dict[str, Any]]:
    """Fetch all countries from the REST Countries API v5, paginating as needed.

    Implements automatic retry with exponential backoff, timeout handling,
    and pagination (the API caps free-tier requests at ``page_limit``
    objects per page).

    Args:
        timeout: Request timeout in seconds (default: 30)
        url: API base endpoint URL (default: REST Countries API v5)
        api_key: Explicit API key; falls back to REST_COUNTRIES_API_KEY env var
        page_limit: Objects requested per page (max 100 on the free plan)

    Returns:
        List of country dictionaries (v5 schema) from API

    Raises:
        ConfigurationError: If no API key is available
        requests.RequestException: If all retry attempts fail
        ValueError: If the API reports an error, or the response is empty/invalid
    """
    resolved_key = _get_api_key(api_key)
    session = _create_session_with_retry()
    headers = {"Authorization": f"Bearer {resolved_key}"}
    start_time = time.time()
    all_objects: List[dict[str, Any]] = []

    try:
        logger.info(f"Fetching countries from {url} (timeout={timeout}s)")

        offset = 0
        for _ in range(MAX_PAGES):
            response = session.get(
                url,
                params={"limit": page_limit, "offset": offset},
                headers=headers,
                timeout=timeout,
            )
            response.raise_for_status()
            payload = response.json()

            if payload.get("errors"):
                message = payload["errors"][0].get("message", "Unknown API error")
                logger.error(f"REST Countries API returned an error: {message}")
                raise ValueError(f"REST Countries API error: {message}")

            data = payload.get("data") or {}
            objects = data.get("objects")
            if not isinstance(objects, list):
                logger.warning("API returned empty or invalid response")
                raise ValueError("API returned empty response")

            all_objects.extend(objects)

            meta = data.get("meta") or {}
            if not meta.get("more"):
                break
            offset += page_limit
        else:
            logger.warning(f"Aborted pagination after {MAX_PAGES} pages (safety cap)")

        if not all_objects:
            logger.warning("API returned empty or invalid response")
            raise ValueError("API returned empty response")

        elapsed = time.time() - start_time
        logger.info(
            f"Successfully fetched {len(all_objects)} countries in {elapsed:.2f}s"
        )

        return all_objects

    except requests.Timeout:
        elapsed = time.time() - start_time
        logger.error(f"Request timeout after {elapsed:.2f}s")
        raise
    except requests.RequestException as e:
        logger.error(f"Failed to fetch countries: {type(e).__name__}: {str(e)}")
        raise
    finally:
        session.close()


def normalize_countries(
    raw_data: List[dict[str, Any]],
) -> tuple[List[NormalizedCountry], List[str]]:
    """Normalize raw API response data to internal schema.

    Validates each country record and handles data extraction/transformation.
    Logs errors for individual countries but continues processing.

    Args:
        raw_data: List of raw country dictionaries from API (v5 schema)

    Returns:
        Tuple of (valid normalized countries, list of error messages)
    """
    normalized = []
    errors = []

    logger.info(f"Normalizing {len(raw_data)} countries")

    for idx, raw_country in enumerate(raw_data):
        display_name = raw_country.get("names", {}).get("common", "UNKNOWN")
        try:
            # Validate raw data against API schema
            api_schema = CountryResponse(**raw_country)

            name_common = api_schema.names.common
            name_official = api_schema.names.official

            if not name_common or not name_official:
                raise ValueError(
                    f"Missing name data for country {api_schema.codes.alpha_2}"
                )

            # Territories without an assigned ISO 3166-1 code (e.g. disputed
            # regions like Northern Cyprus) report empty alpha_2/alpha_3
            # codes; skip them rather than let several collide on "".
            if not api_schema.codes.alpha_2 or not api_schema.codes.alpha_3:
                raise ValueError(f"Missing ISO code data for country {name_common}")

            # Extract coordinates
            latitude = None
            longitude = None
            if api_schema.coordinates:
                latitude = api_schema.coordinates.lat
                longitude = api_schema.coordinates.lng

            # Extract languages
            languages = None
            if api_schema.languages:
                languages = [lang.name for lang in api_schema.languages]

            # Extract currencies
            currencies = None
            if api_schema.currencies:
                currencies = [curr.code for curr in api_schema.currencies]

            # Extract area
            area = api_schema.area.kilometers if api_schema.area else None

            # Create normalized record
            normalized_country = NormalizedCountry(
                name_common=name_common,
                name_official=name_official,
                iso_code_2=api_schema.codes.alpha_2,
                iso_code_3=api_schema.codes.alpha_3,
                region=api_schema.region,
                subregion=api_schema.subregion,
                population=api_schema.population,
                area=area,
                latitude=latitude,
                longitude=longitude,
                languages=languages,
                currencies=currencies,
                timezones=api_schema.timezones,
            )

            normalized.append(normalized_country)
            logger.debug(f"Normalized {name_common} ({api_schema.codes.alpha_2})")

        except ValidationError as e:
            error_msg = f"Validation error for country {idx}: {display_name} - {str(e)}"
            logger.warning(error_msg)
            errors.append(error_msg)
        except (KeyError, ValueError, AttributeError) as e:
            error_msg = (
                f"Data extraction error for country {idx}: {display_name} - {str(e)}"
            )
            logger.warning(error_msg)
            errors.append(error_msg)

    logger.info(
        f"Normalized {len(normalized)}/{len(raw_data)} countries "
        f"({len(errors)} errors)"
    )

    return normalized, errors


def transform_to_country_model(normalized: NormalizedCountry) -> Optional[Country]:
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
) -> tuple[List[Country], List[str]]:
    """Transform list of normalized countries to SQLAlchemy Country models.

    Args:
        normalized_countries: List of NormalizedCountry instances

    Returns:
        Tuple of (valid Country models, list of error messages)
    """
    countries: List[Country] = []
    errors: List[str] = []

    logger.info(
        f"Transforming {len(normalized_countries)} normalized countries to models"
    )

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
