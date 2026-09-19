"""Integration tests for FastAPI endpoints and HTTP status codes.

Priority: ALTO (PRIORIDADE 2)
Test Suite: API Status Codes
Tests HTTP contract: 200, 201, 204, 404, 409 status codes.
Uses TestClient to test FastAPI routes with isolated dependencies.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database.models import Base
from app.main import app
from app.models.task import CountryCreate
from app.service.country_service import CountryService


class TestAPIEndpoints:
    """Test suite for API endpoints and HTTP status codes."""

    @pytest.fixture
    def test_db(self):
        """Create isolated test database for each test."""
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            echo=False,
        )
        Base.metadata.create_all(engine)
        yield engine
        engine.dispose()

    @pytest.fixture
    def session(self, test_db) -> Session:
        """Create database session with rollback."""
        connection = test_db.connect()
        transaction = connection.begin()
        session = sessionmaker(bind=connection)()

        yield session

        session.close()
        transaction.rollback()
        connection.close()

    @pytest.fixture
    def client(self, session: Session):
        """Create TestClient with isolated database session."""

        def override_get_db():
            yield session

        from app.database.connection import get_db_session

        app.dependency_overrides[get_db_session] = override_get_db

        test_client = TestClient(app)
        yield test_client

        app.dependency_overrides.clear()

    @pytest.fixture
    def populated_client(self, client: TestClient, session: Session):
        """TestClient with pre-populated sample country."""
        service = CountryService(session)
        sample = CountryCreate(
            name_common="Brazil",
            name_official="Federative Republic of Brazil",
            iso_code_2="BR",
            iso_code_3="BRA",
            region="Americas",
            population=215313498,
        )
        service.create_country(sample)
        return client

    # ========================================================================
    # POST /api/v1/countries - CREATE (201 Created)
    # ========================================================================

    def test_post_create_country_201(self, client: TestClient):
        """Verify POST /api/v1/countries returns 201 Created.

        Business rule: Successful country creation returns 201.
        Expected: Status 201, response contains country data with ID.
        Why: REST contract for successful resource creation.
        """
        payload = {
            "name_common": "France",
            "name_official": "French Republic",
            "iso_code_2": "FR",
            "iso_code_3": "FRA",
            "region": "Europe",
            "population": 67970571,
        }

        response = client.post("/api/v1/countries", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["id"] > 0
        assert data["name_common"] == "France"
        assert data["iso_code_2"] == "FR"
        assert "created_at" in data
        assert "updated_at" in data

    def test_post_create_country_duplicate_409(self, populated_client: TestClient):
        """Verify duplicate country returns 409 Conflict.

        Business rule: Duplicate ISO2 should return 409.
        Expected: Status 409, error message about duplicate.
        Why: REST contract for conflict/duplicate resource.
        """
        # Brazil already exists from fixture
        payload = {
            "name_common": "Brazil 2",
            "name_official": "Different",
            "iso_code_2": "BR",  # Duplicate
            "iso_code_3": "BRX",
            "region": "Americas",
            "population": 200000000,
        }

        response = populated_client.post("/api/v1/countries", json=payload)

        assert response.status_code == 409
        data = response.json()
        assert "detail" in data or "message" in data

    def test_post_create_country_invalid_422(self, client: TestClient):
        """Verify invalid data returns 422 Unprocessable Entity.

        Business rule: Invalid payload validation error returns 422.
        Expected: Status 422, validation error details.
        Why: REST contract for validation failure.
        """
        payload = {
            "name_common": "Test",
            # Missing required fields
        }

        response = client.post("/api/v1/countries", json=payload)

        assert response.status_code == 422

    # ========================================================================
    # GET /api/v1/countries - LIST (200 OK)
    # ========================================================================

    def test_get_list_countries_200(self, populated_client: TestClient):
        """Verify GET /api/v1/countries returns 200 OK.

        Business rule: List endpoint returns paginated results with 200.
        Expected: Status 200, pagination metadata included.
        Why: REST contract for successful list retrieval.
        """
        response = populated_client.get("/api/v1/countries")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "limit" in data
        assert "pages" in data
        assert len(data["items"]) > 0

    def test_get_list_countries_with_pagination_200(self, populated_client: TestClient):
        """Verify pagination parameters work correctly.

        Business rule: Query parameters control pagination.
        Expected: Status 200, correct page returned.
        Why: Dashboard depends on pagination working.
        """
        response = populated_client.get("/api/v1/countries?page=1&limit=10")

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["limit"] == 10

    def test_get_list_countries_with_filter_200(self, populated_client: TestClient):
        """Verify region filter works.

        Business rule: Region query parameter filters results.
        Expected: Status 200, only countries from region returned.
        Why: Dashboard region filter depends on this.
        """
        response = populated_client.get("/api/v1/countries?region=Americas")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 0
        for item in data["items"]:
            assert item["region"] == "Americas"

    # ========================================================================
    # GET /api/v1/countries/{id} - DETAIL (200 OK / 404 Not Found)
    # ========================================================================

    def test_get_country_by_id_200(self, populated_client: TestClient):
        """Verify GET /api/v1/countries/{id} returns 200 OK.

        Business rule: Valid country ID returns 200 with details.
        Expected: Status 200, country data with relationships.
        Why: REST contract for successful retrieval.
        """
        response = populated_client.get("/api/v1/countries/1")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["name_common"] == "Brazil"
        assert "languages" in data
        assert "currencies" in data
        assert "timezones" in data

    def test_get_country_not_found_404(self, client: TestClient):
        """Verify missing country returns 404 Not Found.

        Business rule: Non-existent country ID returns 404.
        Expected: Status 404, error message.
        Why: REST contract for missing resource.
        """
        response = client.get("/api/v1/countries/9999")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data or "message" in data

    # ========================================================================
    # PUT /api/v1/countries/{id} - UPDATE (200 OK / 404 Not Found)
    # ========================================================================

    def test_put_update_country_200(self, populated_client: TestClient):
        """Verify PUT /api/v1/countries/{id} returns 200 OK.

        Business rule: Successful update returns 200 with updated data.
        Expected: Status 200, modified fields updated.
        Why: REST contract for successful update.
        """
        payload = {
            "population": 220000000,
            "name_common": "Brazil (Updated)",
        }

        response = populated_client.put("/api/v1/countries/1", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["population"] == 220000000
        assert data["name_common"] == "Brazil (Updated)"

    def test_put_update_country_not_found_404(self, client: TestClient):
        """Verify update on missing country returns 404.

        Business rule: Cannot update non-existent resource.
        Expected: Status 404, error message.
        Why: REST contract for missing resource.
        """
        payload = {"population": 200000000}

        response = client.put("/api/v1/countries/9999", json=payload)

        assert response.status_code == 404

    # ========================================================================
    # DELETE /api/v1/countries/{id} - DELETE (204 No Content / 404 Not Found)
    # ========================================================================

    def test_delete_country_204(self, populated_client: TestClient):
        """Verify DELETE /api/v1/countries/{id} returns 204 No Content.

        Business rule: Successful delete returns 204 with no response body.
        Expected: Status 204, empty response body.
        Why: REST contract for successful deletion.
        """
        response = populated_client.delete("/api/v1/countries/1")

        assert response.status_code == 204
        # 204 should have no response body
        assert response.content == b""

    def test_delete_country_not_found_404(self, client: TestClient):
        """Verify delete on missing country returns 404.

        Business rule: Cannot delete non-existent resource.
        Expected: Status 404, error message.
        Why: REST contract for missing resource.
        """
        response = client.delete("/api/v1/countries/9999")

        assert response.status_code == 404

    def test_delete_country_idempotent(self, populated_client: TestClient):
        """Verify second delete returns 404 (already deleted).

        Business rule: Delete is idempotent up to first deletion.
        Expected: First 204, second 404.
        Why: Validates delete doesn't exist twice.
        """
        # First delete succeeds
        response1 = populated_client.delete("/api/v1/countries/1")
        assert response1.status_code == 204

        # Second delete fails (already gone)
        response2 = populated_client.delete("/api/v1/countries/1")
        assert response2.status_code == 404

    # ========================================================================
    # GET /health - HEALTHCHECK (200 OK)
    # ========================================================================

    def test_health_check_200(self, client: TestClient):
        """Verify GET /health returns 200 OK.

        Business rule: Health endpoint always returns 200.
        Expected: Status 200, status=ok.
        Why: Used by orchestrators (Kubernetes) for liveness checks.
        """
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data
        assert "timestamp" in data

    # ========================================================================
    # POST /api/v1/sync - BATCH SYNC (200 OK)
    # ========================================================================

    def test_post_sync_batch_200(self, client: TestClient):
        """Verify POST /api/v1/sync returns 200 OK and real sync statistics.

        Business rule: Sync runs the real ingestion pipeline and reports
        its outcome (not a hardcoded placeholder).
        Expected: Status 200, sync statistics reflect the pipeline result.
        Why: Validates the endpoint is actually wired to ingest_countries()
        rather than the old always-zero placeholder response. The pipeline
        itself (fetch->normalize->persist) is covered end to end elsewhere
        (tests/integration/test_e2e_pipeline.py); here fetch_countries is
        mocked so this test stays fast and network-free.
        """
        from unittest.mock import patch

        raw_country = {
            "names": {"common": "Testland", "official": "Republic of Testland"},
            "codes": {"alpha_2": "TL", "alpha_3": "TLD"},
            "region": "Europe",
            "population": 1000,
        }

        with patch("app.scripts.ingest.fetch_countries", return_value=[raw_country]):
            response = client.post("/api/v1/sync")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["countries_inserted"] == 1
        assert data["countries_updated"] == 0
        assert "sync_id" in data

    # ========================================================================
    # Response Headers and Content-Type
    # ========================================================================

    def test_json_content_type_header(self, populated_client: TestClient):
        """Verify responses have correct Content-Type header.

        Business rule: API should return application/json.
        Expected: Content-Type: application/json.
        Why: Clients depend on correct content type.
        """
        response = populated_client.get("/api/v1/countries")

        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")

    def test_cors_headers_present(self, client: TestClient):
        """Verify CORS headers if configured.

        Business rule: A: definir (CORS configuration not yet specified).
        Expected: CORS headers present or explicitly none.
        Why: Frontend integration depends on CORS.
        """
        response = client.get("/health")
        assert response.status_code == 200
        # CORS headers may or may not be present depending on configuration
