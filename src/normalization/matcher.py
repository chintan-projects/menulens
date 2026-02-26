"""Dish name matching against canonical dishes.

Uses pgvector cosine similarity to find the best canonical match for a dish name.
"""

import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.logger import get_logger
from src.normalization.embeddings import embed_dish_name

logger = get_logger(__name__)

# Similarity thresholds
AUTO_MATCH_THRESHOLD = 0.85
SUGGEST_THRESHOLD = 0.70


class MatchResult:
    """Result of matching a dish name to canonical dishes."""

    def __init__(
        self,
        dish_name: str,
        canonical_id: uuid.UUID | None,
        canonical_name: str | None,
        similarity: float,
        match_type: str,
    ) -> None:
        """Initialize match result.

        Args:
            dish_name: The original dish name that was matched.
            canonical_id: UUID of the matched canonical dish, if any.
            canonical_name: Name of the matched canonical dish, if any.
            similarity: Cosine similarity score (0-1).
            match_type: One of 'auto', 'suggest', 'new'.
        """
        self.dish_name = dish_name
        self.canonical_id = canonical_id
        self.canonical_name = canonical_name
        self.similarity = similarity
        self.match_type = match_type


class DishMatcher:
    """Matches extracted dish names to canonical dishes using embeddings."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with database session.

        Args:
            session: Async database session with pgvector support.
        """
        self._session = session

    async def match(self, dish_name: str) -> MatchResult:
        """Find the best canonical match for a dish name.

        Args:
            dish_name: The dish name to match.

        Returns:
            MatchResult with the best match or 'new' if no good match found.
        """
        embedding = embed_dish_name(dish_name)
        embedding_list = embedding.tolist()

        # Query pgvector for nearest canonical dish
        stmt = text("""
            SELECT id, canonical_name, 1 - (embedding <=> :embedding::vector) AS similarity
            FROM canonical_dishes
            ORDER BY embedding <=> :embedding::vector
            LIMIT 1
        """)

        result = await self._session.execute(stmt, {"embedding": str(embedding_list)})
        row = result.fetchone()

        if row is None:
            return MatchResult(
                dish_name=dish_name,
                canonical_id=None,
                canonical_name=None,
                similarity=0.0,
                match_type="new",
            )

        canonical_id, canonical_name, similarity = row

        if similarity >= AUTO_MATCH_THRESHOLD:
            match_type = "auto"
        elif similarity >= SUGGEST_THRESHOLD:
            match_type = "suggest"
        else:
            match_type = "new"

        logger.info(
            "dish_matched",
            dish_name=dish_name,
            canonical_name=canonical_name,
            similarity=round(similarity, 3),
            match_type=match_type,
        )

        return MatchResult(
            dish_name=dish_name,
            canonical_id=canonical_id,
            canonical_name=canonical_name,
            similarity=similarity,
            match_type=match_type,
        )

    async def match_batch(self, dish_names: list[str]) -> list[MatchResult]:
        """Match a batch of dish names.

        Args:
            dish_names: List of dish names to match.

        Returns:
            List of MatchResults in the same order as input.
        """
        results: list[MatchResult] = []
        for name in dish_names:
            result = await self.match(name)
            results.append(result)
        return results
