"""Tests for the dish taxonomy loader."""

from src.normalization.taxonomy import DishTaxonomy


class TestDishTaxonomy:
    """Tests for DishTaxonomy."""

    def test_load_indian_taxonomy(self) -> None:
        taxonomy = DishTaxonomy("indian")
        assert len(taxonomy.dishes) > 0

    def test_get_all_names_with_aliases(self) -> None:
        taxonomy = DishTaxonomy("indian")
        entries = taxonomy.get_all_names_with_aliases()
        assert len(entries) > 0

        # Check structure
        name, cuisine, category, aliases = entries[0]
        assert isinstance(name, str)
        assert cuisine == "indian"
        assert isinstance(aliases, list)

    def test_has_common_dishes(self) -> None:
        taxonomy = DishTaxonomy("indian")
        names = [d["canonical_name"] for d in taxonomy.dishes]
        assert "Butter Chicken" in names
        assert "Chicken Tikka Masala" in names
        assert "Naan" in names
        assert "Palak Paneer" in names

    def test_butter_chicken_aliases(self) -> None:
        taxonomy = DishTaxonomy("indian")
        butter_chicken = next(d for d in taxonomy.dishes if d["canonical_name"] == "Butter Chicken")
        aliases = butter_chicken["aliases"]
        assert "Murgh Makhani" in aliases

    def test_nonexistent_cuisine(self) -> None:
        taxonomy = DishTaxonomy("nonexistent")
        assert taxonomy.dishes == []
