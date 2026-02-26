"""Dish price comparison endpoints."""

import uuid
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from src.api.dependencies import DbSession
from src.intelligence.comparison import compare_dish_prices

router = APIRouter(prefix="/api/compare", tags=["compare"])


@router.get("")
async def compare_prices(
    session: DbSession,
    dish_id: Annotated[uuid.UUID, Query(description="Canonical dish UUID")],
    lat: Annotated[float, Query(description="Latitude of center point")],
    lng: Annotated[float, Query(description="Longitude of center point")],
    radius_miles: Annotated[
        float, Query(ge=0.5, le=25.0, description="Search radius in miles")
    ] = 5.0,
) -> dict:
    """Compare prices for a dish across restaurants in an area.

    Returns price statistics (median, min, max, percentiles) and per-restaurant prices.
    """
    result = await compare_dish_prices(session, dish_id, lat, lng, radius_miles)

    if result is None:
        raise HTTPException(
            status_code=404, detail="No price data found for this dish in the specified area"
        )

    return {
        "dish": {
            "name": result.dish_name,
            "canonical_id": str(result.canonical_dish_id),
        },
        "area": {
            "latitude": lat,
            "longitude": lng,
            "radius_miles": radius_miles,
        },
        "stats": result.stats.model_dump(),
        "restaurants": result.restaurants,
    }
