"""Domain models."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class QueryState(Enum):
    """Query processing states."""
    INITIAL = "initial"
    WAITING_TOPIC = "waiting_topic"
    WAITING_PERIOD = "waiting_period"
    WAITING_GEO = "waiting_geo"
    COMPLETE = "complete"


class ReportStatus(Enum):
    """Report generation status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class QueryPayload:
    """Query parameters for Apify."""
    topic: str
    period: int  # 7 or 30 days
    geo: str  # RU, US, WORLD, etc.
    user_id: int
    message_id: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "topic": self.topic,
            "period": self.period,
            "geo": self.geo,
            "user_id": self.user_id,
            "message_id": self.message_id
        }
    
    def to_apify_input(self, limit: int = 5) -> Dict[str, Any]:
        """Convert to Apify actor input."""
        # Instagram Reel Scraper requires username array
        # We'll search for accounts related to the topic
        usernames = []
        
        # Map topic to popular Instagram accounts
        # This is a simplified approach - in production you'd have a better mapping
        topic_accounts = {
            "фитнес": ["fitness", "fitnessmotivation", "fitnessaddict"],
            "коммуникации": ["communication", "socialmedia", "marketing"],
            "мода": ["fashion", "style", "fashionblogger"],
            "еда": ["food", "foodie", "recipes"],
            "путешествия": ["travel", "travelgram", "wanderlust"],
        }
        
        # Get accounts for topic or use topic as username
        topic_lower = self.topic.lower()
        if topic_lower in topic_accounts:
            usernames = topic_accounts[topic_lower]
        else:
            # Use topic as username search
            usernames = [self.topic, f"{self.topic}reels", f"{self.topic}videos"]
        
        return {
            "usernames": usernames[:3],  # Limit to 3 accounts
            "resultsLimit": limit
        }


@dataclass
class ReelData:
    """Instagram Reel data."""
    id: str
    title: str
    author: str
    author_username: str
    url: str
    video_url: Optional[str]
    views: int
    likes: int
    comments: int
    shares: int
    engagement_rate: float
    date: datetime
    transcript: Optional[str] = None
    hashtags: List[str] = None
    thumbnail_url: Optional[str] = None
    duration: Optional[int] = None  # in seconds
    author_avatar_url: Optional[str] = None  # Profile picture URL
    
    def __post_init__(self):
        if self.hashtags is None:
            self.hashtags = []
    
    @property
    def formatted_date(self) -> str:
        """Get formatted date string."""
        return self.date.strftime("%Y-%m-%d")
    
    @property
    def formatted_views(self) -> str:
        """Get formatted views count."""
        if self.views >= 1000000:
            return f"{self.views/1000000:.1f}M"
        elif self.views >= 1000:
            return f"{self.views/1000:.0f}K"
        return str(self.views)


@dataclass
class AnalysisResult:
    """Analysis result from Apify."""
    query: QueryPayload
    reels: List[ReelData]
    total_views: int
    average_er: float
    popular_hashtags: List[Dict[str, Any]]
    insights: List[str]
    recommendations: List[str]
    usage_cost_usd: float
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
    
    @property
    def cost_rub(self) -> float:
        """Calculate cost in RUB."""
        from src.domain.constants import USD_TO_RUB, PRICE_MULTIPLIER
        return self.usage_cost_usd * PRICE_MULTIPLIER * USD_TO_RUB


@dataclass
class UserRequest:
    """User request data."""
    user_id: int
    username: Optional[str]
    message: str
    is_voice: bool = False
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class Report:
    """Generated report data."""
    id: Optional[int]
    user_id: int
    query_payload: QueryPayload
    analysis_result: AnalysisResult
    pdf_path: str
    created_at: datetime
    price_rub: float
    status: ReportStatus = ReportStatus.COMPLETED