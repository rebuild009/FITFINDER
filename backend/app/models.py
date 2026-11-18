from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base

JSONType = JSON().with_variant(JSONB(), "postgresql")


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    external_id: Mapped[str] = mapped_column(String(300), unique=True, index=True)
    source: Mapped[str] = mapped_column(String(40), index=True)  # seed | shopify
    store: Mapped[str] = mapped_column(String(200), index=True)
    brand: Mapped[str] = mapped_column(String(200), index=True)
    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(40), index=True)
    gender: Mapped[str] = mapped_column(String(20), index=True)  # men | women | unisex
    price: Mapped[float] = mapped_column(Float, index=True)
    currency: Mapped[str] = mapped_column(String(8), default="INR")
    colors: Mapped[list] = mapped_column(JSONType, default=list)
    materials: Mapped[list] = mapped_column(JSONType, default=list)
    tags: Mapped[list] = mapped_column(JSONType, default=list)
    image_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    product_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    sizes_available: Mapped[list] = mapped_column(JSONType, default=list)
    # {"unit": "cm", "source": "product|brand|standard", "sizes": [{"label": "XL", "measurements": {"chest": [lo, hi]}}]}
    size_chart: Mapped[dict] = mapped_column(JSONType, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    @property
    def search_text(self) -> str:
        parts = [self.title, self.description, self.brand, self.category, *self.colors, *self.materials, *self.tags]
        return " ".join(p for p in parts if p).lower()
