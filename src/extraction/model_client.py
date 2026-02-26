"""Model client abstraction for LLM-based extraction.

Supports multiple backends:
- Local models via llama-server (OpenAI-compatible API on port 8081)
- Claude API (Anthropic) as fallback
"""

from typing import TypeVar

import instructor
from anthropic import AsyncAnthropic
from openai import AsyncOpenAI
from pydantic import BaseModel

from src.common.logger import get_logger
from src.config.settings import Settings

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)


class ExtractionModelClient:
    """Unified client for calling extraction models.

    Wraps both OpenAI-compatible (llama-server/vLLM/ollama) and Anthropic backends
    with instructor for Pydantic schema enforcement.
    """

    def __init__(self, settings: Settings) -> None:
        """Initialize model clients from settings.

        Args:
            settings: Application settings with model configuration.
        """
        self._settings = settings
        self._primary_model = settings.extraction_model_primary

        # Primary: OpenAI-compatible client pointing at llama-server
        # Use JSON mode (not tool-calling) — llama-server with local models generates
        # JSON directly rather than using OpenAI function-calling format.
        openai_client = AsyncOpenAI(
            base_url=f"{settings.llm_base_url}/v1",
            api_key="not-needed",  # llama-server doesn't require an API key
        )
        self._primary_client = instructor.from_openai(openai_client, mode=instructor.Mode.JSON)

        # Fallback: Anthropic client
        if settings.anthropic_api_key:
            anthropic_client = AsyncAnthropic(api_key=settings.anthropic_api_key)
            self._fallback_client = instructor.from_anthropic(anthropic_client)
            self._fallback_model = settings.extraction_model_fallback
        else:
            self._fallback_client = None
            self._fallback_model = None

    async def extract(
        self,
        response_model: type[T],
        system_prompt: str,
        user_prompt: str,
        *,
        use_fallback: bool = False,
    ) -> T:
        """Run structured extraction using the configured model.

        Args:
            response_model: Pydantic model class defining the expected output schema.
            system_prompt: System-level instructions for the model.
            user_prompt: User-level prompt with the content to extract.
            use_fallback: If True, use the fallback model (Claude) instead of primary.

        Returns:
            An instance of response_model populated with extracted data.

        Raises:
            Exception: If extraction fails on both primary and fallback.
        """
        if use_fallback and self._fallback_client:
            return await self._call_fallback(response_model, system_prompt, user_prompt)

        try:
            return await self._call_primary(response_model, system_prompt, user_prompt)
        except Exception as e:
            logger.warning(
                "primary_model_failed",
                model=self._primary_model,
                error=str(e),
            )
            if self._fallback_client:
                logger.info("falling_back_to_anthropic", model=self._fallback_model)
                return await self._call_fallback(response_model, system_prompt, user_prompt)
            raise

    async def _call_primary(
        self,
        response_model: type[T],
        system_prompt: str,
        user_prompt: str,
    ) -> T:
        """Call the primary (local) model.

        Args:
            response_model: Expected output schema.
            system_prompt: System instructions.
            user_prompt: Content prompt.

        Returns:
            Extracted data as response_model instance.
        """
        result: T = await self._primary_client.chat.completions.create(
            model=self._primary_model,
            response_model=response_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_retries=2,
        )
        logger.info("primary_extraction_done", model=self._primary_model)
        return result

    async def _call_fallback(
        self,
        response_model: type[T],
        system_prompt: str,
        user_prompt: str,
    ) -> T:
        """Call the fallback (Anthropic) model.

        Args:
            response_model: Expected output schema.
            system_prompt: System instructions.
            user_prompt: Content prompt.

        Returns:
            Extracted data as response_model instance.
        """
        if not self._fallback_client or not self._fallback_model:
            raise RuntimeError("Fallback model not configured (missing ANTHROPIC_API_KEY)")

        result: T = await self._fallback_client.messages.create(
            model=self._fallback_model,
            response_model=response_model,
            max_tokens=4096,
            messages=[
                {"role": "user", "content": f"{system_prompt}\n\n{user_prompt}"},
            ],
            max_retries=2,
        )
        logger.info("fallback_extraction_done", model=self._fallback_model)
        return result
