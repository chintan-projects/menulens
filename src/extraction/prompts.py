"""Extraction prompts for different menu source types."""

MENU_EXTRACTION_SYSTEM = """You are a precise menu data extractor. Your job is to extract structured \
menu data from raw restaurant menu content.

RULES:
1. Extract EVERY dish with its name and price. Do not skip items.
2. Prices must be numeric (e.g., 14.99 not "$14.99"). If a price range like "12-15" is given, \
use the lower bound.
3. Group items into their menu sections (Appetizers, Entrees, etc.). If no sections exist, \
use "General" as the section name.
4. For dishes with size/style variants (small/large, half/full, lunch/dinner), capture each \
variant in price_variants and use the first/default as the main price.
5. Extract dietary tags when marked (V, VG, GF, etc.).
6. If the restaurant name appears in the content, extract it. Otherwise use "Unknown".
7. If you cannot determine a price for an item, skip that item rather than guessing.
8. Do NOT include beverages, drinks, or dessert toppings unless they are clearly separate \
menu items with their own prices."""


MENU_EXTRACTION_USER_TEMPLATE = """Extract all menu items from the following restaurant menu content.

Source type: {source_type}
Restaurant name (if known): {restaurant_name}

--- MENU CONTENT START ---
{content}
--- MENU CONTENT END ---

Extract the complete structured menu data."""
