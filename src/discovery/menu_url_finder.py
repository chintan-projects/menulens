"""Find actual menu page URLs from restaurant websites.

Given a restaurant's homepage URL, crawl 1-2 levels deep looking for menu pages.
"""

import re
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from src.common.logger import get_logger

logger = get_logger(__name__)

MENU_URL_PATTERNS = [
    re.compile(r"/menu", re.IGNORECASE),
    re.compile(r"/food", re.IGNORECASE),
    re.compile(r"/our-menu", re.IGNORECASE),
    re.compile(r"/dinner-menu", re.IGNORECASE),
    re.compile(r"/lunch-menu", re.IGNORECASE),
    re.compile(r"/dine", re.IGNORECASE),
]

MENU_LINK_TEXT_PATTERNS = [
    re.compile(r"\bmenu\b", re.IGNORECASE),
    re.compile(r"\bfood\b", re.IGNORECASE),
    re.compile(r"\bdine\b", re.IGNORECASE),
    re.compile(r"\border\s*online\b", re.IGNORECASE),
]


async def find_menu_urls(website_url: str) -> list[str]:
    """Find menu page URLs from a restaurant website.

    Fetches the homepage and looks for links that likely point to menu pages.
    Returns URLs sorted by confidence (URL pattern match > link text match).

    Args:
        website_url: The restaurant's homepage URL.

    Returns:
        List of candidate menu URLs, most likely first.
    """
    menu_urls: list[str] = []

    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            response = await client.get(website_url)
            response.raise_for_status()
    except httpx.HTTPError as e:
        logger.warning("menu_url_finder_fetch_failed", url=website_url, error=str(e))
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    base_domain = urlparse(website_url).netloc

    for link in soup.find_all("a", href=True):
        href = link["href"]
        full_url = urljoin(website_url, href)
        parsed = urlparse(full_url)

        # Skip external links
        if parsed.netloc and parsed.netloc != base_domain:
            continue

        # Check URL path patterns
        for pattern in MENU_URL_PATTERNS:
            if pattern.search(parsed.path):
                if full_url not in menu_urls:
                    menu_urls.append(full_url)
                break

        # Check link text patterns
        link_text = link.get_text(strip=True)
        for pattern in MENU_LINK_TEXT_PATTERNS:
            if pattern.search(link_text):
                if full_url not in menu_urls:
                    menu_urls.append(full_url)
                break

    # Also check for PDF links that might be menus
    for link in soup.find_all("a", href=True):
        href = link["href"]
        if href.lower().endswith(".pdf"):
            full_url = urljoin(website_url, href)
            link_text = link.get_text(strip=True).lower()
            if "menu" in link_text or "menu" in href.lower():
                if full_url not in menu_urls:
                    menu_urls.append(full_url)

    # If no menu links found, the homepage itself might be the menu
    if not menu_urls:
        menu_urls.append(website_url)

    logger.info("menu_urls_found", website=website_url, count=len(menu_urls), urls=menu_urls[:3])
    return menu_urls
