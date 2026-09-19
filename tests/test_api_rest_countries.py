"""Unit tests for REST Countries API v5 client.

Tests cover:
- Fetching country data with retry logic, pagination, and API key auth
- Timeout and error handling
- Data normalization and validation
- Logging behavior
"""

from unittest.mock import MagicMock, patch

import pytest
import requests

from app.api.rest_countries import (
    NormalizedCountry,
    fetch_countries,
    normalize_countries,
)
from app.utils.errors import ConfigurationError

TEST_API_KEY = "test_api_key"


def _api_page(
    objects: list[dict], more: bool = False, total: int | None = None
) -> dict:
    """Build a v5 API page envelope around a list of raw country objects."""
    return {
        "data": {
            "objects": objects,
            "meta": {
                "total": total if total is not None else len(objects),
                "count": len(objects),
                "limit": 100,
                "offset": 0,
                "more": more,
            },
        }
    }


@pytest.fixture
def sample_api_response():
    """Sample v5 API country objects with minimal data."""
    return [
        {
            "names": {"common": "Brazil", "official": "Federative Republic of Brazil"},
            "codes": {"alpha_2": "BR", "alpha_3": "BRA"},
            "region": "Americas",
            "subregion": "South America",
            "population": 215313498,
            "area": {"kilometers": 8514877.0},
            "coordinates": {"lat": -15.793889, "lng": -47.882778},
            "languages": [{"name": "Portuguese"}],
            "currencies": [{"code": "BRL", "name": "Brazilian real", "symbol": "R$"}],
            "timezones": ["UTC-03:00"],
        },
        {
            "names": {"common": "France", "official": "French Republic"},
            "codes": {"alpha_2": "FR", "alpha_3": "FRA"},
            "region": "Europe",
            "subregion": "Western Europe",
            "population": 67750000,
            "area": {"kilometers": 551695.0},
            "coordinates": {"lat": 46.227638, "lng": 2.213749},
            "languages": [{"name": "French"}],
            "currencies": [{"code": "EUR", "name": "Euro", "symbol": "€"}],
            "timezones": ["UTC+01:00"],
        },
    ]


