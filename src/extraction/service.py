"""Extraction service orchestrator.

Coordinates LLM-based extraction of menu content into structured data.
"""

import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.logger import get_logger
from src.config.settings import Settings
from src.db.models import MenuItem, MenuSnapshot
from src.extraction.confidence import compute_confidence
from src.extraction.model_client import ExtractionModelClient
from src.extraction.prompts import MENU_EXTRACTION_SYSTEM, MENU_EXTRACTION_USER_TEMPLATE
from src.extraction.schemas import ExtractedMenu

logger = get_logger(__name__)


class ExtractionService:
    """Orchestrates LLM-based menu extraction and persistence."""

    def __init__(
        self,
        model_client: ExtractionModelClient,
        session: AsyncSession,
        settings: Settings,
    ) -> None:
        """Initialize with model client, database session, and settings.

        Args:
            model_client: Client for calling extraction models.
            session: Async database session.
            settings: Application settings.
        """
        self._model = model_client
        self._session = session
        self._confidence_threshold = settings.extraction_confidence_threshold

    async def extract_snapshot(
        self,
        snapshot_id: uuid.UUID,
        content: str,
        *,
        source_type: str = "html",
        restaurant_name: str = "Unknown",
    ) -> tuple[ExtractedMenu, float]:
        """Extract structured menu data from a snapshot's content.

        Args:
            snapshot_id: UUID of the menu snapshot.
            content: Cleaned menu content text.
            source_type: Type of source content ('html', 'pdf').
            restaurant_name: Name of the restaurant (if known).

        Returns:
            Tuple of (extracted menu, confidence score).
        """
        user_prompt = MENU_EXTRACTION_USER_TEMPLATE.format(
            source_type=source_type,
            restaurant_name=restaurant_name,
            content=content[:15000],  # Limit to avoid exceeding context window
        )

        # Try primary model first
        menu = await self._model.extract(
            response_model=ExtractedMenu,
            system_prompt=MENU_EXTRACTION_SYSTEM,
            user_prompt=user_prompt,
        )

        confidence = compute_confidence(menu, len(content))

        # If confidence is below threshold, retry with fallback
        if confidence < self._confidence_threshold:
            logger.info(
                "low_confidence_retrying",
                snapshot_id=str(snapshot_id),
                confidence=confidence,
                threshold=self._confidence_threshold,
            )
            menu = await self._model.extract(
                response_model=ExtractedMenu,
                system_prompt=MENU_EXTRACTION_SYSTEM,
                user_prompt=user_prompt,
                use_fallback=True,
            )
            confidence = compute_confidence(menu, len(content))

        # Update snapshot with extraction results
        await self._update_snapshot(snapshot_id, menu, confidence)

        # Create menu item records
        await self._create_menu_items(snapshot_id, menu)

        logger.info(
            "extraction_completed",
            snapshot_id=str(snapshot_id),
            sections=len(menu.menu_sections),
            total_items=sum(len(s.items) for s in menu.menu_sections),
            confidence=confidence,
        )

        return menu, confidence

    async def extract_all_pending(self) -> dict[str, int]:
        """Extract menus from all unprocessed snapshots.

        Returns:
            Dict with counts: total, success, low_confidence, failed.
        """
        stmt = select(MenuSnapshot).where(
            MenuSnapshot.is_latest.is_(True),
            MenuSnapshot.extraction_confidence.is_(None),
        )
        result = await self._session.execute(stmt)
        snapshots = result.scalars().all()

        stats = {"total": len(snapshots), "success": 0, "low_confidence": 0, "failed": 0}

        for snapshot in snapshots:
            try:
                # Read raw content from stored data or path
                content = snapshot.extracted_data.get("cleaned_content", "")
                if not content and snapshot.raw_content_path:
                    from pathlib import Path

                    raw_path = Path(snapshot.raw_content_path)
                    if raw_path.exists():
                        raw_bytes = raw_path.read_bytes()
                        if snapshot.source_type == "pdf":
                            from src.fetching.pdf_fetcher import extract_text_from_pdf_bytes

                            content = extract_text_from_pdf_bytes(raw_bytes)
                        else:
                            from src.fetching.content_cleaner import clean_html

                            content = clean_html(raw_bytes.decode("utf-8", errors="replace"))

                if not content:
                    logger.warning("no_content_for_snapshot", snapshot_id=str(snapshot.id))
                    stats["failed"] += 1
                    continue

                _menu, confidence = await self.extract_snapshot(
                    snapshot.id,
                    content,
                    source_type=snapshot.source_type,
                )

                if confidence >= self._confidence_threshold:
                    stats["success"] += 1
                else:
                    stats["low_confidence"] += 1

            except Exception as e:
                logger.error(
                    "extraction_failed",
                    snapshot_id=str(snapshot.id),
                    error=str(e),
                )
                stats["failed"] += 1

        logger.info("extract_all_completed", **stats)
        return stats

    async def _update_snapshot(
        self,
        snapshot_id: uuid.UUID,
        menu: ExtractedMenu,
        confidence: float,
    ) -> None:
        """Update a snapshot record with extraction results.

        Args:
            snapshot_id: The snapshot UUID.
            menu: Extracted menu data.
            confidence: Computed confidence score.
        """
        await self._session.execute(
            update(MenuSnapshot)
            .where(MenuSnapshot.id == snapshot_id)
            .values(
                extracted_data=menu.model_dump(),
                extraction_confidence=confidence,
                extraction_model=self._model._settings.extraction_model_primary,
            )
        )
        await self._session.commit()

    async def _create_menu_items(
        self,
        snapshot_id: uuid.UUID,
        menu: ExtractedMenu,
    ) -> None:
        """Create individual menu item records from extracted menu.

        Args:
            snapshot_id: The snapshot UUID these items belong to.
            menu: Extracted menu data.
        """
        # Get the restaurant_id from the snapshot
        stmt = select(MenuSnapshot.restaurant_id).where(MenuSnapshot.id == snapshot_id)
        result = await self._session.execute(stmt)
        restaurant_id = result.scalar_one()

        # Mark previous items as not current
        await self._session.execute(
            update(MenuItem)
            .where(
                MenuItem.restaurant_id == restaurant_id,
                MenuItem.is_current.is_(True),
            )
            .values(is_current=False)
        )

        for section in menu.menu_sections:
            for item in section.items:
                menu_item = MenuItem(
                    snapshot_id=snapshot_id,
                    restaurant_id=restaurant_id,
                    dish_name=item.dish_name,
                    section_name=section.section_name,
                    price=item.price,
                    price_variants=(
                        [v.model_dump() for v in item.price_variants]
                        if item.price_variants
                        else None
                    ),
                    description=item.description,
                    dietary_tags=item.dietary_tags if item.dietary_tags else None,
                    currency=item.currency,
                    is_current=True,
                )
                self._session.add(menu_item)

        await self._session.commit()
