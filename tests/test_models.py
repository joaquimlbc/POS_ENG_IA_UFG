"""Unit tests for SQLAlchemy ORM models.

Tests cover model instantiation, relationships, constraints, and database interactions.
"""

from datetime import datetime

import pytest
from sqlalchemy import Column, String, create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from app.database.models import Base, Country, Currency, Language, Timezone


@pytest.fixture(scope="function")
def test_db_session():
    """Create a test database session with fresh in-memory database.

    Uses SQLite in-memory database for each test, cleaning up after.
    """
    # Create in-memory SQLite database for testing
    test_engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=test_engine)

    TestSessionLocal = sessionmaker(bind=test_engine, class_=Session, expire_on_commit=False)
    session = TestSessionLocal()

    yield session

    session.close()
    Base.metadata.drop_all(bind=test_engine)


class TestCountryModel:
    """Tests for Country model."""

    def test_create_country(self, test_db_session: Session):
        """Should successfully create and persist a Country."""
        country = Country(
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
        )

        test_db_session.add(country)
        test_db_session.commit()

        assert country.id is not None
        assert country.name_common == "Brazil"
        assert country.iso_code_2 == "BR"
        assert isinstance(country.created_at, datetime)
        assert isinstance(country.updated_at, datetime)

    def test_country_required_fields(self, test_db_session: Session):
        """Should enforce required fields on Country."""
        country = Country(
            name_common="Test",
            name_official="Test Official",
            iso_code_2="TS",
            iso_code_3="TST",
            region="Test",
            population=1000,
        )
        test_db_session.add(country)
        test_db_session.commit()

        # Verify required fields were saved
        assert country.name_common == "Test"
        assert country.name_official == "Test Official"

        # Verify optional fields default to None
        assert country.subregion is None
        assert country.area is None
        assert country.latitude is None
        assert country.longitude is None

    def test_country_unique_constraints(self, test_db_session: Session):
        """Should enforce unique constraints on ISO codes and name."""
        country1 = Country(
            name_common="Brazil",
            name_official="Federative Republic of Brazil",
            iso_code_2="BR",
            iso_code_3="BRA",
            region="Americas",
            population=215313498,
        )
        test_db_session.add(country1)
        test_db_session.commit()

        # Try to add duplicate
        country2 = Country(
            name_common="Brazil",
            name_official="Duplicate",
            iso_code_2="XX",
            iso_code_3="XXX",
            region="Test",
            population=1000,
        )
        test_db_session.add(country2)

        with pytest.raises(Exception):  # IntegrityError
            test_db_session.commit()

    def test_country_iso_codes_unique(self, test_db_session: Session):
        """Should enforce unique constraints on ISO codes."""
        country1 = Country(
            name_common="Brazil",
            name_official="Federative Republic of Brazil",
            iso_code_2="BR",
            iso_code_3="BRA",
            region="Americas",
            population=215313498,
        )
        test_db_session.add(country1)
        test_db_session.commit()

        # Try with duplicate iso_code_2
        country2 = Country(
            name_common="Other",
            name_official="Other Country",
            iso_code_2="BR",
            iso_code_3="OTHER",
            region="Test",
            population=1000,
        )
        test_db_session.add(country2)

        with pytest.raises(Exception):  # IntegrityError
            test_db_session.commit()

    def test_country_repr(self, test_db_session: Session):
        """Should have proper string representation."""
        country = Country(
            name_common="Brazil",
            name_official="Federative Republic of Brazil",
            iso_code_2="BR",
            iso_code_3="BRA",
            region="Americas",
            population=215313498,
        )
        test_db_session.add(country)
        test_db_session.commit()

        repr_str = repr(country)
        assert "Country" in repr_str
        assert "Brazil" in repr_str
        assert "BR" in repr_str

    def test_country_indexed_columns(self):
        """Should have indexes on search columns."""
        # Get table metadata to check indexes
        table = Country.__table__
        index_names = {idx.name for idx in table.indexes}

        expected_indexes = {
            "idx_iso_code_2",
            "idx_iso_code_3",
            "idx_region",
            "idx_region_subregion",
        }

        assert expected_indexes.issubset(index_names), f"Missing indexes: {expected_indexes - index_names}"

    def test_country_timestamps(self, test_db_session: Session):
        """Should automatically manage created_at and updated_at."""
        country = Country(
            name_common="Brazil",
            name_official="Federative Republic of Brazil",
            iso_code_2="BR",
            iso_code_3="BRA",
            region="Americas",
            population=215313498,
        )

        assert country.created_at is None  # Not set until committed
        assert country.updated_at is None

        test_db_session.add(country)
        test_db_session.commit()

        assert country.created_at is not None
        assert country.updated_at is not None
        assert isinstance(country.created_at, datetime)

        created_at = country.created_at
        updated_at = country.updated_at

        # Update country
        country.name_common = "Brazil Updated"
        test_db_session.commit()

        # updated_at should change, created_at should not
        assert country.created_at == created_at
        assert country.updated_at >= updated_at


