"""Integration tests for the extraction pipeline.

These tests require a running llama-server at LLM_HOST:LLM_PORT.
Marked with `integration` so they are skipped by default in CI.

Run explicitly:
    pytest tests/test_extraction_integration.py -m integration
"""

import asyncio

import pytest

from src.config.settings import Settings
from src.extraction.confidence import compute_confidence
from src.extraction.model_client import ExtractionModelClient
from src.extraction.prompts import MENU_EXTRACTION_SYSTEM, MENU_EXTRACTION_USER_TEMPLATE
from src.extraction.schemas import ExtractedMenu

SAMPLE_MENU = """
Bombay Palace Indian Restaurant

APPETIZERS
Samosa (2 pcs) .............. $6.99
Crispy pastry filled with spiced potatoes and peas
Vegetable Pakora ............ $7.99
Assorted vegetables dipped in chickpea batter and fried
Chicken Tikka ............... $12.99
Boneless chicken marinated in yogurt and spices, grilled in tandoor
Paneer Tikka (V) ............ $11.99
Cottage cheese marinated and grilled

MAIN COURSE - CHICKEN
Butter Chicken .............. $17.99
Tender chicken in creamy tomato sauce
Chicken Tikka Masala ........ $18.99
Grilled chicken in rich masala gravy
Chicken Korma ............... $17.99
Chicken cooked in mild cashew and cream sauce
Chicken Vindaloo ............ $18.99
Spicy chicken curry with potatoes

MAIN COURSE - LAMB
Lamb Rogan Josh ............. $19.99
Tender lamb in aromatic Kashmiri sauce
Lamb Vindaloo ............... $19.99
Spicy lamb curry Goan style
Goat Curry .................. $20.99
Bone-in goat in traditional curry sauce

MAIN COURSE - VEGETARIAN
Palak Paneer (V) ............ $15.99
Cottage cheese in creamy spinach sauce
Chana Masala (V) ............ $13.99
Chickpeas in spiced tomato gravy
Dal Makhani (V) ............. $14.99
Slow-cooked black lentils in butter and cream
Aloo Gobi (V) ............... $13.99
Potato and cauliflower with spices
Malai Kofta (V) ............. $15.99
Vegetable dumplings in creamy sauce

BREADS
Naan ....................... $3.99
Garlic Naan ................ $4.99
Butter Naan ................ $4.49
Cheese Naan ................ $5.99
Roti ....................... $2.99

RICE
Basmati Rice ............... $3.99
Jeera Rice ................. $4.99
Vegetable Biryani .......... $14.99
Chicken Biryani ............ $16.99
Lamb Biryani ............... $17.99

DESSERTS
Gulab Jamun ................ $5.99
Rasmalai ................... $6.99
Kheer ...................... $5.99
"""

EXPECTED_ITEM_COUNT = 30


def _is_server_reachable(settings: Settings) -> bool:
    """Check if the LLM server is running."""
    import httpx  # noqa: PLC0415

    try:
        resp = httpx.get(f"{settings.llm_base_url}/v1/models", timeout=3.0)
        return resp.status_code == 200  # noqa: TRY300
    except (httpx.ConnectError, httpx.ReadTimeout):
        return False


@pytest.fixture
def settings() -> Settings:
    """Build settings without reading .env (use defaults)."""
    return Settings(_env_file=None)  # type: ignore[call-arg]


@pytest.mark.integration
class TestExtractionIntegration:
    """Integration tests that hit the live model server."""

    def test_full_extraction(self, settings: Settings) -> None:
        """End-to-end: send sample menu → get structured output with high confidence."""
        if not _is_server_reachable(settings):
            pytest.skip(f"LLM server not reachable at {settings.llm_base_url}")

        result = asyncio.get_event_loop().run_until_complete(self._run_extraction(settings))
        menu, confidence = result

        # Structural assertions
        assert menu.restaurant_name, "restaurant_name must be non-empty"
        assert len(menu.menu_sections) >= 3, "should extract at least 3 sections"

        total_items = sum(len(s.items) for s in menu.menu_sections)
        assert total_items >= 20, f"expected >=20 items, got {total_items}"

        # Confidence must meet threshold
        assert confidence >= 0.8, f"confidence {confidence} below 0.8 threshold"

        # All items should have positive prices
        for section in menu.menu_sections:
            for item in section.items:
                assert item.price > 0, f"{item.dish_name} has non-positive price"

    def test_extraction_confidence_above_threshold(self, settings: Settings) -> None:
        """Confidence score should be at or above the configured threshold."""
        if not _is_server_reachable(settings):
            pytest.skip(f"LLM server not reachable at {settings.llm_base_url}")

        menu, confidence = asyncio.get_event_loop().run_until_complete(
            self._run_extraction(settings)
        )
        assert confidence >= settings.extraction_confidence_threshold

    @staticmethod
    async def _run_extraction(settings: Settings) -> tuple[ExtractedMenu, float]:
        """Shared helper: call the model and return menu + confidence."""
        client = ExtractionModelClient(settings)
        user_prompt = MENU_EXTRACTION_USER_TEMPLATE.format(
            source_type="text",
            restaurant_name="Bombay Palace Indian Restaurant",
            content=SAMPLE_MENU,
        )
        menu: ExtractedMenu = await client.extract(
            response_model=ExtractedMenu,
            system_prompt=MENU_EXTRACTION_SYSTEM,
            user_prompt=user_prompt,
        )
        confidence = compute_confidence(menu, len(SAMPLE_MENU))
        return menu, confidence
