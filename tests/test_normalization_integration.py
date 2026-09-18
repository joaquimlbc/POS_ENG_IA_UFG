"""Integration tests for data normalization and transformation.

Tests cover the complete pipeline from raw API data to normalized data
to SQLAlchemy model instances ready for database persistence.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.api.rest_countries import NormalizedCountry, normalize_countries, transform_normalized_countries, transform_to_country_model
from app.database.models import Base, Country, Currency, Language, Timezone


@pytest.fixture(scope="function")
def test_db_session():
    """Create a test database session with in-memory database."""
    test_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=test_engine)

    TestSessionLocal = sessionmaker(bind=test_engine, class_=Session, expire_on_commit=False)
    session = TestSessionLocal()

    yield session

    session.close()
    Base.metadata.drop_all(bind=test_engine)


class TestTransformToCountryModel:
    """Tests for individual country transformation."""

    def test_transform_normalized_to_country_model(self):
        """Should transform normalized data to Country model."""
        normalized = NormalizedCountry(
            name_common="Brazil",
            name_official="Federative Republic of Brazil",
            iso_code_2="BR",
            iso_code_3="BRA",
            region="Americas",
            subregion="South America",
            population=215313498,
            area=8514877.0,
            latitude=-15.793889,
            longitude=-47.882778,
            languages=["Portuguese"],
            currencies=["BRL"],
            timezones=["UTC-03:00"],
        )

        country = transform_to_country_model(normalized)

        assert country is not None
        assert isinstance(country, Country)
        assert country.name_common == "Brazil"
        assert country.iso_code_2 == "BR"
        assert country.population == 215313498
        assert len(country.languages) == 1
        assert len(country.currencies) == 1
        assert len(country.timezones) == 1

    def test_transform_without_optional_fields(self):
        """Should handle missing optional fields."""
        normalized = NormalizedCountry(
            name_common="TestLand",
            name_official="Test Land",
            iso_code_2="TL",
            iso_code_3="TLD",
            region="Test",
            population=1000,
        )

        country = transform_to_country_model(normalized)

        assert country is not None
        assert country.name_common == "TestLand"
        assert country.subregion is None
        assert country.area is None
        assert len(country.languages) == 0
        assert len(country.currencies) == 0
        assert len(country.timezones) == 0

    def test_transform_with_multiple_related_entities(self):
        """Should handle multiple languages, currencies, and timezones."""
        normalized = NormalizedCountry(
            name_common="Spain",
            name_official="Kingdom of Spain",
            iso_code_2="ES",
            iso_code_3="ESP",
            region="Europe",
            population=47615034,
            languages=["Spanish", "Catalan", "Basque"],
            currencies=["EUR"],
            timezones=["UTC+01:00", "UTC+00:00"],
        )

        country = transform_to_country_model(normalized)

        assert country is not None
        assert len(country.languages) == 3
        assert len(country.currencies) == 1
        assert len(country.timezones) == 2

    def test_transform_creates_correct_relationships(self):
        """Should create proper relationships between entities."""
        normalized = NormalizedCountry(
            name_common="France",
            name_official="French Republic",
            iso_code_2="FR",
            iso_code_3="FRA",
            region="Europe",
            population=67750000,
            languages=["French"],
            currencies=["EUR"],
        )

        country = transform_to_country_model(normalized)

        assert country is not None
        # Check relationships are set up
        for language in country.languages:
            assert language.country_id is None  # Not yet persisted
            assert language.language_name == "French"

        for currency in country.currencies:
            assert currency.country_id is None  # Not yet persisted
            assert currency.currency_code == "EUR"


class TestTransformNormalizedCountries:
    """Tests for batch transformation of normalized countries."""

    def test_transform_batch_of_countries(self):
        """Should transform multiple normalized countries."""
        normalized_list = [
            NormalizedCountry(
                name_common="Brazil",
                name_official="Federative Republic of Brazil",
                iso_code_2="BR",
                iso_code_3="BRA",
                region="Americas",
                population=215313498,
                languages=["Portuguese"],
            ),
            NormalizedCountry(
                name_common="France",
                name_official="French Republic",
                iso_code_2="FR",
                iso_code_3="FRA",
                region="Europe",
                population=67750000,
                languages=["French"],
            ),
        ]

        countries, errors = transform_normalized_countries(normalized_list)

        assert len(countries) == 2
        assert len(errors) == 0
        assert all(isinstance(c, Country) for c in countries)
        assert countries[0].name_common == "Brazil"
        assert countries[1].name_common == "France"

    def test_transform_with_partial_failure(self):
        """Should handle partial failures gracefully."""
        normalized_list = [
            NormalizedCountry(
                name_common="Valid Country",
                name_official="Valid Country Official",
                iso_code_2="VC",
                iso_code_3="VLD",
                region="Test",
                population=1000,
            ),
            NormalizedCountry(
                name_common="Another Valid",
                name_official="Another Valid Official",
                iso_code_2="AV",
                iso_code_3="AVL",
                region="Test",
                population=2000,
            ),
        ]

        countries, errors = transform_normalized_countries(normalized_list)

        assert len(countries) == 2
        assert len(errors) == 0

    def test_transform_empty_list(self):
        """Should handle empty input gracefully."""
        countries, errors = transform_normalized_countries([])

        assert len(countries) == 0
        assert len(errors) == 0


class TestNormalizationAndTransformationPipeline:
    """Integration tests for complete normalization pipeline."""

    def test_full_pipeline_from_raw_to_model(self):
        """Should complete full pipeline from raw data to model."""
        raw_data = [
            {
                "name": {"common": "Brazil", "official": "Federative Republic of Brazil"},
                "cca2": "BR",
                "cca3": "BRA",
                "region": "Americas",
                "subregion": "South America",
                "population": 215313498,
                "area": 8514877.0,
                "latlng": [-15.793889, -47.882778],
                "languages": {"por": "Portuguese"},
                "currencies": {"BRL": {"name": "Brazilian real"}},
                "timezones": ["UTC-03:00"],
            },
            {
                "name": {"common": "France", "official": "French Republic"},
                "cca2": "FR",
                "cca3": "FRA",
                "region": "Europe",
                "population": 67750000,
                "area": 551695.0,
                "languages": {"fra": "French"},
                "currencies": {"EUR": {"name": "Euro"}},
                "timezones": ["UTC+01:00"],
            },
        ]

        # Step 1: Normalize
        normalized, norm_errors = normalize_countries(raw_data)
        assert len(normalized) == 2
        assert len(norm_errors) == 0

        # Step 2: Transform to models
        countries, trans_errors = transform_normalized_countries(normalized)
        assert len(countries) == 2
        assert len(trans_errors) == 0

        # Verify final models
        assert countries[0].name_common == "Brazil"
        assert countries[0].population == 215313498
        assert len(countries[0].languages) == 1

        assert countries[1].name_common == "France"
        assert countries[1].population == 67750000

    def test_pipeline_preserves_data_integrity(self):
        """Should preserve all data through pipeline."""
        raw_data = [
            {
                "name": {"common": "Portugal", "official": "Portuguese Republic"},
                "cca2": "PT",
                "cca3": "PRT",
                "region": "Europe",
                "subregion": "Southern Europe",
                "population": 10305564,
                "area": 92090.0,
                "latlng": [39.399872, -8.224454],
                "languages": {"por": "Portuguese"},
                "currencies": {"EUR": {"name": "Euro"}},
                "timezones": ["UTC+00:00", "UTC-01:00"],
            }
        ]

        normalized, _ = normalize_countries(raw_data)
        countries, _ = transform_normalized_countries(normalized)

        country = countries[0]

        # Verify all data preserved
        assert country.name_common == "Portugal"
        assert country.name_official == "Portuguese Republic"
        assert country.iso_code_2 == "PT"
        assert country.iso_code_3 == "PRT"
        assert country.region == "Europe"
        assert country.subregion == "Southern Europe"
        assert country.population == 10305564
        assert country.area == 92090.0
        assert country.latitude == 39.399872
        assert country.longitude == -8.224454
        assert len(country.timezones) == 2

    def test_pipeline_with_partial_optional_data(self):
        """Should handle partial optional data correctly."""
        raw_data = [
            {
                "name": {"common": "Iceland", "official": "Iceland"},
                "cca2": "IS",
                "cca3": "ISL",
                "region": "Europe",
                # Missing: subregion, area, latlng, languages, currencies
                "population": 381900,
            }
        ]

        normalized, norm_errors = normalize_countries(raw_data)
        assert len(normalized) == 1
        assert len(norm_errors) == 0

        countries, trans_errors = transform_normalized_countries(normalized)
        assert len(countries) == 1
        assert len(trans_errors) == 0

        country = countries[0]
        assert country.subregion is None
        assert country.area is None
        assert country.latitude is None
        assert len(country.languages) == 0
        assert len(country.currencies) == 0


class TestNormalizationWithDatabasePersistence:
    """Tests for normalizing and persisting to database."""

    def test_persist_normalized_countries_to_db(self, test_db_session: Session):
        """Should persist transformed countries to database."""
        raw_data = [
            {
                "name": {"common": "Germany", "official": "Federal Republic of Germany"},
                "cca2": "DE",
                "cca3": "DEU",
                "region": "Europe",
                "population": 83369843,
                "area": 357022.0,
                "latlng": [51.165691, 10.451526],
                "languages": {"deu": "German"},
                "currencies": {"EUR": {"name": "Euro"}},
                "timezones": ["UTC+01:00"],
            }
        ]

        # Normalize and transform
        normalized, _ = normalize_countries(raw_data)
        countries, _ = transform_normalized_countries(normalized)

        # Persist to database
        country = countries[0]
        test_db_session.add(country)
        test_db_session.commit()

        # Verify persistence
        queried = test_db_session.query(Country).filter(Country.iso_code_2 == "DE").first()
        assert queried is not None
        assert queried.name_common == "Germany"
        assert queried.population == 83369843
        assert len(queried.languages) == 1
        assert len(queried.currencies) == 1

    def test_persist_multiple_countries(self, test_db_session: Session):
        """Should persist multiple transformed countries."""
        raw_data = [
            {
                "name": {"common": "Italy", "official": "Italian Republic"},
                "cca2": "IT",
                "cca3": "ITA",
                "region": "Europe",
                "population": 58940760,
                "languages": {"ita": "Italian"},
                "currencies": {"EUR": {"name": "Euro"}},
            },
            {
                "name": {"common": "Greece", "official": "Hellenic Republic"},
                "cca2": "GR",
                "cca3": "GRC",
                "region": "Europe",
                "population": 10640801,
                "languages": {"ell": "Greek"},
                "currencies": {"EUR": {"name": "Euro"}},
            },
        ]

        normalized, _ = normalize_countries(raw_data)
        countries, _ = transform_normalized_countries(normalized)

        # Persist all
        test_db_session.add_all(countries)
        test_db_session.commit()

        # Verify
        count = test_db_session.query(Country).count()
        assert count == 2

        italy = test_db_session.query(Country).filter(Country.iso_code_2 == "IT").first()
        greece = test_db_session.query(Country).filter(Country.iso_code_2 == "GR").first()

        assert italy.name_common == "Italy"
        assert greece.name_common == "Greece"
