"""Rate limiter for user requests."""

from datetime import datetime, timedelta
from typing import Dict
from src.domain.constants import MAX_REQUESTS_PER_USER
from src.utils.logger import get_logger


logger = get_logger(__name__)


class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self):
        """Initialize rate limiter."""
        self.user_requests: Dict[int, list[datetime]] = {}
        self.max_requests = MAX_REQUESTS_PER_USER
        self.time_window = timedelta(hours=24)
    
    def check_limit(self, user_id: int) -> tuple[bool, int]:
        """
        Check if user has reached rate limit.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Tuple of (is_allowed, remaining_requests)
        """
        now = datetime.now()
        
        # Clean old requests
        if user_id in self.user_requests:
            self.user_requests[user_id] = [
                req_time for req_time in self.user_requests[user_id]
                if now - req_time < self.time_window
            ]
        else:
            self.user_requests[user_id] = []
        
        # Check limit
        current_requests = len(self.user_requests[user_id])
        remaining = self.max_requests - current_requests
        
        if current_requests >= self.max_requests:
            logger.warning(f"Rate limit exceeded for user {user_id}")
            return False, 0
        
        return True, remaining
    
    def add_request(self, user_id: int) -> None:
        """Add request to user's history."""
        if user_id not in self.user_requests:
            self.user_requests[user_id] = []
        
        self.user_requests[user_id].append(datetime.now())
        logger.info(f"Added request for user {user_id}")
    
    def get_reset_time(self, user_id: int) -> datetime:
        """Get time when rate limit resets for user."""
        if user_id not in self.user_requests or not self.user_requests[user_id]:
            return datetime.now()
        
        oldest_request = min(self.user_requests[user_id])
        return oldest_request + self.time_window


# Global rate limiter instance
rate_limiter = RateLimiter()