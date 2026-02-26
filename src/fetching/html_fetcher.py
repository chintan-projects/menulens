"""HTML menu page fetcher.

Supports static (httpx) and dynamic (Playwright) fetching.
"""

import httpx

from src.common.logger import get_logger
from src.fetching.content_cleaner import clean_html

logger = get_logger(__name__)

# Domains known to require JavaScript rendering
JS_RENDER_DOMAINS = {
    "order.online",
    "www.toasttab.com",
    "ordering.app",
    "www.clover.com",
}


async def fetch_static(url: str) -> tuple[str, str]:
    """Fetch HTML page using httpx (no JavaScript rendering).

    Args:
        url: The URL to fetch.

    Returns:
        Tuple of (raw_html, cleaned_text).

    Raises:
        httpx.HTTPError: If the request fails.
    """
    async with httpx.AsyncClient(
        timeout=30.0,
        follow_redirects=True,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            )
        },
    ) as client:
        response = await client.get(url)
        response.raise_for_status()
        raw_html = response.text

    cleaned = clean_html(raw_html)
    logger.info(
        "html_static_fetched",
        url=url,
        raw_length=len(raw_html),
        cleaned_length=len(cleaned),
    )
    return raw_html, cleaned


async def fetch_dynamic(url: str) -> tuple[str, str]:
    """Fetch JavaScript-rendered page using Playwright.

    Args:
        url: The URL to fetch.

    Returns:
        Tuple of (raw_html, cleaned_text).
    """
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
            raw_html = await page.content()
        finally:
            await browser.close()

    cleaned = clean_html(raw_html)
    logger.info(
        "html_dynamic_fetched",
        url=url,
        raw_length=len(raw_html),
        cleaned_length=len(cleaned),
    )
    return raw_html, cleaned


def needs_javascript(url: str) -> bool:
    """Check if a URL likely requires JavaScript rendering.

    Args:
        url: The URL to check.

    Returns:
        True if the URL domain is in the known JS-render list.
    """
    from urllib.parse import urlparse

    domain = urlparse(url).netloc
    return domain in JS_RENDER_DOMAINS
