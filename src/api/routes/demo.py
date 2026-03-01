"""Demo comparison endpoint with seeded neighborhood data.

Serves realistic pre-seeded data so the frontend can demonstrate the core
restaurant-owner experience: "What do competitors near me charge for this dish?"

No database required — data is in-memory for demo/prototype purposes.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from src.common.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/demo", tags=["demo"])


# ---------------------------------------------------------------------------
# Seed data: realistic Indian restaurants in SF Bay Area
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SeedRestaurant:
    """A seeded restaurant for demo purposes."""

    name: str
    address: str
    lat: float
    lng: float
    rating: float
    review_count: int
    price_tier: str  # "$", "$$", "$$$"
    cuisine_tags: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class SeedMenuItem:
    """A seeded menu item."""

    restaurant_idx: int
    dish_name: str
    canonical_name: str
    price: float
    section: str


RESTAURANTS: list[SeedRestaurant] = [
    SeedRestaurant(
        "Amber India",
        "2290 El Camino Real, Mountain View, CA",
        37.4003,
        -122.1090,
        4.3,
        1842,
        "$$",
        ("indian", "modern indian"),
    ),
    SeedRestaurant(
        "Shalimar Restaurant",
        "1409 Polk St, San Francisco, CA",
        37.7897,
        -122.4200,
        4.1,
        2105,
        "$",
        ("indian", "pakistani"),
    ),
    SeedRestaurant(
        "Dosa",
        "995 Valencia St, San Francisco, CA",
        37.7567,
        -122.4213,
        4.4,
        1623,
        "$$",
        ("south indian", "indian"),
    ),
    SeedRestaurant(
        "Roti Indian Bistro",
        "53 W Portal Ave, San Francisco, CA",
        37.7400,
        -122.4670,
        4.5,
        892,
        "$$",
        ("indian", "north indian"),
    ),
    SeedRestaurant(
        "Curry Up Now",
        "225 Bush St, San Francisco, CA",
        37.7910,
        -122.4010,
        4.0,
        756,
        "$",
        ("indian", "street food"),
    ),
    SeedRestaurant(
        "August 1 Five",
        "524 Van Ness Ave, San Francisco, CA",
        37.7805,
        -122.4210,
        4.6,
        534,
        "$$$",
        ("indian", "fine dining"),
    ),
    SeedRestaurant(
        "Zareen's",
        "365 S California Ave, Palo Alto, CA",
        37.4560,
        -122.1620,
        4.7,
        1456,
        "$$",
        ("indian", "pakistani"),
    ),
    SeedRestaurant(
        "Vik's Chaat",
        "726 Allston Way, Berkeley, CA",
        37.8695,
        -122.2710,
        4.2,
        1321,
        "$",
        ("indian", "street food", "chaat"),
    ),
    SeedRestaurant(
        "Bombay Garden",
        "42380 Fremont Blvd, Fremont, CA",
        37.5885,
        -122.0686,
        4.0,
        645,
        "$",
        ("indian", "north indian"),
    ),
    SeedRestaurant(
        "Taj Campton Place",
        "340 Stockton St, San Francisco, CA",
        37.7890,
        -122.4065,
        4.5,
        423,
        "$$$",
        ("indian", "fine dining"),
    ),
    SeedRestaurant(
        "Kabab & Curry",
        "1320 S De Anza Blvd, San Jose, CA",
        37.3140,
        -122.0320,
        4.1,
        987,
        "$",
        ("indian", "north indian"),
    ),
    SeedRestaurant(
        "Rangoli India",
        "3695 Union City Blvd, Union City, CA",
        37.6350,
        -122.0990,
        4.3,
        712,
        "$$",
        ("indian", "south indian"),
    ),
]

# Canonical dishes with per-restaurant prices (restaurant_idx → price)
# fmt: off
_DISH_DATA: dict[str, dict[str, list[tuple[int, float, str]]]] = {
    "Butter Chicken": {
        "category": "Main Course",  # type: ignore[dict-item]
        "items": [  # type: ignore[dict-item]
            (0, 18.99, "Main Course"), (1, 13.99, "Entrees"), (3, 17.99, "Chicken"),
            (4, 14.49, "Bowls"), (5, 26.99, "Mains"), (6, 16.99, "Entrees"),
            (8, 14.99, "Main Course"), (9, 28.99, "Main Course"),
            (10, 12.99, "Entrees"), (11, 16.49, "Main Course"),
        ],
    },
    "Chicken Tikka Masala": {
        "category": "Main Course",  # type: ignore[dict-item]
        "items": [  # type: ignore[dict-item]
            (0, 19.99, "Main Course"), (1, 14.99, "Entrees"), (3, 18.49, "Chicken"),
            (5, 27.99, "Mains"), (6, 17.49, "Entrees"), (8, 15.49, "Main Course"),
            (9, 29.99, "Main Course"), (10, 13.99, "Entrees"),
            (11, 17.99, "Main Course"),
        ],
    },
    "Palak Paneer": {
        "category": "Vegetarian",  # type: ignore[dict-item]
        "items": [  # type: ignore[dict-item]
            (0, 16.99, "Vegetarian"), (1, 12.99, "Vegetarian"), (3, 15.99, "Paneer"),
            (5, 23.99, "Mains"), (6, 14.99, "Vegetarian"), (8, 13.49, "Vegetarian"),
            (10, 11.99, "Vegetarian"), (11, 14.99, "Vegetarian"),
        ],
    },
    "Lamb Rogan Josh": {
        "category": "Main Course",  # type: ignore[dict-item]
        "items": [  # type: ignore[dict-item]
            (0, 21.99, "Lamb"), (1, 16.99, "Entrees"), (3, 19.99, "Lamb"),
            (5, 31.99, "Mains"), (6, 18.99, "Entrees"),
            (9, 33.99, "Main Course"), (10, 15.99, "Entrees"),
        ],
    },
    "Naan": {
        "category": "Breads",  # type: ignore[dict-item]
        "items": [  # type: ignore[dict-item]
            (0, 3.99, "Breads"), (1, 2.49, "Breads"), (3, 3.49, "Breads"),
            (4, 2.99, "Sides"), (5, 5.99, "Breads"), (6, 3.49, "Breads"),
            (8, 2.99, "Breads"), (9, 6.99, "Breads"),
            (10, 2.49, "Breads"), (11, 3.49, "Breads"),
        ],
    },
    "Garlic Naan": {
        "category": "Breads",  # type: ignore[dict-item]
        "items": [  # type: ignore[dict-item]
            (0, 4.99, "Breads"), (1, 3.49, "Breads"), (3, 4.49, "Breads"),
            (4, 3.99, "Sides"), (5, 6.99, "Breads"), (6, 4.49, "Breads"),
            (8, 3.49, "Breads"), (10, 3.49, "Breads"), (11, 4.49, "Breads"),
        ],
    },
    "Chicken Biryani": {
        "category": "Rice",  # type: ignore[dict-item]
        "items": [  # type: ignore[dict-item]
            (0, 17.99, "Rice & Biryani"), (1, 13.99, "Biryani"),
            (3, 16.99, "Biryani"), (6, 15.99, "Rice"),
            (8, 13.99, "Biryani"), (10, 12.99, "Biryani"),
            (11, 15.99, "Biryani"),
        ],
    },
    "Samosa": {
        "category": "Appetizers",  # type: ignore[dict-item]
        "items": [  # type: ignore[dict-item]
            (0, 7.99, "Appetizers"), (1, 4.99, "Starters"), (3, 6.99, "Starters"),
            (4, 5.49, "Snacks"), (6, 6.49, "Starters"), (7, 4.99, "Chaat & Snacks"),
            (8, 5.99, "Appetizers"), (10, 4.49, "Appetizers"),
            (11, 5.99, "Appetizers"),
        ],
    },
    "Dal Makhani": {
        "category": "Vegetarian",  # type: ignore[dict-item]
        "items": [  # type: ignore[dict-item]
            (0, 15.99, "Vegetarian"), (1, 11.99, "Lentils"), (3, 14.99, "Dal"),
            (5, 21.99, "Mains"), (6, 13.99, "Vegetarian"),
            (8, 12.49, "Vegetarian"), (10, 10.99, "Lentils"),
            (11, 13.99, "Vegetarian"),
        ],
    },
    "Chana Masala": {
        "category": "Vegetarian",  # type: ignore[dict-item]
        "items": [  # type: ignore[dict-item]
            (0, 14.99, "Vegetarian"), (1, 11.49, "Vegetarian"),
            (3, 13.99, "Vegetarian"), (6, 12.99, "Vegetarian"),
            (7, 8.99, "Chaat & Snacks"), (8, 11.99, "Vegetarian"),
            (10, 10.49, "Vegetarian"),
        ],
    },
    "Gulab Jamun": {
        "category": "Desserts",  # type: ignore[dict-item]
        "items": [  # type: ignore[dict-item]
            (0, 7.99, "Desserts"), (1, 4.99, "Desserts"), (3, 6.99, "Desserts"),
            (5, 12.99, "Desserts"), (6, 5.99, "Desserts"),
            (8, 5.49, "Desserts"), (10, 4.49, "Desserts"),
        ],
    },
    "Tandoori Chicken": {
        "category": "Tandoor",  # type: ignore[dict-item]
        "items": [  # type: ignore[dict-item]
            (0, 18.99, "Tandoor"), (1, 13.99, "Tandoor"), (3, 16.99, "Tandoor"),
            (5, 24.99, "From The Tandoor"), (6, 15.99, "Grill"),
            (8, 14.49, "Tandoor"), (10, 12.99, "Tandoor"),
        ],
    },
    "Mango Lassi": {
        "category": "Beverages",  # type: ignore[dict-item]
        "items": [  # type: ignore[dict-item]
            (0, 5.99, "Beverages"), (1, 3.99, "Drinks"), (3, 4.99, "Beverages"),
            (4, 4.49, "Drinks"), (6, 4.99, "Beverages"),
            (8, 3.99, "Beverages"), (10, 3.49, "Drinks"),
            (11, 4.49, "Beverages"),
        ],
    },
}
# fmt: on

# Build canonical dish list for autocomplete
CANONICAL_DISHES: list[str] = sorted(_DISH_DATA.keys())


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class CompetitorPrice(BaseModel):
    """One competitor's price for the searched dish."""

    restaurant_name: str
    address: str
    price: float
    price_tier: str = Field(description="$, $$, or $$$")
    rating: float
    review_count: int
    section_name: str
    distance_miles: float


