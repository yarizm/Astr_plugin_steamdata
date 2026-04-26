from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ReviewItem:
    recommended: bool          # 好评/差评
    review_text: str           # 评论内容
    playtime_hours: float      # 游玩时长（小时）
    language: str              # 评论语言


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
    
    # 价格
    is_free: bool = False
    price_formatted: str = ""        # "¥198" 或 "Free"
    discount_percent: int = 0
    original_price: str = ""
    
    # 在线人数
    current_players: Optional[int] = None
    
    # 评分
    total_reviews: int = 0
    positive_rate: float = 0.0       # 0~100
    review_score_desc: str = ""      # "特别好评" 等
    
    # 评论列表
    reviews: list[ReviewItem] = field(default_factory=list)
    
    # 封面图
    header_image_url: str = ""
    
    # Store 页面链接
    store_url: str = ""
