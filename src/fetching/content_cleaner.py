"""Clean raw HTML content to extract menu-relevant text.

Strips navigation, footers, ads, and other non-menu elements.
"""

import re

from bs4 import BeautifulSoup, Tag

from src.common.logger import get_logger

logger = get_logger(__name__)

REMOVE_TAGS = {"nav", "footer", "header", "aside", "script", "style", "noscript", "iframe"}

REMOVE_CLASS_PATTERNS = [
    re.compile(r"nav", re.IGNORECASE),
    re.compile(r"footer", re.IGNORECASE),
    re.compile(r"sidebar", re.IGNORECASE),
    re.compile(r"header", re.IGNORECASE),
    re.compile(r"cookie", re.IGNORECASE),
    re.compile(r"banner", re.IGNORECASE),
    re.compile(r"social", re.IGNORECASE),
    re.compile(r"newsletter", re.IGNORECASE),
]

REMOVE_ID_PATTERNS = [
    re.compile(r"nav", re.IGNORECASE),
    re.compile(r"footer", re.IGNORECASE),
    re.compile(r"sidebar", re.IGNORECASE),
    re.compile(r"header", re.IGNORECASE),
]


def clean_html(raw_html: str) -> str:
    """Clean HTML content by removing non-menu elements.

    Strips nav, footer, header, sidebar, ads, scripts, and other boilerplate.
    Returns the remaining text content.

    Args:
        raw_html: Raw HTML string.

    Returns:
        Cleaned text content suitable for extraction.
    """
    soup = BeautifulSoup(raw_html, "html.parser")

    # Remove unwanted tags entirely
    for tag_name in REMOVE_TAGS:
        for element in soup.find_all(tag_name):
            element.decompose()

    # Remove elements with class names matching removal patterns
    for element in soup.find_all(True):
        if not isinstance(element, Tag):
            continue

        classes = element.get("class", [])
        if isinstance(classes, list):
            class_str = " ".join(classes)
        else:
            class_str = str(classes)

        for pattern in REMOVE_CLASS_PATTERNS:
            if pattern.search(class_str):
                element.decompose()
                break

    # Remove elements with IDs matching removal patterns
    for element in soup.find_all(True, id=True):
        if not isinstance(element, Tag):
            continue
        element_id = element.get("id", "")
        if isinstance(element_id, str):
            for pattern in REMOVE_ID_PATTERNS:
                if pattern.search(element_id):
                    element.decompose()
                    break

    # Extract text, preserving some structure
    text = soup.get_text(separator="\n", strip=True)

    # Collapse multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()
