"""Integration tests for API endpoints not covered by test_api_endpoints.py.

Priority: ALTO (US-022)
Covers: ISO lookup, relationship endpoints (languages/currencies/timezones),
statistics/regions/data-gaps/validate, and the router-level health check -
none of which had any test coverage before this file.
"""

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.models.task import CountryCreate
from app.service.country_service import CountryService
from app.utils.errors import DuplicateRecordError, ValidationError


def _create_brazil(session) -> int:
    """Helper: persist a sample country and return its id."""
    service = CountryService(session)
    country = service.create_country(
        CountryCreate(
            name_common="Brazil",
            name_official="Federative Republic of Brazil",
            iso_code_2="BR",
            iso_code_3="BRA",
            region="Americas",
            population=215313498,
        )
    )
    return country.id


class TestGetCountryByIso:
    """Tests for GET /api/v1/countries/iso/{iso_code}."""

    def test_lookup_by_iso2_returns_200(
        self, api_client: TestClient, in_memory_session
    ) -> None:
        """Verify a country can be looked up by its ISO2 code."""
        _create_brazil(in_memory_session)

        response = api_client.get("/api/v1/countries/iso/BR")

        assert response.status_code == 200
        assert response.json()["name_common"] == "Brazil"

    def test_lookup_by_iso3_returns_200(
        self, api_client: TestClient, in_memory_session
    ) -> None:
        """Verify a country can be looked up by its ISO3 code."""
        _create_brazil(in_memory_session)

        response = api_client.get("/api/v1/countries/iso/BRA")

        assert response.status_code == 200
        assert response.json()["iso_code_2"] == "BR"

    def test_lookup_unknown_code_returns_404(self, api_client: TestClient) -> None:
        """Verify an unrecognized ISO code returns 404."""
        response = api_client.get("/api/v1/countries/iso/ZZ")

        assert response.status_code == 404

    def test_lookup_is_case_insensitive(
        self, api_client: TestClient, in_memory_session
    ) -> None:
        """Verify lowercase ISO codes are normalized before lookup."""
        _create_brazil(in_memory_session)

        response = api_client.get("/api/v1/countries/iso/br")

        assert response.status_code == 200


class TestRelationshipEndpoints:
    """Tests for POST .../languages, .../currencies, .../timezones."""

    def test_add_languages_returns_201_with_updated_country(
        self, api_client: TestClient, in_memory_session
    ) -> None:
        """Verify languages are added and returned in the detail response."""
        country_id = _create_brazil(in_memory_session)

        response = api_client.post(
            f"/api/v1/countries/{country_id}/languages",
            json=[{"language_code": "PT", "language_name": "Portuguese"}],
        )

        assert response.status_code == 201
        languages = response.json()["languages"]
        assert any(lang["language_name"] == "Portuguese" for lang in languages)

    def test_add_languages_to_missing_country_returns_404(
        self, api_client: TestClient
    ) -> None:
        """Verify adding languages to a nonexistent country returns 404."""
        response = api_client.post(
            "/api/v1/countries/9999/languages",
            json=[{"language_code": "PT", "language_name": "Portuguese"}],
        )

        assert response.status_code == 404

    def test_add_currencies_returns_201_with_updated_country(
        self, api_client: TestClient, in_memory_session
    ) -> None:
        """Verify currencies are added and returned in the detail response."""
        country_id = _create_brazil(in_memory_session)

        response = api_client.post(
            f"/api/v1/countries/{country_id}/currencies",
            json=[{"currency_code": "BRL", "currency_name": "Brazilian Real"}],
        )

        assert response.status_code == 201
        currencies = response.json()["currencies"]
        assert any(cur["currency_code"] == "BRL" for cur in currencies)

    def test_add_currencies_to_missing_country_returns_404(
        self, api_client: TestClient
    ) -> None:
        """Verify adding currencies to a nonexistent country returns 404."""
        response = api_client.post(
            "/api/v1/countries/9999/currencies",
            json=[{"currency_code": "BRL", "currency_name": "Brazilian Real"}],
        )

        assert response.status_code == 404

    def test_add_timezones_returns_201_with_updated_country(
        self, api_client: TestClient, in_memory_session
    ) -> None:
        """Verify timezones are added and returned in the detail response."""
        country_id = _create_brazil(in_memory_session)

        response = api_client.post(
            f"/api/v1/countries/{country_id}/timezones",
            json=[{"timezone_name": "America/Sao_Paulo"}],
        )

        assert response.status_code == 201
        timezones = response.json()["timezones"]
        assert any(tz["timezone_name"] == "America/Sao_Paulo" for tz in timezones)

    def test_add_timezones_to_missing_country_returns_404(
        self, api_client: TestClient
    ) -> None:
        """Verify adding timezones to a nonexistent country returns 404."""
        response = api_client.post(
            "/api/v1/countries/9999/timezones",
            json=[{"timezone_name": "America/Sao_Paulo"}],
        )

        assert response.status_code == 404


