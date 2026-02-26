"""Restaurant benchmarking endpoints."""

import uuid

from fastapi import APIRouter, Query

from src.api.dependencies import DbSession
from src.intelligence.comparison import benchmark_restaurant

router = APIRouter(prefix="/api/benchmark", tags=["benchmark"])


@router.get("/{restaurant_id}")
async def get_benchmark(
    session: DbSession,
    restaurant_id: uuid.UUID,
    radius_miles: float = Query(default=5.0, ge=0.5, le=25.0),
) -> dict:
    """Benchmark a restaurant's menu against local competitors.

    Returns each dish with your price vs. local median and a verdict
    (above, below, or at market).
    """
    benchmarks = await benchmark_restaurant(session, restaurant_id, radius_miles)

    return {
        "restaurant_id": str(restaurant_id),
        "radius_miles": radius_miles,
        "benchmarks": benchmarks,
        "summary": {
            "total_dishes": len(benchmarks),
            "above_market": sum(1 for b in benchmarks if b["verdict"] == "above"),
            "below_market": sum(1 for b in benchmarks if b["verdict"] == "below"),
            "at_market": sum(1 for b in benchmarks if b["verdict"] == "at"),
        },
    }
