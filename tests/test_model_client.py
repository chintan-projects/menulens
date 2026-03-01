"""Tests for ExtractionModelClient."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.config.settings import Settings
from src.extraction.model_client import ExtractionModelClient, FallbackNotConfiguredError
from src.extraction.schemas import ExtractedMenu, ExtractedMenuItem, ExtractedMenuSection


def _make_settings(
    *,
    anthropic_key: str = "",
    llm_host: str = "localhost",
    llm_port: int = 8081,
) -> Settings:
    """Create a Settings instance with overrides for testing."""
    return Settings(
        _env_file=None,  # type: ignore[call-arg]
        anthropic_api_key=anthropic_key,
        llm_host=llm_host,
        llm_port=llm_port,
    )


def _sample_menu() -> ExtractedMenu:
    """Build a sample extracted menu for mock returns."""
    return ExtractedMenu(
        restaurant_name="Test Restaurant",
        menu_sections=[
            ExtractedMenuSection(
                section_name="Mains",
                items=[
                    ExtractedMenuItem(dish_name="Butter Chicken", price=17.99),
                ],
            )
        ],
    )


class TestExtractionModelClientInit:
    """Initialization and configuration tests."""

    def test_creates_primary_client(self) -> None:
        settings = _make_settings()
        client = ExtractionModelClient(settings)
        assert client._primary_model == "lfm2-8b-a1b"
        assert client._primary_client is not None

    def test_no_fallback_without_api_key(self) -> None:
        settings = _make_settings(anthropic_key="")
        client = ExtractionModelClient(settings)
        assert client._fallback_client is None
        assert client._fallback_model is None

    def test_fallback_configured_with_api_key(self) -> None:
        settings = _make_settings(anthropic_key="sk-test-key")
        client = ExtractionModelClient(settings)
        assert client._fallback_client is not None
        assert client._fallback_model == "claude-sonnet-4-20250514"

    def test_uses_computed_base_url(self) -> None:
        settings = _make_settings(llm_host="10.0.0.1", llm_port=9090)
        assert settings.llm_base_url == "http://10.0.0.1:9090"


class TestExtractionModelClientExtract:
    """Extraction call routing and fallback tests."""

    @pytest.mark.asyncio
    async def test_primary_success(self) -> None:
        settings = _make_settings()
        client = ExtractionModelClient(settings)

        expected = _sample_menu()
        mock_create = AsyncMock(return_value=expected)
        client._primary_client = MagicMock()
        client._primary_client.chat.completions.create = mock_create

        result = await client.extract(
            response_model=ExtractedMenu,
            system_prompt="Extract menu",
            user_prompt="Here is a menu",
        )

        assert result.restaurant_name == "Test Restaurant"
        assert len(result.menu_sections) == 1
        mock_create.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_primary_fails_no_fallback_raises(self) -> None:
        settings = _make_settings(anthropic_key="")
        client = ExtractionModelClient(settings)

        client._primary_client = MagicMock()
        client._primary_client.chat.completions.create = AsyncMock(
            side_effect=ConnectionError("server down")
        )

        with pytest.raises(ConnectionError, match="server down"):
            await client.extract(
                response_model=ExtractedMenu,
                system_prompt="Extract menu",
                user_prompt="Here is a menu",
            )

    @pytest.mark.asyncio
    async def test_primary_fails_fallback_succeeds(self) -> None:
        settings = _make_settings(anthropic_key="sk-test")
        client = ExtractionModelClient(settings)

        expected = _sample_menu()

        # Primary fails
        client._primary_client = MagicMock()
        client._primary_client.chat.completions.create = AsyncMock(
            side_effect=ConnectionError("server down")
        )

        # Fallback succeeds
        mock_fallback_create = AsyncMock(return_value=expected)
        client._fallback_client = MagicMock()
        client._fallback_client.messages.create = mock_fallback_create

        result = await client.extract(
            response_model=ExtractedMenu,
            system_prompt="Extract menu",
            user_prompt="Here is a menu",
        )

        assert result.restaurant_name == "Test Restaurant"
        mock_fallback_create.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_use_fallback_flag_skips_primary(self) -> None:
        settings = _make_settings(anthropic_key="sk-test")
        client = ExtractionModelClient(settings)

        expected = _sample_menu()

        # Set up both clients
        mock_primary = AsyncMock()
        client._primary_client = MagicMock()
        client._primary_client.chat.completions.create = mock_primary

        mock_fallback = AsyncMock(return_value=expected)
        client._fallback_client = MagicMock()
        client._fallback_client.messages.create = mock_fallback

        result = await client.extract(
            response_model=ExtractedMenu,
            system_prompt="Extract",
            user_prompt="Menu",
            use_fallback=True,
        )

        assert result.restaurant_name == "Test Restaurant"
        mock_primary.assert_not_awaited()
        mock_fallback.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_fallback_not_configured_raises_typed_error(self) -> None:
        settings = _make_settings(anthropic_key="")
        client = ExtractionModelClient(settings)

        with pytest.raises(FallbackNotConfiguredError, match="ANTHROPIC_API_KEY"):
            await client._call_fallback(
                response_model=ExtractedMenu,
                system_prompt="Extract",
                user_prompt="Menu",
            )