class TestStatisticsAndAnalyticsEndpoints:
    """Tests for GET /statistics, /regions, /data-gaps, .../validate."""

    def test_get_statistics_returns_200_with_expected_shape(
        self, api_client: TestClient, in_memory_session
    ) -> None:
        """Verify global statistics include totals and a regional breakdown."""
        _create_brazil(in_memory_session)

        response = api_client.get("/api/v1/statistics")
        body = response.json()

        assert response.status_code == 200
        assert body["total_countries"] == 1
        assert body["total_population"] == 215313498
        assert "regions" in body

    def test_get_statistics_on_empty_database(self, api_client: TestClient) -> None:
        """Verify statistics degrade gracefully with zero countries."""
        response = api_client.get("/api/v1/statistics")
        body = response.json()

        assert response.status_code == 200
        assert body["total_countries"] == 0

    def test_get_regions_returns_200_with_breakdown(
        self, api_client: TestClient, in_memory_session
    ) -> None:
        """Verify the regional breakdown lists the seeded region."""
        _create_brazil(in_memory_session)

        response = api_client.get("/api/v1/regions")
        body = response.json()

        assert response.status_code == 200
        assert any(r["region"] == "Americas" for r in body)

    def test_get_data_gaps_returns_200(
        self, api_client: TestClient, in_memory_session
    ) -> None:
        """Verify the data-gaps report responds successfully."""
        _create_brazil(in_memory_session)

        response = api_client.get("/api/v1/data-gaps")
        body = response.json()

        assert response.status_code == 200
        assert "total_countries" in body

    def test_validate_country_returns_200_with_quality_report(
        self, api_client: TestClient, in_memory_session
    ) -> None:
        """Verify the quality-validation report includes a score and level."""
        country_id = _create_brazil(in_memory_session)

        response = api_client.get(f"/api/v1/countries/{country_id}/validate")
        body = response.json()

        assert response.status_code == 200
        assert "quality_score" in body
        assert "quality_level" in body

    def test_validate_missing_country_returns_404(self, api_client: TestClient) -> None:
        """Verify validating a nonexistent country returns 404."""
        response = api_client.get("/api/v1/countries/9999/validate")

        assert response.status_code == 404


class TestRouterLevelHealthCheck:
    """Tests for GET /api/v1/health (distinct from the app-level /health)."""

    def test_router_health_check_returns_200(self, api_client: TestClient) -> None:
        """Verify the versioned health endpoint responds with the same schema."""
        response = api_client.get("/api/v1/health")
        body = response.json()

        assert response.status_code == 200
        assert body["status"] == "ok"
        assert "version" in body
        assert "timestamp" in body


