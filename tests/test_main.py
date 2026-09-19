"""Tests for app-level FastAPI concerns: health check, root, docs, CORS.

Priority: ALTO (US-022)
Covers what US-011 (health check) and US-010 (FastAPI setup) promise at the
application level, distinct from the resource-level tests in
tests/integration/test_api_endpoints.py.
"""

from fastapi.testclient import TestClient

from app.main import app


class TestHealthCheck:
    """Tests for GET /health."""

    def test_health_check_returns_200(self, api_client: TestClient) -> None:
        """Verify the health check endpoint is reachable and returns 200 OK."""
        response = api_client.get("/health")

        assert response.status_code == 200

    def test_health_check_response_schema(self, api_client: TestClient) -> None:
        """Verify the health check payload matches the documented schema.

        Why: Orchestrators (Kubernetes, Docker) parse this response; a
        missing or renamed field silently breaks liveness/readiness probes.
        """
        response = api_client.get("/health")
        body = response.json()

        assert set(body.keys()) == {"status", "version", "timestamp"}
        assert body["status"] == "ok"
        assert body["version"] == "1.0.0"

    def test_health_check_timestamp_is_iso8601_utc(
        self, api_client: TestClient
    ) -> None:
        """Verify the timestamp field is a parseable ISO-8601 UTC datetime."""
        from datetime import datetime

        response = api_client.get("/health")
        timestamp = response.json()["timestamp"]

        parsed = datetime.fromisoformat(timestamp)
        assert parsed.tzinfo is not None

    def test_health_check_does_not_require_database(self) -> None:
        """Verify /health responds even without a database dependency override.

        Why: A health check that touches the database can report the app as
        down when only the DB is briefly unavailable - it must be a pure
        liveness signal.
        """
        client = TestClient(app)

        response = client.get("/health")

        assert response.status_code == 200


class TestRootEndpoint:
    """Tests for GET /."""

    def test_root_returns_200(self, api_client: TestClient) -> None:
        """Verify the root endpoint responds successfully."""
        response = api_client.get("/")

        assert response.status_code == 200

    def test_root_returns_welcome_message(self, api_client: TestClient) -> None:
        """Verify the root endpoint returns a welcome/info payload."""
        response = api_client.get("/")

        assert "message" in response.json()


class TestOpenAPIDocumentation:
    """Tests for auto-generated OpenAPI/Swagger documentation (US-013)."""

    def test_swagger_ui_available(self, api_client: TestClient) -> None:
        """Verify Swagger UI is served at /docs."""
        response = api_client.get("/docs")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_redoc_available(self, api_client: TestClient) -> None:
        """Verify ReDoc is served at /redoc."""
        response = api_client.get("/redoc")

        assert response.status_code == 200

    def test_openapi_schema_available(self, api_client: TestClient) -> None:
        """Verify the raw OpenAPI schema is served and well-formed."""
        response = api_client.get("/openapi.json")
        schema = response.json()

        assert response.status_code == 200
        assert schema["info"]["title"] == "REST Countries API"
        assert schema["info"]["version"] == "1.0.0"

    def test_health_route_documented_in_openapi(self, api_client: TestClient) -> None:
        """Verify /health appears in the generated OpenAPI schema."""
        schema = api_client.get("/openapi.json").json()

        assert "/health" in schema["paths"]


class TestCORSConfiguration:
    """Tests for CORS middleware (US-010)."""

    def test_cors_headers_present_on_allowed_origin(
        self, api_client: TestClient
    ) -> None:
        """Verify CORS headers are returned for a configured origin."""
        response = api_client.get(
            "/health", headers={"Origin": "http://localhost:8501"}
        )

        assert (
            response.headers.get("access-control-allow-origin")
            == "http://localhost:8501"
        )

    def test_cors_preflight_request_allowed(self, api_client: TestClient) -> None:
        """Verify an OPTIONS preflight request from a known origin succeeds."""
        response = api_client.options(
            "/health",
            headers={
                "Origin": "http://localhost:8501",
                "Access-Control-Request-Method": "GET",
            },
        )

        assert response.status_code == 200
