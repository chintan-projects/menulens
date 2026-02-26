"""Canonical dish search and price distribution endpoints."""

import uuid

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, select, text

from src.api.dependencies import DbSession
from src.db.models import CanonicalDish, MenuItem

router = APIRouter(prefix="/api/dishes", tags=["dishes"])


@router.get("/search")
async def search_dishes(
    session: DbSession,
    q: str = Query(min_length=2, description="Search query for dish names"),
    cuisine: str | None = Query(default=None, description="Filter by cuisine"),
    limit: int = Query(default=20, ge=1, le=100),
) -> dict:
    """Search canonical dishes by name.

    Uses ILIKE for text matching. Returns dishes with average price and restaurant count.
    """
    stmt = (
        select(
            CanonicalDish.id,
            CanonicalDish.canonical_name,
            CanonicalDish.cuisine,
            CanonicalDish.category,
            func.count(MenuItem.id).label("restaurant_count"),
            func.avg(MenuItem.price).label("avg_price"),
        )
        .outerjoin(
            MenuItem,
            (MenuItem.canonical_dish_id == CanonicalDish.id) & (MenuItem.is_current.is_(True)),
        )
        .where(CanonicalDish.canonical_name.ilike(f"%{q}%"))
        .group_by(CanonicalDish.id)
        .order_by(func.count(MenuItem.id).desc())
        .limit(limit)
    )

    if cuisine:
        stmt = stmt.where(CanonicalDish.cuisine == cuisine.lower())

    result = await session.execute(stmt)
    rows = result.fetchall()

    dishes = [
        {
            "id": str(row.id),
            "canonical_name": row.canonical_name,
            "cuisine": row.cuisine,
            "category": row.category,
            "restaurant_count": row.restaurant_count,
            "avg_price": round(float(row.avg_price), 2) if row.avg_price else None,
        }
        for row in rows
    ]

    return {"dishes": dishes, "count": len(dishes)}


@router.get("/{dish_id}/prices")
async def get_dish_prices(
    session: DbSession,
    dish_id: uuid.UUID,
) -> dict:
    """Get all current prices for a canonical dish across restaurants."""
    canonical = await session.execute(select(CanonicalDish).where(CanonicalDish.id == dish_id))
    dish = canonical.scalar_one_or_none()
    if not dish:
        raise HTTPException(status_code=404, detail="Dish not found")

    prices_stmt = text("""
        SELECT
            mi.price,
            mi.dish_name,
            r.name AS restaurant_name,
            r.address
        FROM menu_items mi
        JOIN restaurants r ON mi.restaurant_id = r.id
        WHERE mi.canonical_dish_id = :dish_id
          AND mi.is_current = TRUE
          AND r.is_active = TRUE
        ORDER BY mi.price ASC
    """)

    result = await session.execute(prices_stmt, {"dish_id": str(dish_id)})
    rows = result.fetchall()

    return {
        "dish": {
            "id": str(dish.id),
            "canonical_name": dish.canonical_name,
            "cuisine": dish.cuisine,
            "category": dish.category,
        },
        "prices": [
            {
                "price": float(row.price),
                "dish_name": row.dish_name,
                "restaurant_name": row.restaurant_name,
                "address": row.address,
            }
            for row in rows
        ],
        "count": len(rows),
    }
