"""Pytest configuration and shared fixtures for REST Countries API tests."""

import os
import tempfile
from typing import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database.models import Base
from app.database.connection import get_db_session
from app.models.task import CountryCreate
from app.service.country_service import CountryService


@pytest.fixture(scope="session")
def test_db_path() -> str:
    """Create temporary database for tests."""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)
    yield db_path
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture(scope="session")
def engine(test_db_path):
    """Create SQLAlchemy engine for tests."""
    database_url = f"sqlite:///{test_db_path}"
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},
        echo=False,
    )
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def session(engine) -> Generator[Session, None, None]:
    """Create database session for each test with rollback."""
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def service(session: Session) -> CountryService:
    """Create CountryService instance for tests."""
    return CountryService(session)


@pytest.fixture
def sample_country() -> CountryCreate:
    """Create sample country data for testing."""
    return CountryCreate(
        name_common="Brazil",
        name_official="Federative Republic of Brazil",
        iso_code_2="BR",
        iso_code_3="BRA",
        region="Americas",
        subregion="South America",
        population=215313498,
        area=8514877.0,
        latitude=-14.2350,
        longitude=-51.9253,
    )


@pytest.fixture
def sample_country_france() -> CountryCreate:
    """Create second sample country (France) for duplicate testing."""
    return CountryCreate(
        name_common="France",
        name_official="French Republic",
        iso_code_2="FR",
        iso_code_3="FRA",
        region="Europe",
        subregion="Western Europe",
        population=67970571,
        area=643801.0,
        latitude=46.2276,
        longitude=2.2137,
    )


@pytest.fixture
def service_with_sample_country(
    service: CountryService, sample_country: CountryCreate
) -> CountryService:
    """Create service with pre-loaded sample country."""
    service.create_country(sample_country)
    return service


@pytest.fixture
def service_with_250_countries(service: CountryService) -> CountryService:
    """Create service with 250 test countries for pagination testing."""
    countries = []
    regions = ["Africa", "Americas", "Asia", "Europe", "Oceania"]
    # ISO codes must be alphabetic only
    iso2_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    iso3_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    for i in range(250):
        region = regions[i % 5]
        # Generate valid ISO2 codes (2 letters)
        iso2 = iso2_chars[i % 26] + iso2_chars[(i // 26) % 26]
        # Generate valid ISO3 codes (3 letters)
        iso3 = (
            iso3_chars[i % 26]
            + iso3_chars[(i // 26) % 26]
            + iso3_chars[(i // 52) % 26]
        )

        country = CountryCreate(
            name_common=f"Country {i}",
            name_official=f"Official Country {i}",
            iso_code_2=iso2,
            iso_code_3=iso3,
            region=region,
            subregion=f"Subregion {i}",
            population=1000000 + i * 1000,
            area=10000.0 + i,
            latitude=-90 + (i % 180),
            longitude=-180 + (i % 360),
        )
        countries.append(country)

    service.sync_countries_batch(countries, validate_quality=False)
    return service


@pytest.fixture
def service_with_relationships(
    service: CountryService, sample_country: CountryCreate
) -> CountryService:
    """Create service with country that has relationships for cascade testing."""
    from app.models.task import CurrencyCreate, LanguageCreate, TimezoneCreate

    country = service.create_country(sample_country)

    languages = [
        LanguageCreate(language_code="PT", language_name="Portuguese"),
        LanguageCreate(language_code="EN", language_name="English"),
    ]

    currencies = [
        CurrencyCreate(currency_code="BRL", currency_name="Brazilian Real"),
    ]

    timezones = [
        TimezoneCreate(timezone_name="America/Sao_Paulo"),
    ]

    service.add_languages(country.id, languages)
    service.add_currencies(country.id, currencies)
    service.add_timezones(country.id, timezones)

    return service
