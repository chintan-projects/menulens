"""Test the extraction pipeline against a live llama-server.

Usage:
    python -m scripts.test_extraction
"""

import asyncio
import json
import time

from src.config.settings import get_settings
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


async def main() -> None:
    """Run extraction test against live model."""
    settings = get_settings()
    client = ExtractionModelClient(settings)

    user_prompt = MENU_EXTRACTION_USER_TEMPLATE.format(
        source_type="text",
        restaurant_name="Bombay Palace Indian Restaurant",
        content=SAMPLE_MENU,
    )

    print("Sending menu to LFM2-8B-A1B for extraction...")  # noqa: T201
    start = time.time()

    menu: ExtractedMenu = await client.extract(
        response_model=ExtractedMenu,
        system_prompt=MENU_EXTRACTION_SYSTEM,
        user_prompt=user_prompt,
    )

    elapsed = time.time() - start
    confidence = compute_confidence(menu, len(SAMPLE_MENU))

    print(f"\nExtraction completed in {elapsed:.1f}s")  # noqa: T201
    print(f"Confidence: {confidence}")  # noqa: T201
    print(f"Restaurant: {menu.restaurant_name}")  # noqa: T201
    print(f"Sections: {len(menu.menu_sections)}")  # noqa: T201

    total_items = 0
    for section in menu.menu_sections:
        print(f"\n  [{section.section_name}] ({len(section.items)} items)")  # noqa: T201
        for item in section.items:
            tags = f" ({', '.join(item.dietary_tags)})" if item.dietary_tags else ""
            print(f"    {item.dish_name}: ${item.price:.2f}{tags}")  # noqa: T201
            total_items += 1

    print(f"\nTotal items extracted: {total_items}")  # noqa: T201
    print("Expected items: ~30")  # noqa: T201

    # Dump full JSON
    print("\n--- Full JSON output ---")  # noqa: T201
    print(json.dumps(menu.model_dump(), indent=2))  # noqa: T201


if __name__ == "__main__":
    asyncio.run(main())
