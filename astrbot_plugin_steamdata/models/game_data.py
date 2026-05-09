from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ReviewItem:
    recommended: bool
    review_text: str
    playtime_hours: float
    language: str


@dataclass
class GameData:
    appid: int
    name: str
    short_description: str = ""
    developers: list[str] = field(default_factory=list)
    publishers: list[str] = field(default_factory=list)
    genres: list[str] = field(default_factory=list)
    release_date: str = ""
    platforms: dict[str, bool] = field(default_factory=dict)

    is_free: bool = False
    price_formatted: str = ""
    discount_percent: int = 0
    original_price: str = ""

    current_players: int | None = None

    total_reviews: int = 0
    positive_rate: float = 0.0
    review_score_desc: str = ""
    reviews: list[ReviewItem] = field(default_factory=list)

    header_image_url: str = ""
    store_url: str = ""
