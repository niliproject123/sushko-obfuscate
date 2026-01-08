"""
API endpoint tests using FastAPI TestClient.
"""
import pytest
import json
from pathlib import Path
from fastapi.testclient import TestClient

from api.main import app


# Path to test resources
RESOURCES_PATH = Path(__file__).parent / "resources"


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def sample_pdf():
    """Load sample PDF for testing."""
    path = RESOURCES_PATH / "medical_form_original.pdf"
    if path.exists():
        return path.read_bytes()
    pytest.skip("Test PDF file not found")


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check(self, client):
        """Test health endpoint returns healthy."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_root_endpoint(self, client):
        """Test root endpoint returns API info."""
        response = client.get("/")
        assert response.status_code == 200
        assert "PDF" in response.json()["message"]


class TestConfigEndpoints:
    """Tests for configuration endpoints."""

    def test_get_config(self, client):
        """Test getting server configuration."""
        response = client.get("/api/config")
        assert response.status_code == 200

        data = response.json()
        assert "patterns" in data
        assert "replacement_pools" in data
        assert "ocr" in data
        assert "placeholders" in data

    def test_get_patterns(self, client):
        """Test getting detection patterns."""
        response = client.get("/api/config/patterns")
        assert response.status_code == 200

        patterns = response.json()
        assert isinstance(patterns, list)
        assert len(patterns) > 0

    def test_get_replacement_pools(self, client):
        """Test getting replacement pools."""
        response = client.get("/api/config/pools")
        assert response.status_code == 200

        pools = response.json()
        assert "name_hebrew_first" in pools
        assert "city" in pools


class TestExtractEndpoint:
    """Tests for the extract/anonymize endpoint."""

    def test_extract_with_pdf(self, client, sample_pdf):
        """Test PDF extraction and anonymization."""
        response = client.post(
            "/api/extract",
            files={"file": ("test.pdf", sample_pdf, "application/pdf")},
            data={"config": "{}"},
        )

        assert response.status_code == 200

        data = response.json()
        assert "file_id" in data
        assert "page_count" in data
        assert "total_matches" in data
        assert "pages" in data
        assert "mappings_used" in data

    def test_extract_with_user_replacements(self, client, sample_pdf):
        """Test extraction with user-defined replacements."""
        config = {
            "user_replacements": {
                "מיכאל": "דוד",
                "פורגאצ'": "כהן",
            }
        }

        response = client.post(
            "/api/extract",
            files={"file": ("test.pdf", sample_pdf, "application/pdf")},
            data={"config": json.dumps(config)},
        )

        assert response.status_code == 200

        data = response.json()
        mappings = data.get("mappings_used", {})

        # User mappings should be in the result
        assert mappings.get("מיכאל") == "דוד"
        assert mappings.get("פורגאצ'") == "כהן"

    def test_extract_with_disabled_detectors(self, client, sample_pdf):
        """Test extraction with some detectors disabled."""
        config = {
            "disabled_detectors": ["email", "phone_mobile"],
        }

        response = client.post(
            "/api/extract",
            files={"file": ("test.pdf", sample_pdf, "application/pdf")},
            data={"config": json.dumps(config)},
        )

        assert response.status_code == 200

    def test_extract_invalid_config(self, client, sample_pdf):
        """Test extraction with invalid config JSON."""
        response = client.post(
            "/api/extract",
            files={"file": ("test.pdf", sample_pdf, "application/pdf")},
            data={"config": "not valid json"},
        )

        assert response.status_code == 400

    def test_download_file(self, client, sample_pdf):
        """Test downloading processed file."""
        # First, extract a file
        extract_response = client.post(
            "/api/extract",
            files={"file": ("test.pdf", sample_pdf, "application/pdf")},
            data={"config": "{}"},
        )

        assert extract_response.status_code == 200
        file_id = extract_response.json()["file_id"]

        # Then download it
        download_response = client.get(f"/api/download/{file_id}")

        assert download_response.status_code == 200
        assert download_response.headers["content-type"] == "application/pdf"

    def test_download_nonexistent_file(self, client):
        """Test downloading non-existent file returns 404."""
        response = client.get("/api/download/nonexistent123")
        assert response.status_code == 404


class TestExtractResponse:
    """Tests for extract response format."""

    def test_response_contains_page_details(self, client, sample_pdf):
        """Test that response contains per-page match details."""
        response = client.post(
            "/api/extract",
            files={"file": ("test.pdf", sample_pdf, "application/pdf")},
            data={"config": "{}"},
        )

        assert response.status_code == 200

        data = response.json()
        pages = data["pages"]

        assert len(pages) > 0

        for page in pages:
            assert "page_number" in page
            assert "matches_found" in page
            assert "matches" in page

            for match in page["matches"]:
                assert "text" in match
                assert "type" in match
                assert "replacement" in match

    def test_matches_have_correct_format(self, client, sample_pdf):
        """Test that matches have all required fields."""
        response = client.post(
            "/api/extract",
            files={"file": ("test.pdf", sample_pdf, "application/pdf")},
            data={"config": "{}"},
        )

        data = response.json()

        for page in data["pages"]:
            for match in page["matches"]:
                assert "text" in match
                assert "type" in match
                assert "start" in match
                assert "end" in match
                assert "pattern_name" in match
                assert "replacement" in match
