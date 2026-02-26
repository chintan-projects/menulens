"""Discover restaurants for a location and cuisine.

Usage:
    python -m scripts.discover_restaurants --lat 37.7749 --lng -122.4194 --cuisine indian
"""

import argparse
import asyncio

from src.common.logger import setup_logging
from src.common.models import GeoPoint
from src.config.settings import get_settings
from src.db.engine import create_engine
from src.discovery.google_maps import GoogleMapsClient
from src.discovery.models import DiscoveryRequest
from src.discovery.service import DiscoveryService


async def run(lat: float, lng: float, radius: int, cuisine: str) -> None:
    """Run restaurant discovery.

    Args:
        lat: Center latitude.
        lng: Center longitude.
        radius: Search radius in miles.
        cuisine: Cuisine keyword.
    """
    setup_logging(json_output=False, log_level="INFO")
    settings = get_settings()
    _engine, session_factory = create_engine(settings)

    async with session_factory() as session:
        google_client = GoogleMapsClient(settings.google_maps_api_key)
        service = DiscoveryService(google_client, session)

        result = await service.discover(
            DiscoveryRequest(
                location=GeoPoint(latitude=lat, longitude=lng),
                radius_miles=radius,
                cuisine=cuisine,
            )
        )

        await google_client.close()

    print(
        f"Found {result.total_found} restaurants ({result.total_with_websites} with websites)"
    )  # noqa: T201
    for r in result.restaurants[:10]:
        print(f"  - {r.name} | {r.address} | {r.website_url or 'no website'}")  # noqa: T201


def main() -> None:
    """Parse arguments and run discovery."""
    parser = argparse.ArgumentParser(description="Discover restaurants")
    parser.add_argument("--lat", type=float, required=True)
    parser.add_argument("--lng", type=float, required=True)
    parser.add_argument("--radius", type=int, default=5)
    parser.add_argument("--cuisine", type=str, default="indian")
    args = parser.parse_args()

    asyncio.run(run(args.lat, args.lng, args.radius, args.cuisine))


if __name__ == "__main__":
    main()
