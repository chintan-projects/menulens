"""Restaurant listing and detail endpoints."""

import uuid

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select, text

from src.api.dependencies import DbSession
from src.db.models import MenuItem, Restaurant

router = APIRouter(prefix="/api/restaurants", tags=["restaurants"])


@router.get("")
async def list_restaurants(
    session: DbSession,
    lat: float = Query(description="Latitude of center point"),
    lng: float = Query(description="Longitude of center point"),
    radius_miles: float = Query(default=5.0, ge=0.5, le=25.0),
    cuisine: str | None = Query(default=None, description="Filter by cuisine type"),
) -> dict:
    """List restaurants in a geographic area.

    Returns restaurants sorted by distance with metadata.
    """
    radius_meters = radius_miles * 1609.34

    query = text("""
        SELECT
            r.id,
            r.name,
            r.address,
            r.cuisine_types,
            r.price_tier,
            r.website_url,
            ST_Distance(
                r.location::geography,
                ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography
            ) / 1609.34 AS distance_miles,
            (SELECT COUNT(*) FROM menu_items mi
             WHERE mi.restaurant_id = r.id AND mi.is_current = TRUE) AS item_count
        FROM restaurants r
        WHERE r.is_active = TRUE
          AND ST_DWithin(
              r.location::geography,
              ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography,
              :radius
          )
        ORDER BY distance_miles ASC
    """)

    result = await session.execute(query, {"lat": lat, "lng": lng, "radius": radius_meters})
    rows = result.fetchall()

    restaurants = []
    for row in rows:
        cuisine_types = row.cuisine_types or []
        if cuisine and cuisine.lower() not in [c.lower() for c in cuisine_types]:
            continue

        restaurants.append(
            {
                "id": str(row.id),
                "name": row.name,
                "address": row.address,
                "cuisine_types": cuisine_types,
                "price_tier": row.price_tier,
                "website_url": row.website_url,
                "distance_miles": round(float(row.distance_miles), 2),
                "item_count": row.item_count,
            }
        )

    return {"restaurants": restaurants, "count": len(restaurants)}


@router.get("/{restaurant_id}")
async def get_restaurant(
    session: DbSession,
    restaurant_id: uuid.UUID,
) -> dict:
    """Get detailed restaurant information with full menu."""
    stmt = select(Restaurant).where(Restaurant.id == restaurant_id)
    result = await session.execute(stmt)
    restaurant = result.scalar_one_or_none()

    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    # Get current menu items grouped by section
    items_stmt = (
        select(MenuItem)
        .where(
            MenuItem.restaurant_id == restaurant_id,
            MenuItem.is_current.is_(True),
        )
        .order_by(MenuItem.section_name, MenuItem.price)
    )
    items_result = await session.execute(items_stmt)
    items = items_result.scalars().all()

    # Group by section
    sections: dict[str, list[dict]] = {}
    for item in items:
        section = item.section_name or "General"
        if section not in sections:
            sections[section] = []
        sections[section].append(
            {
                "id": str(item.id),
                "dish_name": item.dish_name,
                "price": float(item.price),
                "description": item.description,
                "dietary_tags": item.dietary_tags or [],
                "canonical_dish_id": (
                    str(item.canonical_dish_id) if item.canonical_dish_id else None
                ),
            }
        )

    return {
        "id": str(restaurant.id),
        "name": restaurant.name,
        "address": restaurant.address,
        "cuisine_types": restaurant.cuisine_types or [],
        "price_tier": restaurant.price_tier,
        "website_url": restaurant.website_url,
        "menu_sections": [
            {"section_name": name, "items": items_list} for name, items_list in sections.items()
        ],
    }