class TestUnexpectedErrorsSurfaceAs500:
    """Every endpoint's catch-all `except Exception` -> 500 branch.

    Why: Each route has a safety net against unanticipated failures (a
    corrupt row, a driver error) mapping any non-domain exception to a
    generic 500 rather than leaking internals. These are deliberately
    generic (RuntimeError, not a domain error) to simulate exactly that
    "unanticipated" case, and cover the branch regardless of whether
    today's business logic can trigger it for real.
    """

    def test_create_country_internal_error_returns_500(
        self, api_client: TestClient
    ) -> None:
        with patch.object(
            CountryService, "create_country", side_effect=RuntimeError("boom")
        ):
            response = api_client.post(
                "/api/v1/countries",
                json={
                    "name_common": "Testland",
                    "name_official": "Republic of Testland",
                    "iso_code_2": "TL",
                    "iso_code_3": "TLD",
                    "region": "Europe",
                    "population": 1000,
                },
            )

        assert response.status_code == 500

    def test_list_countries_internal_error_returns_500(
        self, api_client: TestClient
    ) -> None:
        with patch.object(
            CountryService, "list_countries", side_effect=RuntimeError("boom")
        ):
            response = api_client.get("/api/v1/countries")

        assert response.status_code == 500

    def test_get_country_internal_error_returns_500(
        self, api_client: TestClient
    ) -> None:
        with patch.object(
            CountryService, "get_country", side_effect=RuntimeError("boom")
        ):
            response = api_client.get("/api/v1/countries/1")

        assert response.status_code == 500

    def test_get_country_by_iso_internal_error_returns_500(
        self, api_client: TestClient
    ) -> None:
        with patch.object(
            CountryService, "get_country_by_iso", side_effect=RuntimeError("boom")
        ):
            response = api_client.get("/api/v1/countries/iso/BR")

        assert response.status_code == 500

    def test_update_country_internal_error_returns_500(
        self, api_client: TestClient
    ) -> None:
        with patch.object(
            CountryService, "update_country", side_effect=RuntimeError("boom")
        ):
            response = api_client.put("/api/v1/countries/1", json={})

        assert response.status_code == 500

    def test_add_languages_internal_error_returns_500(
        self, api_client: TestClient
    ) -> None:
        with patch.object(
            CountryService, "add_languages", side_effect=RuntimeError("boom")
        ):
            response = api_client.post(
                "/api/v1/countries/1/languages",
                json=[{"language_code": "PT", "language_name": "Portuguese"}],
            )

        assert response.status_code == 500

    def test_add_currencies_internal_error_returns_500(
        self, api_client: TestClient
    ) -> None:
        with patch.object(
            CountryService, "add_currencies", side_effect=RuntimeError("boom")
        ):
            response = api_client.post(
                "/api/v1/countries/1/currencies",
                json=[{"currency_code": "BRL", "currency_name": "Brazilian Real"}],
            )

        assert response.status_code == 500

    def test_add_timezones_internal_error_returns_500(
        self, api_client: TestClient
    ) -> None:
        with patch.object(
            CountryService, "add_timezones", side_effect=RuntimeError("boom")
        ):
            response = api_client.post(
                "/api/v1/countries/1/timezones",
                json=[{"timezone_name": "America/Sao_Paulo"}],
            )

        assert response.status_code == 500

    def test_trigger_sync_internal_error_returns_500(
        self, api_client: TestClient
    ) -> None:
        """Verify a pipeline failure (e.g. REST Countries API unreachable) is a 500."""
        with patch(
            "app.api.country_routes.ingest_countries",
            side_effect=RuntimeError("REST Countries API unreachable"),
        ):
            response = api_client.post("/api/v1/sync")

        assert response.status_code == 500

    def test_get_statistics_internal_error_returns_500(
        self, api_client: TestClient
    ) -> None:
        with patch.object(
            CountryService,
            "get_global_statistics",
            side_effect=RuntimeError("boom"),
        ):
            response = api_client.get("/api/v1/statistics")

        assert response.status_code == 500

    def test_get_regions_internal_error_returns_500(
        self, api_client: TestClient
    ) -> None:
        with patch.object(
            CountryService, "get_regional_breakdown", side_effect=RuntimeError("boom")
        ):
            response = api_client.get("/api/v1/regions")

        assert response.status_code == 500

    def test_analyze_data_gaps_internal_error_returns_500(
        self, api_client: TestClient
    ) -> None:
        with patch.object(
            CountryService, "identify_data_gaps", side_effect=RuntimeError("boom")
        ):
            response = api_client.get("/api/v1/data-gaps")

        assert response.status_code == 500

    def test_validate_country_internal_error_returns_500(
        self, api_client: TestClient
    ) -> None:
        with patch.object(
            CountryService,
            "validate_country_integrity",
            side_effect=RuntimeError("boom"),
        ):
            response = api_client.get("/api/v1/countries/1/validate")

        assert response.status_code == 500