class TestLanguageModel:
    """Tests for Language model."""

    def test_create_language(self, test_db_session: Session):
        """Should successfully create and persist a Language."""
        country = Country(
            name_common="Brazil",
            name_official="Federative Republic of Brazil",
            iso_code_2="BR",
            iso_code_3="BRA",
            region="Americas",
            population=215313498,
        )
        language = Language(
            country=country,
            language_code="por",
            language_name="Portuguese",
        )

        test_db_session.add(country)
        test_db_session.add(language)
        test_db_session.commit()

        assert language.id is not None
        assert language.country_id == country.id
        assert language.language_code == "por"
        assert language.language_name == "Portuguese"

    def test_language_country_relationship(self, test_db_session: Session):
        """Should maintain proper relationship between Language and Country."""
        country = Country(
            name_common="Brazil",
            name_official="Federative Republic of Brazil",
            iso_code_2="BR",
            iso_code_3="BRA",
            region="Americas",
            population=215313498,
        )
        test_db_session.add(country)
        test_db_session.flush()

        lang1 = Language(country_id=country.id, language_code="por", language_name="Portuguese")
        lang2 = Language(country_id=country.id, language_code="eng", language_name="English")

        test_db_session.add(lang1)
        test_db_session.add(lang2)
        test_db_session.commit()

        # Verify relationship from Country side
        assert len(country.languages) == 2
        assert any(l.language_code == "por" for l in country.languages)
        assert any(l.language_code == "eng" for l in country.languages)

    def test_language_cascade_delete(self, test_db_session: Session):
        """Should cascade delete languages when country is deleted."""
        country = Country(
            name_common="Brazil",
            name_official="Federative Republic of Brazil",
            iso_code_2="BR",
            iso_code_3="BRA",
            region="Americas",
            population=215313498,
        )
        language = Language(
            country=country,
            language_code="por",
            language_name="Portuguese",
        )

        test_db_session.add(country)
        test_db_session.add(language)
        test_db_session.commit()

        language_id = language.id

        # Delete country
        test_db_session.delete(country)
        test_db_session.commit()

        # Language should also be deleted
        deleted_language = test_db_session.query(Language).filter(Language.id == language_id).first()
        assert deleted_language is None

    def test_language_repr(self, test_db_session: Session):
        """Should have proper string representation."""
        language = Language(
            language_code="por",
            language_name="Portuguese",
        )

        repr_str = repr(language)
        assert "Language" in repr_str
        assert "por" in repr_str


class TestCurrencyModel:
    """Tests for Currency model."""

    def test_create_currency(self, test_db_session: Session):
        """Should successfully create and persist a Currency."""
        country = Country(
            name_common="Brazil",
            name_official="Federative Republic of Brazil",
            iso_code_2="BR",
            iso_code_3="BRA",
            region="Americas",
            population=215313498,
        )
        currency = Currency(
            country=country,
            currency_code="BRL",
            currency_name="Brazilian Real",
        )

        test_db_session.add(country)
        test_db_session.add(currency)
        test_db_session.commit()

        assert currency.id is not None
        assert currency.country_id == country.id
        assert currency.currency_code == "BRL"

    def test_currency_country_relationship(self, test_db_session: Session):
        """Should maintain proper relationship between Currency and Country."""
        country = Country(
            name_common="Brazil",
            name_official="Federative Republic of Brazil",
            iso_code_2="BR",
            iso_code_3="BRA",
            region="Americas",
            population=215313498,
        )
        test_db_session.add(country)
        test_db_session.flush()

        curr1 = Currency(country_id=country.id, currency_code="BRL", currency_name="Brazilian Real")
        curr2 = Currency(country_id=country.id, currency_code="USD", currency_name="US Dollar")

        test_db_session.add(curr1)
        test_db_session.add(curr2)
        test_db_session.commit()

        # Verify relationship
        assert len(country.currencies) == 2
        assert any(c.currency_code == "BRL" for c in country.currencies)

    def test_currency_cascade_delete(self, test_db_session: Session):
        """Should cascade delete currencies when country is deleted."""
        country = Country(
            name_common="Brazil",
            name_official="Federative Republic of Brazil",
            iso_code_2="BR",
            iso_code_3="BRA",
            region="Americas",
            population=215313498,
        )
        currency = Currency(
            country=country,
            currency_code="BRL",
            currency_name="Brazilian Real",
        )

        test_db_session.add(country)
        test_db_session.add(currency)
        test_db_session.commit()

        currency_id = currency.id

        test_db_session.delete(country)
        test_db_session.commit()

        deleted_currency = test_db_session.query(Currency).filter(Currency.id == currency_id).first()
        assert deleted_currency is None

    def test_currency_repr(self, test_db_session: Session):
        """Should have proper string representation."""
        currency = Currency(
            currency_code="BRL",
            currency_name="Brazilian Real",
        )

        repr_str = repr(currency)
        assert "Currency" in repr_str
        assert "BRL" in repr_str


