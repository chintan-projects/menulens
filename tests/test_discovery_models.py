"""Tests for discovery models."""

from src.common.models import GeoPoint
from src.discovery.models import DiscoveredRestaurant, DiscoveryRequest


class TestDiscoveryRequest:
    """Tests for DiscoveryRequest model."""

    def test_defaults(self) -> None:
        req = DiscoveryRequest(
            location=GeoPoint(latitude=37.7749, longitude=-122.4194),
        )
        assert req.radius_miles == 5
        assert req.cuisine == "indian"
        assert req.max_results == 200

    def test_custom_values(self) -> None:
        req = DiscoveryRequest(
            location=GeoPoint(latitude=40.7128, longitude=-74.0060),
            radius_miles=10,
            cuisine="italian",
            max_results=100,
        )
        assert req.radius_miles == 10
        assert req.cuisine == "italian"


class TestDiscoveredRestaurant:
    """Tests for DiscoveredRestaurant model."""

    def test_minimal(self) -> None:
        r = DiscoveredRestaurant(
            name="Test Restaurant",
            latitude=37.7749,
            longitude=-122.4194,
        )
        assert r.name == "Test Restaurant"
        assert r.website_url is None
        assert r.cuisine_types == []

    def test_full(self) -> None:
        r = DiscoveredRestaurant(
            name="Taj Mahal",
            latitude=37.7749,
            longitude=-122.4194,
            address="123 Main St",
            google_place_id="ChIJ123",
            website_url="https://tajmahal.com",
            cuisine_types=["indian"],
            price_level=2,
            rating=4.5,
            total_ratings=200,
        )
        assert r.google_place_id == "ChIJ123"
        assert r.rating == 4.5
