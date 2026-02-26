"""Discovery service orchestrator.

Coordinates restaurant discovery via Google Maps and menu URL finding.
"""

from geoalchemy2.functions import ST_MakePoint
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.logger import get_logger
from src.common.models import PriceTier
from src.db.models import Restaurant
from src.discovery.google_maps import GoogleMapsClient
from src.discovery.menu_url_finder import find_menu_urls
from src.discovery.models import DiscoveredRestaurant, DiscoveryRequest, DiscoveryResult

logger = get_logger(__name__)

PRICE_LEVEL_MAP: dict[int, str] = {
    0: PriceTier.BUDGET,
    1: PriceTier.BUDGET,
    2: PriceTier.MID,
    3: PriceTier.UPSCALE,
    4: PriceTier.FINE_DINING,
}


class DiscoveryService:
    """Orchestrates restaurant discovery and persistence."""

    def __init__(self, google_client: GoogleMapsClient, session: AsyncSession) -> None:
        """Initialize with API client and database session.

        Args:
            google_client: Google Maps API client.
            session: Async database session.
        """
        self._google = google_client
        self._session = session

    async def discover(self, request: DiscoveryRequest) -> DiscoveryResult:
        """Run discovery for restaurants matching the request.

        1. Search Google Maps for restaurants
        2. Get details (website URL) for each
        3. Find menu URLs from websites
        4. Persist to database

        Args:
            request: Discovery parameters (location, radius, cuisine).

        Returns:
            Summary of discovery results.
        """
        logger.info(
            "discovery_started",
            lat=request.location.latitude,
            lng=request.location.longitude,
            radius=request.radius_miles,
            cuisine=request.cuisine,
        )

        # Step 1: Search nearby
        raw_results = await self._google.search_nearby(
            latitude=request.location.latitude,
            longitude=request.location.longitude,
            radius_miles=request.radius_miles,
            keyword=f"{request.cuisine} restaurant",
            max_results=request.max_results,
        )

        # Step 2: Enrich with details and find menu URLs
        restaurants: list[DiscoveredRestaurant] = []
        for place in raw_results:
            place_id = place.get("place_id", "")
            geometry = place.get("geometry", {}).get("location", {})

            # Get details for website URL
            details = await self._google.get_place_details(place_id) if place_id else {}

            restaurant = DiscoveredRestaurant(
                name=place.get("name", "Unknown"),
                latitude=geometry.get("lat", 0.0),
                longitude=geometry.get("lng", 0.0),
                address=details.get("formatted_address") or place.get("vicinity"),
                google_place_id=place_id,
                website_url=details.get("website"),
                cuisine_types=[request.cuisine],
                price_level=details.get("price_level") or place.get("price_level"),
                rating=place.get("rating"),
                total_ratings=place.get("user_ratings_total"),
            )
            restaurants.append(restaurant)

        # Step 3: Find menu URLs for restaurants with websites
        for restaurant in restaurants:
            if restaurant.website_url:
                try:
                    menu_urls = await find_menu_urls(restaurant.website_url)
                    # Store menu URLs in the discovered restaurant (will be saved to DB)
                    restaurant.menu_urls = menu_urls  # type: ignore[attr-defined]
                except Exception as e:
                    logger.warning(
                        "menu_url_discovery_failed",
                        restaurant=restaurant.name,
                        error=str(e),
                    )

        # Step 4: Persist to database
        await self._persist_restaurants(restaurants)

        total_with_websites = sum(1 for r in restaurants if r.website_url)
        logger.info(
            "discovery_completed",
            total=len(restaurants),
            with_websites=total_with_websites,
        )

        return DiscoveryResult(
            request=request,
            restaurants=restaurants,
            total_found=len(restaurants),
            total_with_websites=total_with_websites,
        )

    async def _persist_restaurants(self, restaurants: list[DiscoveredRestaurant]) -> None:
        """Upsert discovered restaurants into the database.

        Args:
            restaurants: List of discovered restaurants to persist.
        """
        for r in restaurants:
            menu_urls: list[str] = getattr(r, "menu_urls", [])
            price_tier = (
                PRICE_LEVEL_MAP.get(r.price_level, PriceTier.MID)
                if r.price_level is not None
                else None
            )

            stmt = insert(Restaurant).values(
                name=r.name,
                location=ST_MakePoint(r.longitude, r.latitude),
                address=r.address,
                cuisine_types=r.cuisine_types,
                google_place_id=r.google_place_id,
                website_url=r.website_url,
                menu_source_urls=menu_urls if menu_urls else None,
                price_tier=price_tier,
            )

            # On conflict (same google_place_id), update relevant fields
            if r.google_place_id:
                stmt = stmt.on_conflict_do_update(
                    index_elements=["google_place_id"],
                    set_={
                        "name": r.name,
                        "website_url": r.website_url,
                        "menu_source_urls": menu_urls if menu_urls else None,
                        "price_tier": price_tier,
                    },
                )
            else:
                stmt = stmt.on_conflict_do_nothing()

            await self._session.execute(stmt)

        await self._session.commit()
        logger.info("restaurants_persisted", count=len(restaurants))
