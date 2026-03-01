"""Menu extraction demo endpoint (no database required).

Accepts raw menu text, runs it through the LLM extraction pipeline,
and returns structured menu data with confidence scoring.
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from instructor.core import InstructorRetryException
from openai import APIConnectionError, APIStatusError, APITimeoutError
from pydantic import BaseModel, Field

from src.common.logger import get_logger
from src.config.settings import get_settings
from src.extraction.confidence import compute_confidence
from src.extraction.model_client import ExtractionModelClient, FallbackNotConfiguredError
from src.extraction.prompts import MENU_EXTRACTION_SYSTEM, MENU_EXTRACTION_USER_TEMPLATE
from src.extraction.schemas import ExtractedMenu

logger = get_logger(__name__)

router = APIRouter(prefix="/api/extract", tags=["extract"])

# Specific exceptions that can occur during LLM extraction:
# - APIConnectionError / APITimeoutError: llama-server unreachable or slow
# - APIStatusError: model returned an HTTP error (5xx, 4xx)
# - InstructorRetryException: schema validation failed after max retries
# - FallbackNotConfiguredError: primary failed and no Anthropic key set
_EXTRACTION_ERRORS = (
    APIConnectionError,
    APITimeoutError,
    APIStatusError,
    InstructorRetryException,
    FallbackNotConfiguredError,
)


class ExtractionRequest(BaseModel):
    """Request body for menu extraction."""

    menu_text: str = Field(
        min_length=20,
        max_length=30000,
        description="Raw menu content to extract from (plain text or cleaned HTML)",
    )
    restaurant_name: str = Field(
        default="Unknown",
        description="Restaurant name (helps guide extraction)",
    )
    source_type: str = Field(
        default="text",
        description="Source type: 'text', 'html', or 'pdf'",
    )


class ExtractionResponse(BaseModel):
    """Response with extracted menu and metadata."""

    menu: ExtractedMenu
    confidence: float
    total_items: int
    total_sections: int


@router.post("", response_model=ExtractionResponse)
async def extract_menu(request: ExtractionRequest) -> ExtractionResponse:
    """Extract structured menu data from raw text.

    Sends the content through the LLM extraction pipeline and returns
    structured sections, items, prices, and dietary tags with a confidence score.
    """
    settings = get_settings()
    client = ExtractionModelClient(settings)

    user_prompt = MENU_EXTRACTION_USER_TEMPLATE.format(
        source_type=request.source_type,
        restaurant_name=request.restaurant_name,
        content=request.menu_text[:15000],
    )

    try:
        menu: ExtractedMenu = await client.extract(
            response_model=ExtractedMenu,
            system_prompt=MENU_EXTRACTION_SYSTEM,
            user_prompt=user_prompt,
        )
    except _EXTRACTION_ERRORS as e:
        logger.error("extraction_endpoint_failed", error=str(e), error_type=type(e).__name__)
        return JSONResponse(  # type: ignore[return-value]
            status_code=502,
            content={"detail": f"Extraction model unavailable: {type(e).__name__}"},
        )

    confidence = compute_confidence(menu, len(request.menu_text))
    total_items = sum(len(s.items) for s in menu.menu_sections)

    logger.info(
        "extraction_api_success",
        confidence=confidence,
        sections=len(menu.menu_sections),
        items=total_items,
    )

    return ExtractionResponse(
        menu=menu,
        confidence=confidence,
        total_items=total_items,
        total_sections=len(menu.menu_sections),
    )