class TestValidationErrorBranchesReturn422:
    """The `except ValidationError` -> 422 branch on every endpoint that has one.

    Why: None of today's service methods actually raise ValidationError
    from these particular call sites (it's currently only raised by
    sync_countries_batch's batch-size check), so these branches are
    unreachable through real business logic yet - but the route contract
    (a documented 422 response) must still hold if a future validation
    rule starts raising it here. Mocked at the service boundary to pin
    that contract now, ahead of the logic existing.
    """

    def test_create_country_validation_error_returns_422(
        self, api_client: TestClient
    ) -> None:
        with patch.object(
            CountryService,
            "create_country",
            side_effect=ValidationError("region", "invalid region"),
        ):
            response = api_client.post(
                "/api/v1/countries",
                json={
                    "name_common": "Testland",
                    "name_official": "Republic of Testland",
                    "iso_code_2": "TL",
                    "iso_code_3": "TLD",
                    "region": "Europe",
                    "population": 1000,
                },
            )

        assert response.status_code == 422

    def test_list_countries_validation_error_returns_422(
        self, api_client: TestClient
    ) -> None:
        with patch.object(
            CountryService,
            "list_countries",
            side_effect=ValidationError("page", "invalid page"),
        ):
            response = api_client.get("/api/v1/countries")

        assert response.status_code == 422

    def test_update_country_validation_error_returns_422(
        self, api_client: TestClient
    ) -> None:
        with patch.object(
            CountryService,
            "update_country",
            side_effect=ValidationError("population", "invalid population"),
        ):
            response = api_client.put("/api/v1/countries/1", json={})

        assert response.status_code == 422

    def test_add_languages_validation_error_returns_422(
        self, api_client: TestClient
    ) -> None:
        with patch.object(
            CountryService,
            "add_languages",
            side_effect=ValidationError("language_code", "invalid code"),
        ):
            response = api_client.post(
                "/api/v1/countries/1/languages",
                json=[{"language_code": "PT", "language_name": "Portuguese"}],
            )

        assert response.status_code == 422

    def test_add_currencies_validation_error_returns_422(
        self, api_client: TestClient
    ) -> None:
        with patch.object(
            CountryService,
            "add_currencies",
            side_effect=ValidationError("currency_code", "invalid code"),
        ):
            response = api_client.post(
                "/api/v1/countries/1/currencies",
                json=[{"currency_code": "BRL", "currency_name": "Brazilian Real"}],
            )

        assert response.status_code == 422

    def test_add_timezones_validation_error_returns_422(
        self, api_client: TestClient
    ) -> None:
        with patch.object(
            CountryService,
            "add_timezones",
            side_effect=ValidationError("timezone_name", "invalid timezone"),
        ):
            response = api_client.post(
                "/api/v1/countries/1/timezones",
                json=[{"timezone_name": "America/Sao_Paulo"}],
            )

        assert response.status_code == 422


class TestUpdateCountryDuplicateRecordErrorReturns409:
    """The `except DuplicateRecordError` -> 409 branch on PUT /countries/{id}.

    Why: update_country never raises DuplicateRecordError through today's
    business logic (CountryUpdate excludes ISO code fields, the only
    uniqueness constraint), so this branch is currently unreachable via a
    real request - mocked to pin the route's documented 409 contract.
    """

    def test_update_country_duplicate_returns_409(self, api_client: TestClient) -> None:
        with patch.object(
            CountryService,
            "update_country",
            side_effect=DuplicateRecordError("Country", "iso_code_2", "BR"),
        ):
            response = api_client.put("/api/v1/countries/1", json={})

        assert response.status_code == 409
