"""Cuisine-specific dish taxonomy management.

Loads and manages canonical dish definitions from YAML taxonomy files.
"""

from pathlib import Path
from typing import Any

import yaml

from src.common.logger import get_logger

logger = get_logger(__name__)

TAXONOMY_DIR = Path(__file__).parent.parent.parent / "data" / "taxonomies"


class DishTaxonomy:
    """Manages canonical dish definitions for a cuisine."""

    def __init__(self, cuisine: str) -> None:
        """Initialize taxonomy for a cuisine.

        Args:
            cuisine: Cuisine name (e.g., 'indian'). Must have a matching YAML file.
        """
        self.cuisine = cuisine
        self.dishes: list[dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        """Load taxonomy from YAML file."""
        taxonomy_path = TAXONOMY_DIR / f"{self.cuisine}.yaml"
        if not taxonomy_path.exists():
            logger.warning("taxonomy_not_found", cuisine=self.cuisine, path=str(taxonomy_path))
            return

        with open(taxonomy_path) as f:
            data = yaml.safe_load(f)

        self.dishes = data.get("dishes", [])
        logger.info(
            "taxonomy_loaded",
            cuisine=self.cuisine,
            dish_count=len(self.dishes),
        )

    def get_all_names_with_aliases(self) -> list[tuple[str, str, str | None, list[str]]]:
        """Get all canonical names with their aliases.

        Returns:
            List of (canonical_name, cuisine, category, aliases) tuples.
        """
        results: list[tuple[str, str, str | None, list[str]]] = []
        for dish in self.dishes:
            canonical_name = dish["canonical_name"]
            cuisine = dish.get("cuisine", self.cuisine)
            category = dish.get("category")
            aliases = dish.get("aliases", [])
            results.append((canonical_name, cuisine, category, aliases))
        return results
