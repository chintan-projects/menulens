"""SQLAlchemy ORM models matching the MenuLens data model.

Schema follows PRD Section 8 with PostGIS geography and pgvector embeddings.
"""

import uuid
from datetime import datetime

from geoalchemy2 import Geography
from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, DateTime, Float, Index, Numeric, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


class Restaurant(Base):
    """A restaurant with its location and metadata."""

    __tablename__ = "restaurants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    location: Mapped[str] = mapped_column(
        Geography(geometry_type="POINT", srid=4326), nullable=False
    )
    address: Mapped[str | None] = mapped_column(Text)
    cuisine_types: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    google_place_id: Mapped[str | None] = mapped_column(Text, unique=True)
    website_url: Mapped[str | None] = mapped_column(Text)
    menu_source_urls: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    price_tier: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    snapshots: Mapped[list["MenuSnapshot"]] = relationship(back_populates="restaurant")
    menu_items: Mapped[list["MenuItem"]] = relationship(back_populates="restaurant")

    __table_args__ = (Index("idx_restaurants_location", "location", postgresql_using="gist"),)


class MenuSnapshot(Base):
    """A point-in-time capture of a restaurant's menu."""

    __tablename__ = "menu_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    restaurant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(Text, nullable=False)
    raw_content_path: Mapped[str | None] = mapped_column(Text)
    extraction_model: Mapped[str | None] = mapped_column(Text)
    extraction_confidence: Mapped[float | None] = mapped_column(Float)
    extracted_data: Mapped[dict] = mapped_column(JSONB, nullable=False)  # type: ignore[assignment]
    is_latest: Mapped[bool] = mapped_column(Boolean, default=True)

    restaurant: Mapped["Restaurant"] = relationship(back_populates="snapshots")
    items: Mapped[list["MenuItem"]] = relationship(back_populates="snapshot")


class CanonicalDish(Base):
    """A normalized dish identity for cross-restaurant comparison."""

    __tablename__ = "canonical_dishes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    canonical_name: Mapped[str] = mapped_column(Text, nullable=False)
    cuisine: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str | None] = mapped_column(Text)
    aliases: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    embedding = mapped_column(Vector(384))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    menu_items: Mapped[list["MenuItem"]] = relationship(back_populates="canonical_dish")


class MenuItem(Base):
    """A specific dish on a specific restaurant's menu at a point in time."""

    __tablename__ = "menu_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    snapshot_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    restaurant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    canonical_dish_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    dish_name: Mapped[str] = mapped_column(Text, nullable=False)
    section_name: Mapped[str | None] = mapped_column(Text)
    price: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)  # type: ignore[assignment]
    price_variants: Mapped[dict | None] = mapped_column(JSONB)  # type: ignore[assignment]
    description: Mapped[str | None] = mapped_column(Text)
    dietary_tags: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    currency: Mapped[str] = mapped_column(Text, default="USD")
    is_current: Mapped[bool] = mapped_column(Boolean, default=True)

    snapshot: Mapped["MenuSnapshot"] = relationship(back_populates="items")
    restaurant: Mapped["Restaurant"] = relationship(back_populates="menu_items")
    canonical_dish: Mapped["CanonicalDish | None"] = relationship(back_populates="menu_items")

    __table_args__ = (
        Index("idx_menu_items_restaurant_dish", "restaurant_id", "canonical_dish_id", "is_current"),
        Index(
            "idx_menu_items_canonical_current",
            "canonical_dish_id",
            postgresql_where="is_current = TRUE",
        ),
    )
