"""Tests for extraction confidence scoring."""

from src.extraction.confidence import compute_confidence
from src.extraction.schemas import ExtractedMenu, ExtractedMenuItem, ExtractedMenuSection


class TestComputeConfidence:
    """Tests for the confidence scoring function."""

    def test_empty_menu_low_confidence(self) -> None:
        menu = ExtractedMenu(restaurant_name="Empty")
        score = compute_confidence(menu, 1000)
        assert score < 0.3

    def test_good_menu_high_confidence(self) -> None:
        menu = ExtractedMenu(
            restaurant_name="Good Restaurant",
            menu_sections=[
                ExtractedMenuSection(
                    section_name="Main Course",
                    items=[
                        ExtractedMenuItem(
                            dish_name="Butter Chicken with creamy sauce", price=17.99
                        ),
                        ExtractedMenuItem(dish_name="Chicken Tikka Masala spicy", price=18.99),
                        ExtractedMenuItem(dish_name="Palak Paneer spinach curry", price=15.99),
                        ExtractedMenuItem(dish_name="Dal Makhani black lentils", price=14.99),
                        ExtractedMenuItem(dish_name="Lamb Rogan Josh curry", price=19.99),
                        ExtractedMenuItem(dish_name="Chana Masala chickpea", price=13.99),
                    ],
                ),
            ],
        )
        score = compute_confidence(menu, 2000)
        assert score >= 0.7

    def test_items_with_zero_prices_reduce_confidence(self) -> None:
        menu = ExtractedMenu(
            restaurant_name="Bad Prices",
            menu_sections=[
                ExtractedMenuSection(
                    section_name="Main",
                    items=[
                        ExtractedMenuItem(dish_name="Item A", price=0),
                        ExtractedMenuItem(dish_name="Item B", price=0),
                        ExtractedMenuItem(dish_name="Item C", price=15.99),
                    ],
                ),
            ],
        )
        score = compute_confidence(menu, 500)
        # Should be lower than a menu with all valid prices
        assert score < 0.8

    def test_unreasonable_prices_reduce_confidence(self) -> None:
        menu = ExtractedMenu(
            restaurant_name="Crazy Prices",
            menu_sections=[
                ExtractedMenuSection(
                    section_name="Main",
                    items=[
                        ExtractedMenuItem(dish_name="Item A", price=5000.00),
                        ExtractedMenuItem(dish_name="Item B", price=0.01),
                    ],
                ),
            ],
        )
        score = compute_confidence(menu, 500)
        assert score < 0.8

    def test_score_capped_at_one(self) -> None:
        menu = ExtractedMenu(
            restaurant_name="Perfect",
            menu_sections=[
                ExtractedMenuSection(
                    section_name="Section",
                    items=[
                        ExtractedMenuItem(
                            dish_name=f"Dish {i} with a long description", price=15.0 + i
                        )
                        for i in range(20)
                    ],
                ),
            ],
        )
        score = compute_confidence(menu, 500)
        assert score <= 1.0
