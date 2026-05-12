from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class NewsItem:
    title: str
    url: str
    source: str
    published_at: str          # ISO 8601 string
    media_type: str            # "article" | "video" | "tweet" | "match_result" | "schedule"
    summary: Optional[str] = None
    image_url: Optional[str] = None
    embed_html: Optional[str] = None   # for tweets / youtube iframes
    players: list[str] = field(default_factory=list)
    tournaments: list[str] = field(default_factory=list)
    weight: int = 0            # 排序权重，越大越靠前


class BaseDataSource(ABC):
    @abstractmethod
    def fetch(self) -> list[NewsItem]:
        """抓取并返回 NewsItem 列表"""
        ...