class TestTimezoneModel:
    """Tests for Timezone model."""

    def test_create_timezone(self, test_db_session: Session):
        """Should successfully create and persist a Timezone."""
        country = Country(
            name_common="Brazil",
            name_official="Federative Republic of Brazil",
            iso_code_2="BR",
            iso_code_3="BRA",
            region="Americas",
            population=215313498,
        )
        timezone = Timezone(
            country=country,
            timezone_name="UTC-03:00",
        )

        test_db_session.add(country)
        test_db_session.add(timezone)
        test_db_session.commit()

        assert timezone.id is not None
        assert timezone.country_id == country.id
        assert timezone.timezone_name == "UTC-03:00"

    def test_timezone_country_relationship(self, test_db_session: Session):
        """Should maintain proper relationship between Timezone and Country."""
        country = Country(
            name_common="Brazil",
            name_official="Federative Republic of Brazil",
            iso_code_2="BR",
            iso_code_3="BRA",
            region="Americas",
            population=215313498,
        )
        test_db_session.add(country)
        test_db_session.flush()

        tz1 = Timezone(country_id=country.id, timezone_name="UTC-03:00")
        tz2 = Timezone(country_id=country.id, timezone_name="UTC-04:00")

        test_db_session.add(tz1)
        test_db_session.add(tz2)
        test_db_session.commit()

        assert len(country.timezones) == 2
        assert any(t.timezone_name == "UTC-03:00" for t in country.timezones)

    def test_timezone_cascade_delete(self, test_db_session: Session):
        """Should cascade delete timezones when country is deleted."""
        country = Country(
            name_common="Brazil",
            name_official="Federative Republic of Brazil",
            iso_code_2="BR",
            iso_code_3="BRA",
            region="Americas",
            population=215313498,
        )
        timezone = Timezone(
            country=country,
            timezone_name="UTC-03:00",
        )

        test_db_session.add(country)
        test_db_session.add(timezone)
        test_db_session.commit()

        timezone_id = timezone.id

        test_db_session.delete(country)
        test_db_session.commit()

        deleted_timezone = test_db_session.query(Timezone).filter(Timezone.id == timezone_id).first()
        assert deleted_timezone is None

    def test_timezone_repr(self, test_db_session: Session):
        """Should have proper string representation."""
        timezone = Timezone(timezone_name="UTC-03:00")

        repr_str = repr(timezone)
        assert "Timezone" in repr_str
        assert "UTC-03:00" in repr_str


class TestCompleteCountryWithRelationships:
    """Integration tests for Country with all relationships."""

    def test_country_with_all_relationships(self, test_db_session: Session):
        """Should handle complete Country with languages, currencies, and timezones."""
        country = Country(
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
        )

        # Add relationships
        country.languages = [
            Language(language_code="por", language_name="Portuguese"),
        ]
        country.currencies = [
            Currency(currency_code="BRL", currency_name="Brazilian Real"),
        ]
        country.timezones = [
            Timezone(timezone_name="UTC-03:00"),
            Timezone(timezone_name="UTC-04:00"),
        ]

        test_db_session.add(country)
        test_db_session.commit()

        # Verify all relationships were saved
        assert country.id is not None
        assert len(country.languages) == 1
        assert len(country.currencies) == 1
        assert len(country.timezones) == 2

        # Verify data integrity
        assert country.languages[0].language_name == "Portuguese"
        assert country.currencies[0].currency_code == "BRL"
        assert "UTC-03:00" in [t.timezone_name for t in country.timezones]

    def test_query_country_with_relationships(self, test_db_session: Session):
        """Should query Country with all relationships loaded."""
        country = Country(
            name_common="France",
            name_official="French Republic",
            iso_code_2="FR",
            iso_code_3="FRA",
            region="Europe",
            population=67750000,
        )
        country.languages = [
            Language(language_code="fra", language_name="French"),
        ]
        country.currencies = [
            Currency(currency_code="EUR", currency_name="Euro"),
        ]

        test_db_session.add(country)
        test_db_session.commit()

        # Query back
        queried = test_db_session.query(Country).filter(Country.iso_code_2 == "FR").first()

        assert queried is not None
        assert queried.name_common == "France"
        assert len(queried.languages) == 1
        assert len(queried.currencies) == 1

    def test_multiple_countries(self, test_db_session: Session):
        """Should handle multiple countries without conflicts."""
        brazil = Country(
            name_common="Brazil",
            name_official="Federative Republic of Brazil",
            iso_code_2="BR",
            iso_code_3="BRA",
            region="Americas",
            population=215313498,
        )
        france = Country(
            name_common="France",
            name_official="French Republic",
            iso_code_2="FR",
            iso_code_3="FRA",
            region="Europe",
            population=67750000,
        )

        test_db_session.add_all([brazil, france])
        test_db_session.commit()

        countries = test_db_session.query(Country).all()
        assert len(countries) == 2

        names = {c.name_common for c in countries}
        assert "Brazil" in names
        assert "France" in names
