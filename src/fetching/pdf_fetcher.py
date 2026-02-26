"""PDF menu fetcher.

Downloads PDF files and extracts text content using pymupdf.
"""

import httpx
import pymupdf

from src.common.logger import get_logger

logger = get_logger(__name__)


async def fetch_pdf(url: str) -> tuple[bytes, str]:
    """Download a PDF and extract its text content.

    Args:
        url: URL of the PDF file.

    Returns:
        Tuple of (raw_pdf_bytes, extracted_text).

    Raises:
        httpx.HTTPError: If the download fails.
        pymupdf.FileDataError: If the PDF is corrupted.
    """
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        response = await client.get(url)
        response.raise_for_status()
        pdf_bytes = response.content

    text = extract_text_from_pdf_bytes(pdf_bytes)
    logger.info(
        "pdf_fetched",
        url=url,
        pdf_size=len(pdf_bytes),
        text_length=len(text),
    )
    return pdf_bytes, text


def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    """Extract text content from PDF bytes.

    Args:
        pdf_bytes: Raw PDF file content.

    Returns:
        Extracted text from all pages, concatenated.
    """
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    pages: list[str] = []

    for page in doc:
        text = page.get_text("text")
        if text.strip():
            pages.append(text.strip())

    doc.close()
    return "\n\n".join(pages)
