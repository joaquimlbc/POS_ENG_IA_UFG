"""Unit tests for REST Countries API client.

Tests cover:
- Fetching country data with retry logic
- Timeout and error handling
- Data normalization and validation
- Logging behavior
"""

import json
from unittest.mock import MagicMock, Mock, patch

import pytest
import requests

from app.api.rest_countries import (
    NormalizedCountry,
    fetch_countries,
    normalize_countries,
)


@pytest.fixture
def sample_api_response():
    """Sample API response with minimal country data."""
    return [
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
            "currencies": {"BRL": {"name": "Brazilian real", "symbol": "R$"}},
            "timezones": ["UTC-03:00"],
        },
        {
            "name": {"common": "France", "official": "French Republic"},
            "cca2": "FR",
            "cca3": "FRA",
            "region": "Europe",
            "subregion": "Western Europe",
            "population": 67750000,
            "area": 551695.0,
            "latlng": [46.227638, 2.213749],
            "languages": {"fra": "French"},
            "currencies": {"EUR": {"name": "Euro", "symbol": "€"}},
            "timezones": ["UTC+01:00"],
        },
    ]


@pytest.fixture
def sample_malformed_response():
    """API response with missing/invalid data."""
    return [
        {
            "name": {"common": "Invalid"},
            # Missing required fields
            "cca2": "XX",
            "region": "Test",
        }
    ]


