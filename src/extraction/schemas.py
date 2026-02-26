"""Pydantic schemas for structured menu extraction.

These models define the target output schema for LLM-based extraction.
Used with the `instructor` library for schema-enforced generation.
"""

from pydantic import BaseModel, Field


class PriceVariant(BaseModel):
    """A size or style variant with its own price."""

    label: str = Field(description="Variant label, e.g. 'small', 'large', 'lunch', 'dinner'")
    price: float = Field(ge=0, description="Price for this variant in the menu's currency")


class ExtractedMenuItem(BaseModel):
    """A single dish extracted from a menu."""

    dish_name: str = Field(description="Name of the dish as written on the menu")
    description: str | None = Field(
        default=None,
        description="Description of the dish if provided",
    )
    price: float = Field(ge=0, description="Primary price of the dish")
    price_variants: list[PriceVariant] = Field(
        default_factory=list,
        description="Size/style variants with different prices",
    )
    currency: str = Field(default="USD", description="Currency code")
    dietary_tags: list[str] = Field(
        default_factory=list,
        description="Dietary tags like 'vegetarian', 'vegan', 'gluten-free'",
    )
    spice_level: str | None = Field(
        default=None,
        description="Spice level if indicated, e.g. 'mild', 'medium', 'hot'",
    )


class ExtractedMenuSection(BaseModel):
    """A section of the menu (e.g., 'Appetizers', 'Main Course')."""

    section_name: str = Field(description="Name of the menu section")
    items: list[ExtractedMenuItem] = Field(
        default_factory=list,
        description="Menu items in this section",
    )


class ExtractedMenu(BaseModel):
    """Complete structured extraction of a restaurant menu."""

    restaurant_name: str = Field(description="Name of the restaurant")
    menu_sections: list[ExtractedMenuSection] = Field(
        default_factory=list,
        description="Sections of the menu with their items",
    )
    extraction_notes: str | None = Field(
        default=None,
        description="Any notes about the extraction quality or issues",
    )