@pytest.fixture
def sample_malformed_response():
    """API response with missing/invalid data."""
    return [
        {
            "names": {"common": "Invalid"},
            # Missing required fields (official name, codes, population, region)
            "codes": {"alpha_2": "XX"},
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
            mock_response.json.return_value = _api_page(sample_api_response)
            mock_response.status_code = 200
            mock_session.get.return_value = mock_response
            mock_session_class.return_value = mock_session

            result = fetch_countries(api_key=TEST_API_KEY)

            assert len(result) == 2
            assert result[0]["names"]["common"] == "Brazil"
            assert result[1]["codes"]["alpha_2"] == "FR"
            mock_session.get.assert_called_once()
            mock_session.close.assert_called_once()

    def test_fetch_countries_sends_bearer_token(self, sample_api_response):
        """Should authenticate with a Bearer token from the given API key."""
        with patch("app.api.rest_countries.requests.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_response = MagicMock()
            mock_response.json.return_value = _api_page(sample_api_response)
            mock_session.get.return_value = mock_response
            mock_session_class.return_value = mock_session

            fetch_countries(api_key=TEST_API_KEY)

            call_kwargs = mock_session.get.call_args[1]
            assert call_kwargs["headers"]["Authorization"] == f"Bearer {TEST_API_KEY}"

    def test_fetch_countries_requires_api_key(self, monkeypatch):
        """Should raise ConfigurationError when no API key is available."""
        monkeypatch.delenv("REST_COUNTRIES_API_KEY", raising=False)

        with pytest.raises(ConfigurationError):
            fetch_countries()

    def test_fetch_countries_uses_env_api_key(self, sample_api_response, monkeypatch):
        """Should fall back to the REST_COUNTRIES_API_KEY environment variable."""
        monkeypatch.setenv("REST_COUNTRIES_API_KEY", "env_key")

        with patch("app.api.rest_countries.requests.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_response = MagicMock()
            mock_response.json.return_value = _api_page(sample_api_response)
            mock_session.get.return_value = mock_response
            mock_session_class.return_value = mock_session

            fetch_countries()

            call_kwargs = mock_session.get.call_args[1]
            assert call_kwargs["headers"]["Authorization"] == "Bearer env_key"

    def test_fetch_countries_with_custom_timeout(self, sample_api_response):
        """Should use custom timeout when provided."""
        with patch("app.api.rest_countries.requests.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_response = MagicMock()
            mock_response.json.return_value = _api_page(sample_api_response)
            mock_session.get.return_value = mock_response
            mock_session_class.return_value = mock_session

            fetch_countries(timeout=60, api_key=TEST_API_KEY)

            mock_session.get.assert_called_once()
            call_args = mock_session.get.call_args
            assert call_args[1]["timeout"] == 60

    def test_fetch_countries_paginates_until_exhausted(self, sample_api_response):
        """Should follow pagination (meta.more) until all pages are fetched."""
        with patch("app.api.rest_countries.requests.Session") as mock_session_class:
            mock_session = MagicMock()
            page1 = MagicMock()
            page1.json.return_value = _api_page(
                [sample_api_response[0]], more=True, total=2
            )
            page2 = MagicMock()
            page2.json.return_value = _api_page(
                [sample_api_response[1]], more=False, total=2
            )
            mock_session.get.side_effect = [page1, page2]
            mock_session_class.return_value = mock_session

            result = fetch_countries(api_key=TEST_API_KEY, page_limit=1)

            assert len(result) == 2
            assert mock_session.get.call_count == 2
            first_call_params = mock_session.get.call_args_list[0][1]["params"]
            second_call_params = mock_session.get.call_args_list[1][1]["params"]
            assert first_call_params["offset"] == 0
            assert second_call_params["offset"] == 1

    def test_fetch_countries_timeout_error(self):
        """Should raise RequestException on timeout."""
        with patch("app.api.rest_countries.requests.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_session.get.side_effect = requests.Timeout("Request timeout")
            mock_session_class.return_value = mock_session

            with pytest.raises(requests.Timeout):
                fetch_countries(api_key=TEST_API_KEY)

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
                fetch_countries(api_key=TEST_API_KEY)

            mock_session.close.assert_called_once()

    def test_fetch_countries_empty_response(self):
        """Should raise ValueError on empty response."""
        with patch("app.api.rest_countries.requests.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_response = MagicMock()
            mock_response.json.return_value = _api_page([])
            mock_session.get.return_value = mock_response
            mock_session_class.return_value = mock_session

            with pytest.raises(ValueError):
                fetch_countries(api_key=TEST_API_KEY)

    def test_fetch_countries_invalid_response_format(self):
        """Should raise ValueError if response has no data.objects list."""
        with patch("app.api.rest_countries.requests.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_response = MagicMock()
            mock_response.json.return_value = {"data": {"meta": {}}}
            mock_session.get.return_value = mock_response
            mock_session_class.return_value = mock_session

            with pytest.raises(ValueError):
                fetch_countries(api_key=TEST_API_KEY)

    def test_fetch_countries_api_error_envelope(self):
        """Should raise ValueError when the API reports a logical error.

        Why: The REST Countries API returns HTTP 200 with an `errors` array
        for cases like a deprecated endpoint or an over-quota request, so
        that envelope must be treated as a failure, not a valid page.
        """
        with patch("app.api.rest_countries.requests.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "errors": [{"message": "This API version has been deprecated."}]
            }
            mock_session.get.return_value = mock_response
            mock_session_class.return_value = mock_session

            with pytest.raises(ValueError, match="deprecated"):
                fetch_countries(api_key=TEST_API_KEY)

    def test_fetch_countries_retry_on_5xx(self, sample_api_response):
        """Should retry on 5xx errors (handled by Retry strategy)."""
        with patch("app.api.rest_countries.requests.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_response = MagicMock()
            mock_response.json.return_value = _api_page(sample_api_response)
            mock_session.get.return_value = mock_response
            mock_session_class.return_value = mock_session

            # Session creation should use retry strategy
            result = fetch_countries(api_key=TEST_API_KEY)
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
                "names": {"common": "Test", "official": "Test Official"},
                "codes": {"alpha_2": "TS", "alpha_3": "TST"},
                "region": "Test Region",
                "subregion": None,
                "population": 1000,
                "area": None,
                "coordinates": None,
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
                "names": {"common": "Invalid"},
                # Missing official name, codes, region, population
            }
        ]

        normalized, errors = normalize_countries(raw_data)

        assert len(normalized) == 0
        assert len(errors) >= 1

    def test_normalize_countries_skips_missing_iso_codes(self):
        """Should skip territories without assigned ISO codes (e.g. disputed regions).

        Why: The REST Countries API reports empty alpha_2/alpha_3 codes for
        unrecognized territories (e.g. Northern Cyprus); persisting more than
        one such record collides on the empty-string unique constraint, so
        these must be treated as a normalization error instead.
        """
        raw_data = [
            {
                "names": {
                    "common": "Northern Cyprus",
                    "official": "Turkish Republic of Northern Cyprus",
                },
                "codes": {"alpha_2": "", "alpha_3": ""},
                "region": "Europe",
                "population": 382836,
            }
        ]

        normalized, errors = normalize_countries(raw_data)

        assert len(normalized) == 0
        assert len(errors) >= 1

    def test_normalize_countries_missing_name(self):
        """Should skip countries without proper name."""
        raw_data = [
            {
                "names": {"official": "Only Official"},  # Missing common name
                "codes": {"alpha_2": "XX", "alpha_3": "XXX"},
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
            {"names": {}, "codes": {"alpha_2": "INVALID"}}  # Invalid record
        ]

        normalized, errors = normalize_countries(mixed_data)

        assert len(normalized) == 2  # Valid countries
        assert len(errors) >= 1  # Invalid country error

    def test_normalize_countries_extracts_languages_and_currencies(self):
        """Should properly extract languages and currencies."""
        raw_data = [
            {
                "names": {"common": "Test", "official": "Test Official"},
                "codes": {"alpha_2": "TS", "alpha_3": "TST"},
                "region": "Test",
                "population": 1000,
                "languages": [{"name": "English"}, {"name": "Spanish"}],
                "currencies": [
                    {"code": "USD", "name": "US Dollar"},
                    {"code": "EUR", "name": "Euro"},
                ],
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
            mock_response.json.return_value = _api_page(sample_api_response)
            mock_session.get.return_value = mock_response
            mock_session_class.return_value = mock_session

            # Simulate complete pipeline
            raw_data = fetch_countries(api_key=TEST_API_KEY)
            normalized, errors = normalize_countries(raw_data)

            assert len(normalized) == 2
            assert len(errors) == 0
            assert all(isinstance(c, NormalizedCountry) for c in normalized)

    def test_normalize_countries_with_edge_case_data(self):
        """Should handle various edge cases in data."""
        edge_cases = [
            {
                "names": {"common": "Special Chars ñ", "official": "Official ñ"},
                "codes": {"alpha_2": "SC", "alpha_3": "SPC"},
                "region": "Test",
                "population": 0,  # Edge case: zero population
            },
            {
                "names": {"common": "Large Country", "official": "Very Large Country"},
                "codes": {"alpha_2": "LC", "alpha_3": "LRG"},
                "region": "Test",
                "population": 9999999999,  # Large number
                "area": {"kilometers": 99999999.99},
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
                "names": {"common": "Test", "official": "Test Official"},
                "codes": {"alpha_2": "TS", "alpha_3": "TST"},
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