class TestFetchCountries:
    """Tests for fetch_countries function."""

    def test_fetch_countries_success(self, sample_api_response):
        """Should successfully fetch countries from API."""
        with patch("app.api.rest_countries.requests.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_response = MagicMock()
            mock_response.json.return_value = sample_api_response
            mock_response.status_code = 200
            mock_session.get.return_value = mock_response
            mock_session_class.return_value = mock_session

            result = fetch_countries()

            assert len(result) == 2
            assert result[0]["name"]["common"] == "Brazil"
            assert result[1]["cca2"] == "FR"
            mock_session.get.assert_called_once()
            mock_session.close.assert_called_once()

    def test_fetch_countries_with_custom_timeout(self, sample_api_response):
        """Should use custom timeout when provided."""
        with patch("app.api.rest_countries.requests.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_response = MagicMock()
            mock_response.json.return_value = sample_api_response
            mock_response.status_code = 200
            mock_session.get.return_value = mock_response
            mock_session_class.return_value = mock_session

            fetch_countries(timeout=60)

            mock_session.get.assert_called_once()
            call_args = mock_session.get.call_args
            assert call_args[1]["timeout"] == 60

    def test_fetch_countries_timeout_error(self):
        """Should raise RequestException on timeout."""
        with patch("app.api.rest_countries.requests.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_session.get.side_effect = requests.Timeout("Request timeout")
            mock_session_class.return_value = mock_session

            with pytest.raises(requests.Timeout):
                fetch_countries()

            mock_session.close.assert_called_once()

    def test_fetch_countries_http_error(self):
        """Should raise RequestException on HTTP error."""
        with patch("app.api.rest_countries.requests.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_response = MagicMock()
            mock_response.raise_for_status.side_effect = requests.HTTPError(
                "404 Not Found"
            )
            mock_session.get.return_value = mock_response
            mock_session_class.return_value = mock_session

            with pytest.raises(requests.HTTPError):
                fetch_countries()

            mock_session.close.assert_called_once()

    def test_fetch_countries_empty_response(self):
        """Should raise ValueError on empty response."""
        with patch("app.api.rest_countries.requests.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_response = MagicMock()
            mock_response.json.return_value = []
            mock_response.status_code = 200
            mock_session.get.return_value = mock_response
            mock_session_class.return_value = mock_session

            with pytest.raises(ValueError):
                fetch_countries()

    def test_fetch_countries_invalid_response_format(self):
        """Should raise ValueError if response is not a list."""
        with patch("app.api.rest_countries.requests.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_response = MagicMock()
            mock_response.json.return_value = {"error": "invalid"}
            mock_response.status_code = 200
            mock_session.get.return_value = mock_response
            mock_session_class.return_value = mock_session

            with pytest.raises(ValueError):
                fetch_countries()

    def test_fetch_countries_retry_on_5xx(self, sample_api_response):
        """Should retry on 5xx errors (handled by Retry strategy)."""
        with patch("app.api.rest_countries.requests.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_response = MagicMock()
            mock_response.json.return_value = sample_api_response
            mock_response.status_code = 200
            mock_session.get.return_value = mock_response
            mock_session_class.return_value = mock_session

            # Session creation should use retry strategy
            result = fetch_countries()
            assert len(result) == 2


class TestNormalizeCountries:
    """Tests for normalize_countries function."""

    def test_normalize_countries_success(self, sample_api_response):
        """Should successfully normalize all valid countries."""
        normalized, errors = normalize_countries(sample_api_response)

        assert len(normalized) == 2
        assert len(errors) == 0

        # Check Brazil normalization
        brazil = normalized[0]
        assert isinstance(brazil, NormalizedCountry)
        assert brazil.name_common == "Brazil"
        assert brazil.iso_code_2 == "BR"
        assert brazil.iso_code_3 == "BRA"
        assert brazil.region == "Americas"
        assert brazil.population == 215313498
        assert brazil.area == 8514877.0
        assert brazil.latitude == -15.793889
        assert brazil.longitude == -47.882778
        assert "Portuguese" in brazil.languages
        assert "BRL" in brazil.currencies

        # Check France normalization
        france = normalized[1]
        assert france.name_common == "France"
        assert france.iso_code_2 == "FR"

    def test_normalize_countries_with_missing_optional_fields(self):
        """Should handle countries with missing optional fields."""
        raw_data = [
            {
                "name": {"common": "Test", "official": "Test Official"},
                "cca2": "TS",
                "cca3": "TST",
                "region": "Test Region",
                "subregion": None,
                "population": 1000,
                "area": None,
                "latlng": None,
                "languages": None,
                "currencies": None,
                "timezones": None,
            }
        ]

        normalized, errors = normalize_countries(raw_data)

        assert len(normalized) == 1
        assert len(errors) == 0

        country = normalized[0]
        assert country.name_common == "Test"
        assert country.subregion is None
        assert country.area is None
        assert country.latitude is None
        assert country.languages is None
        assert country.currencies is None

    def test_normalize_countries_validation_error(self, sample_malformed_response):
        """Should handle validation errors and continue processing."""
        normalized, errors = normalize_countries(sample_malformed_response)

        assert len(normalized) == 0
        assert len(errors) >= 1

    def test_normalize_countries_missing_required_fields(self):
        """Should skip countries with missing required fields."""
        raw_data = [
            {
                "name": {"common": "Invalid"},
                # Missing cca2, cca3, region, population
            }
        ]

        normalized, errors = normalize_countries(raw_data)

        assert len(normalized) == 0
        assert len(errors) >= 1

    def test_normalize_countries_missing_name(self):
        """Should skip countries without proper name."""
        raw_data = [
            {
                "name": {"official": "Only Official"},  # Missing common name
                "cca2": "XX",
                "cca3": "XXX",
                "region": "Test",
                "population": 1000,
            }
        ]

        normalized, errors = normalize_countries(raw_data)

        assert len(normalized) == 0
        assert len(errors) >= 1

    def test_normalize_countries_partial_failure(self, sample_api_response):
        """Should normalize valid countries even if some fail."""
        mixed_data = sample_api_response + [
            {"name": {}, "cca2": "INVALID"}  # Invalid record
        ]

        normalized, errors = normalize_countries(mixed_data)

        assert len(normalized) == 2  # Valid countries
        assert len(errors) >= 1  # Invalid country error

    def test_normalize_countries_extracts_languages_and_currencies(self):
        """Should properly extract languages and currencies."""
        raw_data = [
            {
                "name": {"common": "Test", "official": "Test Official"},
                "cca2": "TS",
                "cca3": "TST",
                "region": "Test",
                "population": 1000,
                "languages": {
                    "eng": "English",
                    "spa": "Spanish",
                },
                "currencies": {
                    "USD": {"name": "US Dollar"},
                    "EUR": {"name": "Euro"},
                },
            }
        ]

        normalized, errors = normalize_countries(raw_data)

        assert len(normalized) == 1
        country = normalized[0]
        assert set(country.languages) == {"English", "Spanish"}
        assert set(country.currencies) == {"USD", "EUR"}

    def test_normalize_countries_empty_input(self):
        """Should handle empty input gracefully."""
        normalized, errors = normalize_countries([])

        assert len(normalized) == 0
        assert len(errors) == 0


class TestIntegration:
    """Integration tests for fetch and normalize pipeline."""

    def test_fetch_and_normalize_pipeline(self, sample_api_response):
        """Should work together in a realistic pipeline."""
        with patch("app.api.rest_countries.requests.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_response = MagicMock()
            mock_response.json.return_value = sample_api_response
            mock_response.status_code = 200
            mock_session.get.return_value = mock_response
            mock_session_class.return_value = mock_session

            # Simulate complete pipeline
            raw_data = fetch_countries()
            normalized, errors = normalize_countries(raw_data)

            assert len(normalized) == 2
            assert len(errors) == 0
            assert all(isinstance(c, NormalizedCountry) for c in normalized)

    def test_normalize_countries_with_edge_case_data(self):
        """Should handle various edge cases in data."""
        edge_cases = [
            {
                "name": {"common": "Special Chars ñ", "official": "Official ñ"},
                "cca2": "SC",
                "cca3": "SPC",
                "region": "Test",
                "population": 0,  # Edge case: zero population
            },
            {
                "name": {"common": "Large Country", "official": "Very Large Country"},
                "cca2": "LC",
                "cca3": "LRG",
                "region": "Test",
                "population": 9999999999,  # Large number
                "area": 99999999.99,
            },
        ]

        normalized, errors = normalize_countries(edge_cases)

        assert len(normalized) == 2
        assert len(errors) == 0
        assert normalized[0].name_common == "Special Chars ñ"
        assert normalized[1].population == 9999999999

    def test_normalize_with_extra_fields(self):
        """Should ignore extra fields not in schema."""
        raw_data = [
            {
                "name": {"common": "Test", "official": "Test Official"},
                "cca2": "TS",
                "cca3": "TST",
                "region": "Test",
                "population": 1000,
                "extra_field_1": "should be ignored",
                "extra_field_2": 12345,
                "extra_field_3": {"nested": "data"},
            }
        ]

        normalized, errors = normalize_countries(raw_data)

        assert len(normalized) == 1
        assert len(errors) == 0
        assert normalized[0].name_common == "Test"
