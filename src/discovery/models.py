"""Pydantic models for the discovery service."""

from pydantic import BaseModel, Field

from src.common.models import GeoPoint


class DiscoveryRequest(BaseModel):
    """Parameters for discovering restaurants in an area."""

    location: GeoPoint
    radius_miles: int = Field(default=5, ge=1, le=25)
    cuisine: str = "indian"
    max_results: int = Field(default=200, ge=1, le=500)


class DiscoveredRestaurant(BaseModel):
    """A restaurant found during discovery, before persistence."""

    name: str
    latitude: float
    longitude: float
    address: str | None = None
    google_place_id: str | None = None
    website_url: str | None = None
    cuisine_types: list[str] = Field(default_factory=list)
    price_level: int | None = None
    rating: float | None = None
    total_ratings: int | None = None


class DiscoveryResult(BaseModel):
    """Result of a discovery run."""

    request: DiscoveryRequest
    restaurants: list[DiscoveredRestaurant]
    total_found: int
    total_with_websites: int
