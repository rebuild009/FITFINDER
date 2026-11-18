from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .units import body_to_cm

Gender = Literal["men", "women", "unisex"]
FitPreference = Literal["snug", "regular", "relaxed"]
Sort = Literal["fit", "price_asc", "price_desc", "relevance"]


class Measurements(BaseModel):
    chest: float | None = Field(None, gt=0, lt=400, description="Chest or bust, fullest part")
    waist: float | None = Field(None, gt=0, lt=400)
    hips: float | None = Field(None, gt=0, lt=400)
    shoulder: float | None = Field(None, gt=0, lt=200, description="Shoulder point to shoulder point")
    inseam: float | None = Field(None, gt=0, lt=200)
    height: float | None = Field(None, gt=0, lt=300)


class FitProfile(BaseModel):
    unit: Literal["cm", "in"] = "cm"
    gender: Gender | None = None
    fit_preference: FitPreference = "regular"
    measurements: Measurements = Field(default_factory=Measurements)

    def body_cm(self) -> dict:
        return body_to_cm(self.measurements.model_dump(), self.unit)


class Filters(BaseModel):
    category: str | None = None
    gender: Gender | None = None
    min_price: float | None = Field(None, ge=0)
    max_price: float | None = Field(None, ge=0)
    colors: list[str] = Field(default_factory=list)
    materials: list[str] = Field(default_factory=list)
    brands: list[str] = Field(default_factory=list)
    size_label: str | None = None
    q: str | None = Field(None, max_length=200, description="Plain keyword filter")


class ParsedQuery(BaseModel):
    """Structured reading of a natural-language query. Measurements are in centimetres."""

    text: str = ""
    category: str | None = None
    gender: Gender | None = None
    colors: list[str] = Field(default_factory=list)
    materials: list[str] = Field(default_factory=list)
    min_price: float | None = None
    max_price: float | None = None
    measurements: dict[str, float] = Field(default_factory=dict)
    size_label: str | None = None
    fit_preference: FitPreference | None = None
    tags: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)


class MatchRequest(BaseModel):
    profile: FitProfile | None = None
    filters: Filters = Field(default_factory=Filters)
    only_fitting: bool = False
    sort: Sort = "fit"
    limit: int = Field(24, ge=1, le=100)
    offset: int = Field(0, ge=0)


class SearchRequest(MatchRequest):
    query: str = Field(..., min_length=1, max_length=300)


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    external_id: str
    source: str
    store: str
    brand: str
    title: str
    description: str
    category: str
    gender: str
    price: float
    currency: str
    colors: list[str]
    materials: list[str]
    tags: list[str]
    image_url: str | None
    product_url: str | None
    sizes_available: list[str]


class DimensionFitOut(BaseModel):
    dimension: str
    label: str
    body_cm: float
    range_cm: tuple[float, float]
    status: str
    delta_cm: float
    score: float
    note: str
    estimated: bool = False


class FitOut(BaseModel):
    score: int | None
    verdict: str
    verdict_label: str
    best_size: str | None
    summary: str
    confidence: str
    dimensions: list[DimensionFitOut] = Field(default_factory=list)
    alternatives: list[dict] = Field(default_factory=list)
    missing: list[str] = Field(default_factory=list)


class MatchItem(BaseModel):
    product: ProductOut
    fit: FitOut | None = None
    relevance: float = 0.0


class Applied(BaseModel):
    """What the search actually used after merging the query, the filters and the saved profile."""

    category: str | None = None
    gender: str | None = None
    min_price: float | None = None
    max_price: float | None = None
    colors: list[str] = Field(default_factory=list)
    materials: list[str] = Field(default_factory=list)
    brands: list[str] = Field(default_factory=list)
    size_label: str | None = None
    keywords: list[str] = Field(default_factory=list)
    fit_preference: str = "regular"
    measurements_cm: dict[str, float] = Field(default_factory=dict)


class MatchResponse(BaseModel):
    total: int
    checked: int
    fitting: int | None
    items: list[MatchItem]
    applied: Applied
    notes: list[str] = Field(default_factory=list)
    parsed: ParsedQuery | None = None
    parser: str | None = None


class SizeRow(BaseModel):
    size: str
    measurements: dict
    score: int | None
    verdict: str
    dimensions: list[DimensionFitOut]
    in_stock: bool


class ProductDetail(BaseModel):
    product: ProductOut
    size_chart_source: str
    fit: FitOut | None = None
    sizes: list[SizeRow]
