"""Confidence scoring for menu extractions.

Evaluates extraction quality based on completeness, consistency, and coverage.
"""

from src.common.logger import get_logger
from src.extraction.schemas import ExtractedMenu

logger = get_logger(__name__)

# Reasonable price range for restaurant dishes (USD)
MIN_REASONABLE_PRICE = 1.0
MAX_REASONABLE_PRICE = 200.0


def compute_confidence(menu: ExtractedMenu, raw_content_length: int) -> float:
    """Compute a confidence score for an extracted menu.

    Scores based on:
    - Has sections (0.15)
    - Has items (0.25)
    - All items have prices (0.25)
    - Prices in reasonable range (0.20)
    - Content coverage — extracted enough relative to raw content (0.15)

    Args:
        menu: The extracted menu to evaluate.
        raw_content_length: Character length of the raw input content.

    Returns:
        Confidence score between 0.0 and 1.0.
    """
    score = 0.0

    # Has sections
    if menu.menu_sections:
        score += 0.15

    # Has items
    total_items = sum(len(section.items) for section in menu.menu_sections)
    if total_items > 0:
        score += 0.25
    if total_items >= 5:
        score += 0.05  # Bonus for substantial menus

    # All items have prices
    items_with_prices = sum(
        1 for section in menu.menu_sections for item in section.items if item.price > 0
    )
    if total_items > 0:
        price_ratio = items_with_prices / total_items
        score += 0.25 * price_ratio

    # Prices in reasonable range
    if total_items > 0:
        reasonable_prices = sum(
            1
            for section in menu.menu_sections
            for item in section.items
            if MIN_REASONABLE_PRICE <= item.price <= MAX_REASONABLE_PRICE
        )
        reasonable_ratio = reasonable_prices / total_items
        score += 0.20 * reasonable_ratio

    # Content coverage — rough heuristic
    extracted_text_length = sum(
        len(item.dish_name) + len(item.description or "")
        for section in menu.menu_sections
        for item in section.items
    )
    if raw_content_length > 0:
        coverage = min(extracted_text_length / raw_content_length, 1.0)
        # We expect extracted content to be 5-30% of raw content
        if 0.02 < coverage < 0.5:
            score += 0.10
        elif coverage >= 0.005:
            score += 0.05

    score = min(score, 1.0)

    logger.info(
        "confidence_computed",
        score=round(score, 3),
        total_items=total_items,
        items_with_prices=items_with_prices,
    )
    return round(score, 3)