class PriceStats(BaseModel):
    """Aggregate price statistics for the searched dish."""

    median: float
    mean: float
    low: float
    high: float
    count: int
    p25: float
    p75: float


class DishComparisonResponse(BaseModel):
    """Full comparison response for a dish search."""

    dish_name: str
    category: str
    location_label: str
    radius_miles: float
    stats: PriceStats
    competitors: list[CompetitorPrice]
    your_price: float | None = Field(
        default=None,
        description="Your price if provided, for benchmarking",
    )
    your_percentile: float | None = Field(
        default=None,
        description="Your percentile rank (0-100) among competitors",
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Approximate distance in miles between two lat/lng points."""
    import math  # noqa: PLC0415

    r = 3958.8  # Earth radius in miles
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lng / 2) ** 2
    )
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _compute_stats(prices: list[float]) -> PriceStats:
    """Compute price statistics from a list of prices."""
    s = sorted(prices)
    n = len(s)
    return PriceStats(
        median=s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2,
        mean=round(sum(s) / n, 2),
        low=s[0],
        high=s[-1],
        count=n,
        p25=s[max(0, n // 4)],
        p75=s[min(n - 1, 3 * n // 4)],
    )


def _percentile_rank(prices: list[float], your_price: float) -> float:
    """What percentage of competitors are priced below your price."""
    below = sum(1 for p in prices if p < your_price)
    return round(below / len(prices) * 100, 1)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/dishes", response_model=list[str])
async def list_dishes() -> list[str]:
    """Return the list of available canonical dishes for autocomplete."""
    return CANONICAL_DISHES


@router.get("/compare", response_model=DishComparisonResponse)
async def compare_dish(
    dish: str = Query(description="Dish name to search for"),
    lat: float = Query(default=37.7749, description="Your latitude"),
    lng: float = Query(default=-122.4194, description="Your longitude"),
    radius: float = Query(default=15.0, ge=1.0, le=50.0, description="Radius in miles"),
    your_price: float | None = Query(default=None, ge=0, description="Your price for benchmarking"),
) -> DishComparisonResponse:
    """Compare a dish's price across nearby competitors.

    Returns price stats, individual competitor prices, and optional benchmarking
    against your own price.
    """
    # Fuzzy match dish name (case-insensitive)
    dish_key: str | None = None
    dish_lower = dish.lower().strip()
    for canonical in _DISH_DATA:
        if canonical.lower() == dish_lower:
            dish_key = canonical
            break

    # Partial match fallback
    if dish_key is None:
        for canonical in _DISH_DATA:
            if dish_lower in canonical.lower() or canonical.lower() in dish_lower:
                dish_key = canonical
                break

    if dish_key is None:
        # Return empty result with guidance
        return DishComparisonResponse(
            dish_name=dish,
            category="Unknown",
            location_label="San Francisco Bay Area",
            radius_miles=radius,
            stats=PriceStats(median=0, mean=0, low=0, high=0, count=0, p25=0, p75=0),
            competitors=[],
            your_price=your_price,
            your_percentile=None,
        )

    dish_info = _DISH_DATA[dish_key]
    items: list[tuple[int, float, str]] = dish_info["items"]  # type: ignore[assignment]
    category: str = dish_info["category"]  # type: ignore[assignment]

    # Filter by radius
    competitors: list[CompetitorPrice] = []
    prices: list[float] = []

    for rest_idx, price, section in items:
        rest = RESTAURANTS[rest_idx]
        dist = _haversine(lat, lng, rest.lat, rest.lng)
        if dist <= radius:
            competitors.append(
                CompetitorPrice(
                    restaurant_name=rest.name,
                    address=rest.address,
                    price=price,
                    price_tier=rest.price_tier,
                    rating=rest.rating,
                    review_count=rest.review_count,
                    section_name=section,
                    distance_miles=round(dist, 1),
                )
            )
            prices.append(price)

    # Sort by distance
    competitors.sort(key=lambda c: c.distance_miles)

    stats = (
        _compute_stats(prices)
        if prices
        else PriceStats(
            median=0,
            mean=0,
            low=0,
            high=0,
            count=0,
            p25=0,
            p75=0,
        )
    )

    your_pct = _percentile_rank(prices, your_price) if your_price and prices else None

    logger.info(
        "demo_compare",
        dish=dish_key,
        results=len(competitors),
        radius=radius,
    )

    return DishComparisonResponse(
        dish_name=dish_key,
        category=category,
        location_label="San Francisco Bay Area",
        radius_miles=radius,
        stats=stats,
        competitors=competitors,
        your_price=your_price,
        your_percentile=your_pct,
    )
