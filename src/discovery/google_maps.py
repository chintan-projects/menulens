"""Google Maps Places API client for restaurant discovery."""

from typing import Any

import httpx

from src.common.logger import get_logger

logger = get_logger(__name__)

PLACES_NEARBY_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
PLACE_DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"

MILES_TO_METERS = 1609.34


class GoogleMapsClient:
    """Client for Google Maps Places API.

    Discovers restaurants in a target area with their metadata and website URLs.
    """

    def __init__(self, api_key: str) -> None:
        """Initialize with Google Maps API key.

        Args:
            api_key: Google Maps Platform API key with Places API enabled.
        """
        self._api_key = api_key
        self._client = httpx.AsyncClient(timeout=30.0)

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()

    async def search_nearby(
        self,
        latitude: float,
        longitude: float,
        radius_miles: int,
        keyword: str,
        max_results: int = 200,
    ) -> list[dict[str, Any]]:
        """Search for restaurants near a location.

        Paginates through all results up to max_results.

        Args:
            latitude: Center point latitude.
            longitude: Center point longitude.
            radius_miles: Search radius in miles.
            keyword: Cuisine or search keyword (e.g., "indian restaurant").
            max_results: Maximum number of results to return.

        Returns:
            List of place results from Google Maps API.
        """
        radius_meters = int(radius_miles * MILES_TO_METERS)
        all_results: list[dict[str, Any]] = []
        next_page_token: str | None = None

        while len(all_results) < max_results:
            params: dict[str, str | int] = {
                "location": f"{latitude},{longitude}",
                "radius": radius_meters,
                "type": "restaurant",
                "keyword": keyword,
                "key": self._api_key,
            }
            if next_page_token:
                params = {"pagetoken": next_page_token, "key": self._api_key}

            response = await self._client.get(PLACES_NEARBY_URL, params=params)
            response.raise_for_status()
            data = response.json()

            status = data.get("status", "UNKNOWN")
            if status not in ("OK", "ZERO_RESULTS"):
                logger.error(
                    "google_maps_nearby_search_error",
                    status=status,
                    error=data.get("error_message"),
                )
                break

            results = data.get("results", [])
            all_results.extend(results)
            logger.info(
                "google_maps_nearby_page",
                count=len(results),
                total=len(all_results),
            )

            next_page_token = data.get("next_page_token")
            if not next_page_token:
                break

            # Google requires a short delay before using next_page_token
            import asyncio

            await asyncio.sleep(2)

        return all_results[:max_results]

    async def get_place_details(self, place_id: str) -> dict[str, Any]:
        """Get detailed information about a specific place.

        Args:
            place_id: Google Maps place ID.

        Returns:
            Place details including website URL, formatted address, etc.
        """
        params = {
            "place_id": place_id,
            "fields": "name,website,formatted_address,url,price_level,rating,user_ratings_total,types",
            "key": self._api_key,
        }

        response = await self._client.get(PLACE_DETAILS_URL, params=params)
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "OK":
            logger.warning(
                "google_maps_details_error",
                place_id=place_id,
                status=data.get("status"),
            )
            return {}

        return data.get("result", {})
