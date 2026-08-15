from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# ── Search Profile models ────────────────────────────────────────────────────

class ManufacturerEntry(BaseModel):
    manufacturer_id: int
    models: list[int] = []


class RangeFilter(BaseModel):
    min: int
    max: int


class IdNameFilter(BaseModel):
    id: int
    name: str


class SearchFilters(BaseModel):
    year: RangeFilter
    price: RangeFilter
    km: RangeFilter
    engine_cc: RangeFilter
    hand: RangeFilter
    engine_types: list[IdNameFilter]
    gearbox: IdNameFilter
    owner_type: IdNameFilter
    price_only: bool = False
    image_only: bool = False


class SearchGroup(BaseModel):
    """One Yad2 search request: up to 4 manufacturers and up to 4 models total."""

    manufacturers: list[int]
    models: list[int] = []


class SearchProfile(BaseModel):
    profile_name: str
    source: str
    category: str
    cars: dict[str, ManufacturerEntry]
    filters: SearchFilters
    search_groups: list[SearchGroup] = []
    expected_yad2_query_params: dict[str, str] = {}
    notes: list[str] = []


# ── Metadata ─────────────────────────────────────────────────────────────────

class ManufacturerMetadata(BaseModel):
    id: int
    name_en: str
    name_he: str
    verification_status: str  # "verified_manual" | "manual_verify_once"


# ── Parser outputs ────────────────────────────────────────────────────────────

class SearchCardListing(BaseModel):
    listing_id: str
    listing_url_relative: str
    listing_url: str
    listing_type: str
    title: Optional[str] = None
    subtitle: Optional[str] = None
    year: Optional[int] = None
    hand: Optional[int] = None
    price: Optional[str] = None
    image_url: Optional[str] = None
    tags: list[str] = []
    raw_card_html_hash: str
    parsed_at: datetime
    source_flags: list[str] = []
    parser_provenance: str = "search_parser.parse_search_page"


class ListingImage(BaseModel):
    url: str
    index: int


class DetailListing(BaseModel):
    km: Optional[str] = None
    color: Optional[str] = None
    current_ownership: Optional[str] = None
    original_ownership: Optional[str] = None
    test_valid_until: Optional[str] = None
    gearbox: Optional[str] = None
    date_on_road: Optional[str] = None
    engine_type: Optional[str] = None
    body_type: Optional[str] = None
    seats: Optional[str] = None
    horse_power: Optional[str] = None
    engine_cc: Optional[str] = None
    combined_fuel_consumption: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    phone_available: bool = False
    images: list[ListingImage] = []
    parsed_at: datetime
    source_flags: list[str] = []
    parser_provenance: str = "detail_parser"


# ── Scoring models ────────────────────────────────────────────────────────────

class KeywordMatch(BaseModel):
    term: str
    category: str        # "hard_reject" | "soft_flags" | "positive"
    subcategory: str     # e.g. "taxi", "leasing_or_company", "condition"
    field_matched: str   # "description" | "tags"


class ScoreBreakdown(BaseModel):
    factors: dict[str, int] = {}

    @property
    def total(self) -> int:
        return sum(self.factors.values())


class ScoredListing(BaseModel):
    score: int
    score_breakdown: ScoreBreakdown
    positive_reasons: list[str] = []
    flags: list[str] = []
    decision: str  # "notify" | "skip" | "rejected"


# ── Telegram models ───────────────────────────────────────────────────────────

class TelegramPayload(BaseModel):
    text: str
    image_url: Optional[str] = None
    extra_image_urls: list[str] = []
