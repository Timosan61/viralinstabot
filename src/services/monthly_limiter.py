"""Monthly rate limiter for user requests."""

from datetime import datetime, timedelta
from typing import Dict, Optional
import os
from src.utils.logger import get_logger


logger = get_logger(__name__)


class MonthlyLimiter:
    """Monthly request limiter."""
    
    def __init__(self):
        """Initialize monthly limiter."""
        self.user_monthly_requests: Dict[int, Dict[str, any]] = {}
        self.max_monthly_requests = int(os.getenv("MAX_REQUESTS_PER_MONTH", "10"))
    
    def check_monthly_limit(self, user_id: int) -> tuple[bool, int, Optional[datetime]]:
        """
        Check if user has reached monthly limit.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Tuple of (is_allowed, remaining_requests, reset_date)
        """
        now = datetime.now()
        current_month = now.strftime("%Y-%m")
        
        # Initialize user data if not exists
        if user_id not in self.user_monthly_requests:
            self.user_monthly_requests[user_id] = {
                "month": current_month,
                "count": 0,
                "first_request": now
            }
        
        user_data = self.user_monthly_requests[user_id]
        
        # Reset counter if new month
        if user_data["month"] != current_month:
            user_data["month"] = current_month
            user_data["count"] = 0
            user_data["first_request"] = now
        
        # Check limit
        remaining = self.max_monthly_requests - user_data["count"]
        
        if user_data["count"] >= self.max_monthly_requests:
            # Calculate reset date (first day of next month)
            next_month = now.replace(day=28) + timedelta(days=4)
            reset_date = next_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            logger.warning(f"Monthly limit exceeded for user {user_id}: {user_data['count']}/{self.max_monthly_requests}")
            return False, 0, reset_date
        
        return True, remaining, None
    
    def add_monthly_request(self, user_id: int) -> None:
        """Add request to user's monthly count."""
        now = datetime.now()
        current_month = now.strftime("%Y-%m")
        
        if user_id not in self.user_monthly_requests:
            self.user_monthly_requests[user_id] = {
                "month": current_month,
                "count": 0,
                "first_request": now
            }
        
        user_data = self.user_monthly_requests[user_id]
        
        # Reset if new month
        if user_data["month"] != current_month:
            user_data["month"] = current_month
            user_data["count"] = 0
            user_data["first_request"] = now
        
        user_data["count"] += 1
        logger.info(f"Added monthly request for user {user_id}: {user_data['count']}/{self.max_monthly_requests}")
    
    def get_monthly_usage(self, user_id: int) -> Dict[str, any]:
        """Get user's monthly usage statistics."""
        now = datetime.now()
        current_month = now.strftime("%Y-%m")
        
        if user_id not in self.user_monthly_requests:
            return {
                "used": 0,
                "limit": self.max_monthly_requests,
                "remaining": self.max_monthly_requests,
                "reset_date": None
            }
        
        user_data = self.user_monthly_requests[user_id]
        
        # Check if data is for current month
        if user_data["month"] != current_month:
            return {
                "used": 0,
                "limit": self.max_monthly_requests,
                "remaining": self.max_monthly_requests,
                "reset_date": None
            }
        
        # Calculate reset date
        next_month = now.replace(day=28) + timedelta(days=4)
        reset_date = next_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        return {
            "used": user_data["count"],
            "limit": self.max_monthly_requests,
            "remaining": max(0, self.max_monthly_requests - user_data["count"]),
            "reset_date": reset_date
        }


# Global monthly limiter instance
monthly_limiter = MonthlyLimiter()