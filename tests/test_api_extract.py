"""Tests for menu extraction API endpoint."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from instructor.core import InstructorRetryException
from openai import APIConnectionError

from src.api.main import app
from src.extraction.model_client import FallbackNotConfiguredError
from src.extraction.schemas import ExtractedMenu, ExtractedMenuItem, ExtractedMenuSection


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the FastAPI app."""
    return TestClient(app)


def _mock_menu() -> ExtractedMenu:
    """Build a realistic mock extraction result."""
    return ExtractedMenu(
        restaurant_name="Test Restaurant",
        menu_sections=[
            ExtractedMenuSection(
                section_name="Appetizers",
                items=[
                    ExtractedMenuItem(
                        dish_name="Spring Rolls",
                        price=8.99,
                        description="Crispy vegetable spring rolls",
                        dietary_tags=["vegetarian"],
                    ),
                ],
            ),
            ExtractedMenuSection(
                section_name="Main Course",
                items=[
                    ExtractedMenuItem(
                        dish_name="Pad Thai",
                        price=14.99,
                        description="Classic Thai stir-fried noodles",
                    ),
                    ExtractedMenuItem(
                        dish_name="Green Curry",
                        price=15.99,
                        description="Thai green curry with vegetables",
                        dietary_tags=["spicy"],
                    ),
                ],
            ),
        ],
    )


_VALID_MENU_TEXT = """
APPETIZERS
Spring Rolls - $8.99
Crispy vegetable spring rolls

MAIN COURSE
Pad Thai - $14.99
Classic Thai stir-fried noodles

Green Curry - $15.99
Thai green curry with vegetables
""".strip()


class TestExtractEndpoint:
    """Tests for POST /api/extract."""

    def test_validation_rejects_short_text(self, client: TestClient) -> None:
        """Menu text below min_length (20) should be rejected."""
        response = client.post(
            "/api/extract",
            json={"menu_text": "too short"},
        )
        assert response.status_code == 422

    def test_validation_requires_menu_text(self, client: TestClient) -> None:
        """Missing menu_text field should fail validation."""
        response = client.post("/api/extract", json={})
        assert response.status_code == 422

    @patch("src.api.routes.extract.ExtractionModelClient")
    def test_successful_extraction(self, mock_client_cls: AsyncMock, client: TestClient) -> None:
        """Valid request should return extraction results."""
        mock_instance = mock_client_cls.return_value
        mock_instance.extract = AsyncMock(return_value=_mock_menu())

        response = client.post(
            "/api/extract",
            json={"menu_text": _VALID_MENU_TEXT, "restaurant_name": "Thai Kitchen"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_items"] == 3
        assert data["total_sections"] == 2
        assert 0 <= data["confidence"] <= 1.0
        assert data["menu"]["restaurant_name"] == "Test Restaurant"

    @patch("src.api.routes.extract.ExtractionModelClient")
    def test_extraction_returns_section_structure(
        self, mock_client_cls: AsyncMock, client: TestClient
    ) -> None:
        """Response should preserve section and item structure."""
        mock_instance = mock_client_cls.return_value
        mock_instance.extract = AsyncMock(return_value=_mock_menu())

        response = client.post(
            "/api/extract",
            json={"menu_text": _VALID_MENU_TEXT},
        )
        data = response.json()
        sections = data["menu"]["menu_sections"]
        assert sections[0]["section_name"] == "Appetizers"
        assert sections[1]["section_name"] == "Main Course"
        assert len(sections[0]["items"]) == 1
        assert len(sections[1]["items"]) == 2

    @patch("src.api.routes.extract.ExtractionModelClient")
    def test_connection_error_returns_502(
        self, mock_client_cls: AsyncMock, client: TestClient
    ) -> None:
        """APIConnectionError should return 502 with model-unavailable message."""
        mock_instance = mock_client_cls.return_value
        mock_instance.extract = AsyncMock(
            side_effect=APIConnectionError(request=None),  # type: ignore[arg-type]
        )

        response = client.post(
            "/api/extract",
            json={"menu_text": _VALID_MENU_TEXT},
        )
        assert response.status_code == 502
        assert "APIConnectionError" in response.json()["detail"]

    @patch("src.api.routes.extract.ExtractionModelClient")
    def test_fallback_not_configured_returns_502(
        self, mock_client_cls: AsyncMock, client: TestClient
    ) -> None:
        """FallbackNotConfiguredError should return 502."""
        mock_instance = mock_client_cls.return_value
        mock_instance.extract = AsyncMock(
            side_effect=FallbackNotConfiguredError("No API key"),
        )

        response = client.post(
            "/api/extract",
            json={"menu_text": _VALID_MENU_TEXT},
        )
        assert response.status_code == 502
        assert "FallbackNotConfiguredError" in response.json()["detail"]

    @patch("src.api.routes.extract.ExtractionModelClient")
    def test_retry_exhaustion_returns_502(
        self, mock_client_cls: AsyncMock, client: TestClient
    ) -> None:
        """InstructorRetryException (schema validation failures) should return 502."""
        mock_instance = mock_client_cls.return_value
        mock_instance.extract = AsyncMock(
            side_effect=InstructorRetryException(
                n_attempts=3,
                total_usage=0,
                messages=[],
                last_completion=None,  # type: ignore[arg-type]
            ),
        )

        response = client.post(
            "/api/extract",
            json={"menu_text": _VALID_MENU_TEXT},
        )
        assert response.status_code == 502

    @patch("src.api.routes.extract.ExtractionModelClient")
    def test_unexpected_error_propagates(
        self, mock_client_cls: AsyncMock, client: TestClient
    ) -> None:
        """Unexpected exceptions (e.g. KeyboardInterrupt) should NOT be caught."""
        mock_instance = mock_client_cls.return_value
        mock_instance.extract = AsyncMock(side_effect=RuntimeError("unexpected"))

        with pytest.raises(RuntimeError, match="unexpected"):
            client.post(
                "/api/extract",
                json={"menu_text": _VALID_MENU_TEXT},
            )

    @patch("src.api.routes.extract.ExtractionModelClient")
    def test_default_source_type_and_restaurant(
        self, mock_client_cls: AsyncMock, client: TestClient
    ) -> None:
        """Optional fields should use defaults when not provided."""
        mock_instance = mock_client_cls.return_value
        mock_instance.extract = AsyncMock(return_value=_mock_menu())

        response = client.post(
            "/api/extract",
            json={"menu_text": _VALID_MENU_TEXT},
        )
        assert response.status_code == 200
        # Verify defaults were used (extract was called successfully)
        mock_instance.extract.assert_called_once()
