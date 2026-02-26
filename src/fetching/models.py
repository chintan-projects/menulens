"""Pydantic models for the fetching service."""

from datetime import datetime

from pydantic import BaseModel

from src.common.models import SourceType


class FetchResult(BaseModel):
    """Result of fetching menu content from a URL."""

    source_url: str
    source_type: SourceType
    raw_content: str
    cleaned_content: str
    fetched_at: datetime
    content_length: int
    raw_content_path: str | None = None
    fetch_success: bool = True
    error_message: str | None = None
