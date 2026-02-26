"""Price comparison and benchmarking computations.

Core pricing intelligence: compare a dish's price across restaurants in a geographic area.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.logger import get_logger
from src.common.models import PriceStats
from src.db.models import CanonicalDish, MenuItem, Restaurant

logger = get_logger(__name__)


class ComparisonResult:
    """Full comparison result for a dish in an area."""

    def __init__(
        self,
        dish_name: str,
        canonical_dish_id: uuid.UUID | None,
        stats: PriceStats,
        restaurants: list[dict[str, object]],
    ) -> None:
        """Initialize comparison result.

        Args:
            dish_name: The dish being compared.
            canonical_dish_id: Canonical dish UUID if matched.
            stats: Price statistics.
            restaurants: List of restaurant price entries.
        """
        self.dish_name = dish_name
        self.canonical_dish_id = canonical_dish_id
        self.stats = stats
        self.restaurants = restaurants


async def compare_dish_prices(
    session: AsyncSession,
    canonical_dish_id: uuid.UUID,
    latitude: float,
    longitude: float,
    radius_miles: float,
) -> ComparisonResult | None:
    """Compare prices for a canonical dish across restaurants in an area.

    Args:
        session: Async database session.
        canonical_dish_id: UUID of the canonical dish to compare.
        latitude: Center point latitude.
        longitude: Center point longitude.
        radius_miles: Search radius in miles.

    Returns:
        ComparisonResult with price stats and per-restaurant data, or None if no data.
    """
    radius_meters = radius_miles * 1609.34

    # Query: join menu_items with restaurants, filter by canonical dish + geography
    stmt = text("""
        SELECT
            r.id AS restaurant_id,
            r.name AS restaurant_name,
            r.address,
            mi.price,
            mi.dish_name,
            ST_Distance(
                r.location::geography,
                ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography
            ) / 1609.34 AS distance_miles
        FROM menu_items mi
        JOIN restaurants r ON mi.restaurant_id = r.id
        WHERE mi.canonical_dish_id = :dish_id
          AND mi.is_current = TRUE
          AND r.is_active = TRUE
          AND ST_DWithin(
              r.location::geography,
              ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography,
              :radius
          )
        ORDER BY mi.price ASC
    """)

    result = await session.execute(
        stmt,
        {
            "dish_id": str(canonical_dish_id),
            "lat": latitude,
            "lng": longitude,
            "radius": radius_meters,
        },
    )
    rows = result.fetchall()

    if not rows:
        return None

    prices = [float(row.price) for row in rows]
    sorted_prices = sorted(prices)
    count = len(sorted_prices)

    # Compute percentiles
    p25_idx = max(0, int(count * 0.25) - 1)
    p75_idx = min(count - 1, int(count * 0.75))
    median_idx = count // 2

    if count % 2 == 0 and count > 1:
        median = (sorted_prices[median_idx - 1] + sorted_prices[median_idx]) / 2
    else:
        median = sorted_prices[median_idx]

    # Get canonical dish name
    canonical = await session.execute(
        select(CanonicalDish.canonical_name).where(CanonicalDish.id == canonical_dish_id)
    )
    dish_name = canonical.scalar_one_or_none() or "Unknown"

    stats = PriceStats(
        dish_name=dish_name,
        canonical_dish_id=canonical_dish_id,
        count=count,
        min_price=sorted_prices[0],
        max_price=sorted_prices[-1],
        median_price=round(median, 2),
        p25_price=sorted_prices[p25_idx],
        p75_price=sorted_prices[p75_idx],
        avg_price=round(sum(prices) / count, 2),
        as_of=datetime.now(UTC),
    )

    restaurants = [
        {
            "restaurant_id": str(row.restaurant_id),
            "restaurant_name": row.restaurant_name,
            "address": row.address,
            "price": float(row.price),
            "dish_name": row.dish_name,
            "distance_miles": round(float(row.distance_miles), 2),
        }
        for row in rows
    ]

    return ComparisonResult(
        dish_name=dish_name,
        canonical_dish_id=canonical_dish_id,
        stats=stats,
        restaurants=restaurants,
    )


async def benchmark_restaurant(
    session: AsyncSession,
    restaurant_id: uuid.UUID,
    radius_miles: float = 5.0,
) -> list[dict[str, object]]:
    """Benchmark all dishes for a restaurant against local competitors.

    Args:
        session: Async database session.
        restaurant_id: UUID of the restaurant to benchmark.
        radius_miles: Radius to search for competitors.

    Returns:
        List of benchmark entries per dish.
    """
    # Get restaurant location
    restaurant = await session.execute(select(Restaurant).where(Restaurant.id == restaurant_id))
    rest = restaurant.scalar_one_or_none()
    if not rest:
        return []

    # Get lat/lng from PostGIS point
    location_result = await session.execute(
        text(
            "SELECT ST_Y(location::geometry) AS lat, ST_X(location::geometry) AS lng FROM restaurants WHERE id = :id"
        ),
        {"id": str(restaurant_id)},
    )
    loc = location_result.fetchone()
    if not loc:
        return []

    # Get all current menu items for this restaurant
    items = await session.execute(
        select(MenuItem).where(
            MenuItem.restaurant_id == restaurant_id,
            MenuItem.is_current.is_(True),
            MenuItem.canonical_dish_id.isnot(None),
        )
    )
    menu_items = items.scalars().all()

    benchmarks: list[dict[str, object]] = []
    for item in menu_items:
        if not item.canonical_dish_id:
            continue

        comparison = await compare_dish_prices(
            session,
            item.canonical_dish_id,
            loc.lat,
            loc.lng,
            radius_miles,
        )

        if comparison and comparison.stats.count > 1:
            your_price = float(item.price)
            median = comparison.stats.median_price

            if your_price > median * 1.1:
                verdict = "above"
            elif your_price < median * 0.9:
                verdict = "below"
            else:
                verdict = "at"

            benchmarks.append(
                {
                    "dish_name": item.dish_name,
                    "canonical_name": comparison.dish_name,
                    "your_price": your_price,
                    "median_price": median,
                    "min_price": comparison.stats.min_price,
                    "max_price": comparison.stats.max_price,
                    "competitor_count": comparison.stats.count - 1,
                    "verdict": verdict,
                }
            )

    return benchmarks
