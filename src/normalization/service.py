"""Normalization service orchestrator.

Loads taxonomy, seeds canonical dishes, and matches extracted menu items.
"""

import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.logger import get_logger
from src.db.models import CanonicalDish, MenuItem
from src.normalization.embeddings import embed_dish_name
from src.normalization.matcher import DishMatcher
from src.normalization.taxonomy import DishTaxonomy

logger = get_logger(__name__)


class NormalizationService:
    """Orchestrates dish name normalization and taxonomy management."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with database session.

        Args:
            session: Async database session.
        """
        self._session = session
        self._matcher = DishMatcher(session)

    async def seed_taxonomy(self, cuisine: str) -> int:
        """Load a cuisine taxonomy and seed canonical dishes into the database.

        Args:
            cuisine: Cuisine name (e.g., 'indian').

        Returns:
            Number of canonical dishes seeded.
        """
        taxonomy = DishTaxonomy(cuisine)
        entries = taxonomy.get_all_names_with_aliases()
        seeded = 0

        for canonical_name, cuisine_name, category, aliases in entries:
            # Check if already exists
            stmt = select(CanonicalDish).where(
                CanonicalDish.canonical_name == canonical_name,
                CanonicalDish.cuisine == cuisine_name,
            )
            result = await self._session.execute(stmt)
            if result.scalar_one_or_none():
                continue

            embedding = embed_dish_name(canonical_name)

            dish = CanonicalDish(
                canonical_name=canonical_name,
                cuisine=cuisine_name,
                category=category,
                aliases=aliases if aliases else None,
                embedding=embedding.tolist(),
            )
            self._session.add(dish)
            seeded += 1

        await self._session.commit()
        logger.info("taxonomy_seeded", cuisine=cuisine, count=seeded)
        return seeded

    async def normalize_all_unmatched(self) -> dict[str, int]:
        """Match all menu items that don't have a canonical_dish_id.

        Returns:
            Dict with counts: total, auto_matched, suggested, new.
        """
        stmt = select(MenuItem).where(
            MenuItem.is_current.is_(True),
            MenuItem.canonical_dish_id.is_(None),
        )
        result = await self._session.execute(stmt)
        items = result.scalars().all()

        stats = {"total": len(items), "auto_matched": 0, "suggested": 0, "new": 0}

        for item in items:
            match = await self._matcher.match(item.dish_name)

            if match.match_type == "auto" and match.canonical_id:
                await self._session.execute(
                    update(MenuItem)
                    .where(MenuItem.id == item.id)
                    .values(canonical_dish_id=match.canonical_id)
                )
                stats["auto_matched"] += 1

            elif match.match_type == "suggest":
                # For MVP, auto-match suggestions too (with logging)
                if match.canonical_id:
                    await self._session.execute(
                        update(MenuItem)
                        .where(MenuItem.id == item.id)
                        .values(canonical_dish_id=match.canonical_id)
                    )
                stats["suggested"] += 1

            else:
                # New dish — create a canonical entry
                canonical_id = await self._create_canonical_dish(item.dish_name, "indian")
                if canonical_id:
                    await self._session.execute(
                        update(MenuItem)
                        .where(MenuItem.id == item.id)
                        .values(canonical_dish_id=canonical_id)
                    )
                stats["new"] += 1

        await self._session.commit()
        logger.info("normalization_completed", **stats)
        return stats

    async def _create_canonical_dish(
        self,
        dish_name: str,
        cuisine: str,
    ) -> uuid.UUID | None:
        """Create a new canonical dish entry.

        Args:
            dish_name: Name for the new canonical dish.
            cuisine: Cuisine type.

        Returns:
            UUID of the created canonical dish, or None on failure.
        """
        try:
            embedding = embed_dish_name(dish_name)
            dish = CanonicalDish(
                canonical_name=dish_name,
                cuisine=cuisine,
                aliases=[],
                embedding=embedding.tolist(),
            )
            self._session.add(dish)
            await self._session.flush()
            logger.info("canonical_dish_created", name=dish_name, id=str(dish.id))
            return dish.id
        except Exception as e:
            logger.error("canonical_dish_creation_failed", name=dish_name, error=str(e))
            return None
