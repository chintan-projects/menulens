"""Tests for demo comparison API endpoints."""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the FastAPI app."""
    return TestClient(app)


class TestDishesEndpoint:
    """Tests for GET /api/demo/dishes."""

    def test_returns_sorted_dish_list(self, client: TestClient) -> None:
        response = client.get("/api/demo/dishes")
        assert response.status_code == 200
        dishes = response.json()
        assert isinstance(dishes, list)
        assert len(dishes) == 13
        assert dishes == sorted(dishes), "Dishes should be sorted alphabetically"

    def test_contains_known_dishes(self, client: TestClient) -> None:
        response = client.get("/api/demo/dishes")
        dishes = response.json()
        for expected in ["Butter Chicken", "Naan", "Samosa", "Mango Lassi"]:
            assert expected in dishes


class TestCompareEndpoint:
    """Tests for GET /api/demo/compare."""

    def test_compare_basic_search(self, client: TestClient) -> None:
        response = client.get("/api/demo/compare", params={"dish": "Butter Chicken"})
        assert response.status_code == 200
        data = response.json()
        assert data["dish_name"] == "Butter Chicken"
        assert data["category"] == "Main Course"
        assert data["location_label"] == "San Francisco Bay Area"
        assert len(data["competitors"]) > 0

    def test_compare_returns_stats(self, client: TestClient) -> None:
        response = client.get("/api/demo/compare", params={"dish": "Naan"})
        data = response.json()
        stats = data["stats"]
        assert stats["count"] > 0
        assert stats["low"] <= stats["median"] <= stats["high"]
        assert stats["low"] <= stats["p25"] <= stats["p75"] <= stats["high"]
        assert stats["mean"] > 0

    def test_compare_with_your_price(self, client: TestClient) -> None:
        response = client.get(
            "/api/demo/compare",
            params={"dish": "Samosa", "your_price": 6.00},
        )
        data = response.json()
        assert data["your_price"] == 6.00
        assert data["your_percentile"] is not None
        assert 0 <= data["your_percentile"] <= 100

    def test_compare_without_your_price(self, client: TestClient) -> None:
        response = client.get("/api/demo/compare", params={"dish": "Samosa"})
        data = response.json()
        assert data["your_price"] is None
        assert data["your_percentile"] is None

    def test_compare_case_insensitive(self, client: TestClient) -> None:
        response = client.get("/api/demo/compare", params={"dish": "butter chicken"})
        data = response.json()
        assert data["dish_name"] == "Butter Chicken"
        assert len(data["competitors"]) > 0

    def test_compare_partial_match(self, client: TestClient) -> None:
        response = client.get("/api/demo/compare", params={"dish": "Tikka"})
        data = response.json()
        assert data["dish_name"] == "Chicken Tikka Masala"

    def test_compare_unknown_dish_returns_empty(self, client: TestClient) -> None:
        response = client.get("/api/demo/compare", params={"dish": "Sushi"})
        assert response.status_code == 200
        data = response.json()
        assert data["dish_name"] == "Sushi"
        assert data["competitors"] == []
        assert data["stats"]["count"] == 0

    def test_compare_radius_filtering(self, client: TestClient) -> None:
        """Smaller radius should return fewer or equal competitors."""
        small = client.get(
            "/api/demo/compare",
            params={"dish": "Butter Chicken", "radius": 5},
        ).json()
        large = client.get(
            "/api/demo/compare",
            params={"dish": "Butter Chicken", "radius": 50},
        ).json()
        assert small["stats"]["count"] <= large["stats"]["count"]

    def test_compare_competitors_sorted_by_distance(self, client: TestClient) -> None:
        response = client.get(
            "/api/demo/compare",
            params={"dish": "Butter Chicken", "radius": 50},
        )
        data = response.json()
        distances = [c["distance_miles"] for c in data["competitors"]]
        assert distances == sorted(distances), "Competitors should be sorted by distance"

    def test_compare_competitor_fields(self, client: TestClient) -> None:
        """Each competitor should have all required fields with valid values."""
        response = client.get("/api/demo/compare", params={"dish": "Dal Makhani"})
        data = response.json()
        for comp in data["competitors"]:
            assert comp["restaurant_name"]
            assert comp["address"]
            assert comp["price"] > 0
            assert comp["price_tier"] in ("$", "$$", "$$$")
            assert 1.0 <= comp["rating"] <= 5.0
            assert comp["review_count"] >= 0
            assert comp["distance_miles"] >= 0

    def test_compare_radius_validation(self, client: TestClient) -> None:
        """Radius below minimum should fail validation."""
        response = client.get(
            "/api/demo/compare",
            params={"dish": "Naan", "radius": 0.5},
        )
        assert response.status_code == 422
