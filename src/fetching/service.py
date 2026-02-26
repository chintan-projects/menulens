"""Fetching service orchestrator.

Classifies URLs, dispatches to the correct fetcher, stores raw content.
"""

import uuid
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.logger import get_logger
from src.common.models import SourceType
from src.config.settings import Settings
from src.db.models import MenuSnapshot, Restaurant
from src.fetching.html_fetcher import fetch_dynamic, fetch_static, needs_javascript
from src.fetching.models import FetchResult
from src.fetching.pdf_fetcher import fetch_pdf

logger = get_logger(__name__)


class FetchingService:
    """Orchestrates menu content fetching for discovered restaurants."""

    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        """Initialize with database session and settings.

        Args:
            session: Async database session.
            settings: Application settings.
        """
        self._session = session
        self._raw_dir = Path(settings.raw_content_dir)
        self._raw_dir.mkdir(parents=True, exist_ok=True)

    async def fetch_restaurant_menus(self, restaurant_id: uuid.UUID) -> list[FetchResult]:
        """Fetch all menu sources for a restaurant.

        Args:
            restaurant_id: UUID of the restaurant.

        Returns:
            List of fetch results for each menu source URL.
        """
        stmt = select(Restaurant).where(Restaurant.id == restaurant_id)
        result = await self._session.execute(stmt)
        restaurant = result.scalar_one_or_none()

        if not restaurant:
            logger.error("restaurant_not_found", restaurant_id=str(restaurant_id))
            return []

        urls = restaurant.menu_source_urls or []
        if not urls:
            logger.warning("no_menu_urls", restaurant_id=str(restaurant_id), name=restaurant.name)
            return []

        results: list[FetchResult] = []
        for url in urls:
            fetch_result = await self._fetch_url(url, restaurant_id)
            if fetch_result.fetch_success:
                await self._store_snapshot(restaurant_id, fetch_result)
            results.append(fetch_result)

        return results

    async def fetch_all_pending(self) -> dict[str, int]:
        """Fetch menus for all restaurants that haven't been fetched yet.

        Returns:
            Dict with counts: total, success, failed.
        """
        stmt = select(Restaurant).where(
            Restaurant.is_active.is_(True),
            Restaurant.menu_source_urls.isnot(None),
        )
        result = await self._session.execute(stmt)
        restaurants = result.scalars().all()

        stats = {"total": 0, "success": 0, "failed": 0}
        for restaurant in restaurants:
            # Skip if we already have a recent snapshot
            existing = await self._session.execute(
                select(MenuSnapshot).where(
                    MenuSnapshot.restaurant_id == restaurant.id, MenuSnapshot.is_latest.is_(True)
                )
            )
            if existing.scalar_one_or_none():
                continue

            results = await self.fetch_restaurant_menus(restaurant.id)
            stats["total"] += len(results)
            stats["success"] += sum(1 for r in results if r.fetch_success)
            stats["failed"] += sum(1 for r in results if not r.fetch_success)

        logger.info("fetch_all_completed", **stats)
        return stats

    async def _fetch_url(self, url: str, restaurant_id: uuid.UUID) -> FetchResult:
        """Fetch content from a single URL.

        Args:
            url: The URL to fetch.
            restaurant_id: ID of the owning restaurant (for file storage paths).

        Returns:
            FetchResult with content or error details.
        """
        now = datetime.now(UTC)
        source_type = self._classify_url(url)

        try:
            if source_type == SourceType.PDF:
                pdf_bytes, text = await fetch_pdf(url)
                raw_path = self._save_raw(restaurant_id, url, pdf_bytes, "pdf")
                return FetchResult(
                    source_url=url,
                    source_type=source_type,
                    raw_content=text,
                    cleaned_content=text,
                    fetched_at=now,
                    content_length=len(text),
                    raw_content_path=str(raw_path),
                )
            else:
                if needs_javascript(url):
                    raw_html, cleaned = await fetch_dynamic(url)
                else:
                    raw_html, cleaned = await fetch_static(url)

                raw_path = self._save_raw(restaurant_id, url, raw_html.encode(), "html")
                return FetchResult(
                    source_url=url,
                    source_type=SourceType.HTML,
                    raw_content=raw_html,
                    cleaned_content=cleaned,
                    fetched_at=now,
                    content_length=len(cleaned),
                    raw_content_path=str(raw_path),
                )

        except Exception as e:
            logger.error("fetch_failed", url=url, error=str(e))
            return FetchResult(
                source_url=url,
                source_type=source_type,
                raw_content="",
                cleaned_content="",
                fetched_at=now,
                content_length=0,
                fetch_success=False,
                error_message=str(e),
            )

    def _classify_url(self, url: str) -> SourceType:
        """Determine source type from URL.

        Args:
            url: The URL to classify.

        Returns:
            The detected source type.
        """
        lower = url.lower()
        if lower.endswith(".pdf") or "pdf" in lower.split("?")[0].split("/")[-1]:
            return SourceType.PDF
        return SourceType.HTML

    def _save_raw(
        self,
        restaurant_id: uuid.UUID,
        url: str,
        content: bytes,
        extension: str,
    ) -> Path:
        """Save raw fetched content to disk.

        Args:
            restaurant_id: ID of the restaurant.
            url: Source URL (for filename).
            content: Raw bytes to save.
            extension: File extension.

        Returns:
            Path to the saved file.
        """
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        dir_path = self._raw_dir / str(restaurant_id)
        dir_path.mkdir(parents=True, exist_ok=True)

        filename = f"{timestamp}.{extension}"
        file_path = dir_path / filename
        file_path.write_bytes(content)

        return file_path

    async def _store_snapshot(
        self,
        restaurant_id: uuid.UUID,
        fetch_result: FetchResult,
    ) -> None:
        """Create a menu snapshot record in the database.

        Args:
            restaurant_id: ID of the restaurant.
            fetch_result: The fetch result to store.
        """
        # Mark previous snapshots as not latest
        from sqlalchemy import update

        await self._session.execute(
            update(MenuSnapshot)
            .where(
                MenuSnapshot.restaurant_id == restaurant_id,
                MenuSnapshot.is_latest.is_(True),
            )
            .values(is_latest=False)
        )

        snapshot = MenuSnapshot(
            restaurant_id=restaurant_id,
            fetched_at=fetch_result.fetched_at,
            source_url=fetch_result.source_url,
            source_type=fetch_result.source_type.value,
            raw_content_path=fetch_result.raw_content_path,
            extracted_data={},  # Will be populated by extraction service
            is_latest=True,
        )
        self._session.add(snapshot)
        await self._session.commit()
