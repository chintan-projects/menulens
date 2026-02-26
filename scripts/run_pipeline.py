"""Run the full MenuLens pipeline from the command line.

Usage:
    python -m scripts.run_pipeline --lat 37.7749 --lng -122.4194 --radius 5 --cuisine indian
"""

import argparse
import asyncio
import json

from src.pipeline.runner import run_pipeline


def main() -> None:
    """Parse arguments and run the pipeline."""
    parser = argparse.ArgumentParser(description="Run the MenuLens pipeline")
    parser.add_argument("--lat", type=float, required=True, help="Latitude of center point")
    parser.add_argument("--lng", type=float, required=True, help="Longitude of center point")
    parser.add_argument("--radius", type=int, default=5, help="Search radius in miles")
    parser.add_argument("--cuisine", type=str, default="indian", help="Target cuisine type")

    args = parser.parse_args()

    results = asyncio.run(
        run_pipeline(
            latitude=args.lat,
            longitude=args.lng,
            radius_miles=args.radius,
            cuisine=args.cuisine,
        )
    )

    print(json.dumps(results, indent=2, default=str))  # noqa: T201


if __name__ == "__main__":
    main()
