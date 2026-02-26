"""Tests for extraction Pydantic schemas."""

from src.extraction.schemas import (
    ExtractedMenu,
    ExtractedMenuItem,
    ExtractedMenuSection,
    PriceVariant,
)


class TestExtractedMenuItem:
    """Tests for ExtractedMenuItem schema."""

    def test_basic_item(self) -> None:
        item = ExtractedMenuItem(dish_name="Butter Chicken", price=17.99)
        assert item.dish_name == "Butter Chicken"
        assert item.price == 17.99
        assert item.currency == "USD"
        assert item.dietary_tags == []

    def test_item_with_variants(self) -> None:
        item = ExtractedMenuItem(
            dish_name="Biryani",
            price=14.99,
            price_variants=[
                PriceVariant(label="half", price=14.99),
                PriceVariant(label="full", price=22.99),
            ],
        )
        assert len(item.price_variants) == 2
        assert item.price_variants[0].label == "half"

    def test_item_with_dietary_tags(self) -> None:
        item = ExtractedMenuItem(
            dish_name="Palak Paneer",
            price=15.99,
            dietary_tags=["vegetarian"],
        )
        assert "vegetarian" in item.dietary_tags


class TestExtractedMenu:
    """Tests for ExtractedMenu schema."""

    def test_full_menu(self) -> None:
        menu = ExtractedMenu(
            restaurant_name="Test Restaurant",
            menu_sections=[
                ExtractedMenuSection(
                    section_name="Appetizers",
                    items=[
                        ExtractedMenuItem(dish_name="Samosa", price=6.99),
                    ],
                ),
                ExtractedMenuSection(
                    section_name="Main Course",
                    items=[
                        ExtractedMenuItem(dish_name="Butter Chicken", price=17.99),
                        ExtractedMenuItem(dish_name="Dal Makhani", price=14.99),
                    ],
                ),
            ],
        )
        assert menu.restaurant_name == "Test Restaurant"
        assert len(menu.menu_sections) == 2
        total_items = sum(len(s.items) for s in menu.menu_sections)
        assert total_items == 3

    def test_empty_menu(self) -> None:
        menu = ExtractedMenu(restaurant_name="Empty Place")
        assert menu.menu_sections == []
