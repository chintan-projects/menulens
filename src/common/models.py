"""Shared Pydantic models used across services."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class SourceType(str, Enum):
    """Type of menu source content."""

    HTML = "html"
    PDF = "pdf"
    IMAGE = "image"
    DELIVERY_PLATFORM = "delivery_platform"


class PriceTier(str, Enum):
    """Restaurant price tier classification."""

    BUDGET = "budget"
    MID = "mid"
    UPSCALE = "upscale"
    FINE_DINING = "fine_dining"


class GeoPoint(BaseModel):
    """A geographic coordinate."""

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class RestaurantSummary(BaseModel):
    """Lightweight restaurant representation for API responses."""

    id: UUID
    name: str
    address: str | None = None
    cuisine_types: list[str] = Field(default_factory=list)
    price_tier: str | None = None
    distance_miles: float | None = None


class PriceStats(BaseModel):
    """Statistical summary of prices for a dish across restaurants."""

    dish_name: str
    canonical_dish_id: UUID | None = None
    count: int
    min_price: float
    max_price: float
    median_price: float
    p25_price: float
    p75_price: float
    avg_price: float
    as_of: datetime
