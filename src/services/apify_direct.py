"""Direct Apify API service for Instagram analysis."""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime, timedelta
import httpx

from src.domain.models import AnalysisResult, ReelData
from src.utils.config import config
from src.utils.progress import ApifyProgressTracker

logger = logging.getLogger(__name__)


class ApifyDirectService:
    """Service for direct Apify API calls."""
    
    def __init__(self):
        """Initialize service."""
        self.api_token = config.api.apify_token
        self.base_url = "https://api.apify.com/v2"
        self.actor_id = "apify/instagram-scraper"
        
    async def analyze_account(self, username: str, period_days: int, sample_size: int, 
                            progress_callback: Optional[Callable] = None) -> AnalysisResult:
        """Analyze Instagram account reels."""
        # Limit sample size to maximum 10
        sample_size = min(sample_size, 10)
        logger.info(f"Analyzing account @{username} for {period_days} days, sample size: {sample_size}")
        
        # Clean username
        username = username.replace("@", "").strip()
        
        # Prepare input for Instagram Scraper
        input_data = {
            "directUrls": [f"https://www.instagram.com/{username}/reels/"],
            "resultsType": "posts",
            "resultsLimit": min(sample_size * 2, 20),  # Get more for filtering, max 20
            "addParentData": True
        }
        
        # Run actor and get results
        results = await self._run_actor(input_data, progress_callback)
        
        # Process results
        return await self._process_results(results, period_days, sample_size, f"@{username}")
    
    async def analyze_hashtag(self, hashtag: str, period_days: int, sample_size: int, 
                            progress_callback: Optional[Callable] = None) -> AnalysisResult:
        """Analyze Instagram hashtag reels."""
        # Limit sample size to maximum 10
        sample_size = min(sample_size, 10)
        logger.info(f"Analyzing hashtag #{hashtag} for {period_days} days, sample size: {sample_size}")
        
        # Clean hashtag
        hashtag = hashtag.replace("#", "").strip()
        
        # Prepare input
        input_data = {
            "hashtags": [hashtag],
            "resultsType": "posts", 
            "resultsLimit": min(sample_size * 3, 30),  # More buffer for non-reel posts, max 30
            "addParentData": True
        }
        
        # Run actor and get results
        results = await self._run_actor(input_data, progress_callback)
        
        # Process results
        return await self._process_results(results, period_days, sample_size, f"#{hashtag}")
    
    async def analyze_location(self, location: str, period_days: int, sample_size: int,
                             progress_callback: Optional[Callable] = None) -> AnalysisResult:
        """Analyze Instagram location reels."""
        # Limit sample size to maximum 10
        sample_size = min(sample_size, 10)
        logger.info(f"Analyzing location {location} for {period_days} days, sample size: {sample_size}")
        
        # First, search for location to get ID
        location_id = await self._search_location(location)
        if not location_id:
            raise ValueError(f"Location '{location}' not found")
        
        # Prepare input
        input_data = {
            "locationIds": [location_id],
            "resultsType": "posts",
            "resultsLimit": min(sample_size * 2, 20),  # Max 20
            "addParentData": True
        }
        
        # Run actor and get results
        results = await self._run_actor(input_data, progress_callback)
        
        # Process results
        return await self._process_results(results, period_days, sample_size, f"📍 {location}")
    
    async def analyze_reel_url(self, url: str, progress_callback: Optional[Callable] = None) -> AnalysisResult:
        """Analyze specific Instagram reel."""
        logger.info(f"Analyzing reel URL: {url}")
        
        # Extract shortcode from URL
        import re
        match = re.search(r'/reel/([A-Za-z0-9_-]+)', url)
        if not match:
            raise ValueError("Invalid Instagram Reel URL")
        
        shortcode = match.group(1)
        
        # Prepare input
        input_data = {
            "directUrls": [url],
            "resultsType": "details",
            "resultsLimit": 1,
            "addParentData": True
        }
        
        # Run actor and get results
        results = await self._run_actor(input_data, progress_callback)
        
        # Process single reel
        return await self._process_results(results, 0, 1, f"Reel {shortcode}")
    
    async def _run_actor(self, input_data: Dict[str, Any], progress_callback: Optional[Callable] = None) -> List[Dict[str, Any]]:
        """Run Apify actor with given input."""
        actor_url = self.actor_id.replace("/", "~")
        
        # Initialize progress tracker if callback provided
        tracker = None
        if progress_callback:
            tracker = ApifyProgressTracker(progress_callback)
            await tracker.update("init")
        
        async with httpx.AsyncClient() as client:
            # Start actor run
            if tracker:
                await tracker.update("send_request")
                
            response = await client.post(
                f"{self.base_url}/acts/{actor_url}/runs",
                headers={"Authorization": f"Bearer {self.api_token}"},
                json=input_data,
                timeout=30
            )
            
            if response.status_code == 403:
                if "usage hard limit exceeded" in response.text.lower():
                    raise Exception("Превышен месячный лимит использования сервиса")
                raise Exception(f"Access denied: {response.text}")
            
            response.raise_for_status()
            
            run_data = response.json()
            run_id = run_data["data"]["id"]
            
            if tracker:
                await tracker.update("send_request", 1.0)
            
            # Wait for completion
            if tracker:
                await self._wait_for_run_with_progress(client, run_id, tracker)
            else:
                await self._wait_for_run(client, run_id)
            
            # Get results
            if tracker:
                await tracker.update("fetch_results")
                
            results = await self._get_run_results(client, run_id)
            
            if tracker:
                await tracker.update("fetch_results", 1.0)
                
            return results
    
    async def _wait_for_run(self, client: httpx.AsyncClient, run_id: str, max_attempts: int = 90):
        """Wait for actor run to complete."""
        # Increased timeout: 90 attempts * 2s = 180s (3 minutes) max
        for _ in range(max_attempts):
            response = await client.get(
                f"{self.base_url}/actor-runs/{run_id}",
                headers={"Authorization": f"Bearer {self.api_token}"}
            )
            response.raise_for_status()
            
            status = response.json()["data"]["status"]
            
            if status == "SUCCEEDED":
                return
            elif status in ["FAILED", "ABORTED", "TIMED-OUT"]:
                raise Exception(f"Actor run {status}")
            
            await asyncio.sleep(2)
        
        raise Exception("Actor run timed out")
    
    async def _wait_for_run_with_progress(self, client: httpx.AsyncClient, run_id: str, tracker: ApifyProgressTracker, max_attempts: int = 90):
        """Wait for actor run to complete with progress tracking."""
        for attempt in range(max_attempts):
            response = await client.get(
                f"{self.base_url}/actor-runs/{run_id}",
                headers={"Authorization": f"Bearer {self.api_token}"}
            )
            response.raise_for_status()
            
            status = response.json()["data"]["status"]
            
            # Calculate sub-progress based on attempt
            sub_progress = min(attempt / max_attempts, 0.9)  # Max 90% for waiting
            await tracker.update("wait_actor", sub_progress)
            
            if status == "SUCCEEDED":
                await tracker.update("wait_actor", 1.0)
                return
            elif status in ["FAILED", "ABORTED", "TIMED-OUT"]:
                raise Exception(f"Actor run {status}")
            
            await asyncio.sleep(2)
        
        raise Exception("Actor run timed out")
    
    async def _get_run_results(self, client: httpx.AsyncClient, run_id: str) -> List[Dict[str, Any]]:
        """Get results from completed run."""
        response = await client.get(
            f"{self.base_url}/actor-runs/{run_id}/dataset/items",
            headers={"Authorization": f"Bearer {self.api_token}"}
        )
        response.raise_for_status()
        
        return response.json()
    
    async def _search_location(self, location_name: str) -> Optional[str]:
        """Search for Instagram location by name."""
        # For now, return a mock location ID
        # In production, would need to use location search endpoint
        logger.warning(f"Location search not implemented, using mock data for: {location_name}")
        return "123456789"  # Mock location ID
    
    async def _process_results(
        self, 
        results: List[Dict[str, Any]], 
        period_days: int,
        sample_size: int,
        query_name: str
    ) -> AnalysisResult:
        """Process raw results into AnalysisResult."""
        
        # Filter only reels
        reels = self._filter_reels_only(results)
        
        # If no reels found, return early with message
        if not reels:
            return AnalysisResult(
                query=None,
                reels=[],
                total_views=0,
                average_er=0,
                popular_hashtags=[],
                insights=["Не найдено видео/Reels для анализа. Попробуйте другой запрос или увеличьте период."],
                recommendations=["Используйте более популярные хэштеги", "Попробуйте анализ другого аккаунта"],
                usage_cost_usd=self._calculate_cost(len(results))
            )
        
        # Sort all reels by views/likes first
        reels = self._sort_and_limit(reels, len(reels))  # Sort all first
        
        # Try to filter by date if period specified
        filtered_by_date = []
        if period_days > 0:
            filtered_by_date = self._filter_by_date(reels, period_days)
        
        # If we have enough reels within the period, use them
        if len(filtered_by_date) >= min(sample_size, 3):  # At least 3 reels
            reels = filtered_by_date
            period_message = f"за последние {period_days} дней"
        else:
            # Use all available reels, sorted by popularity
            logger.info(f"Not enough reels in {period_days} days period, using best available")
            period_message = "из всех доступных (недостаточно данных за выбранный период)"
        
        # Limit to sample size
        reels = reels[:sample_size]
        
        # Convert to ReelData objects
        reel_objects = []
        for reel in reels:
            reel_data = self._convert_to_reel_data(reel)
            if reel_data:
                reel_objects.append(reel_data)
        
        # Calculate metrics
        total_views = sum(r.views for r in reel_objects)
        avg_er = sum(r.engagement_rate for r in reel_objects) / len(reel_objects) if reel_objects else 0
        
        # Extract popular hashtags
        popular_hashtags = self._extract_popular_hashtags(reel_objects)
        
        # Generate insights and recommendations
        insights = self._generate_insights(reel_objects, query_name)
        if period_message != f"за последние {period_days} дней":
            insights.insert(0, f"ℹ️ Показаны лучшие Reels {period_message}")
        
        recommendations = self._generate_recommendations(reel_objects)
        
        return AnalysisResult(
            query=None,  # Will be set later
            reels=reel_objects,
            total_views=total_views,
            average_er=avg_er,
            popular_hashtags=popular_hashtags,
            insights=insights,
            recommendations=recommendations,
            usage_cost_usd=self._calculate_cost(len(results))
        )
    
    def _filter_reels_only(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter only reel/video content."""
        reels = []
        for post in posts:
            product_type = post.get("productType", "")
            is_video = (
                post.get("type") == "Video" or
                post.get("isVideo") == True or
                product_type in ["clips", "igtv", "reel"] or
                (product_type == "feed" and post.get("videoViewCount") is not None)
            )
            
            if is_video:
                reels.append(post)
        
        logger.info(f"Filtered {len(reels)} reels from {len(posts)} posts")
        return reels
    
    def _filter_by_date(self, reels: List[Dict[str, Any]], period_days: int) -> List[Dict[str, Any]]:
        """Filter reels by date period."""
        cutoff_date = datetime.now() - timedelta(days=period_days)
        
        filtered = []
        for reel in reels:
            timestamp = reel.get("timestamp")
            if timestamp:
                try:
                    post_date = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    if post_date > cutoff_date:
                        filtered.append(reel)
                except:
                    filtered.append(reel)  # Keep if can't parse date
        
        logger.info(f"Filtered {len(filtered)} reels within {period_days} days")
        return filtered
    
    def _sort_and_limit(self, reels: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
        """Sort reels by views/likes and limit to sample size."""
        # Sort by views first, then by likes
        reels.sort(
            key=lambda x: (
                x.get("videoViewCount", 0) or x.get("videoPlayCount", 0) or 0,
                x.get("likesCount", 0)
            ),
            reverse=True
        )
        
        return reels[:limit]
    
    def _convert_to_reel_data(self, post: Dict[str, Any]) -> Optional[ReelData]:
        """Convert Instagram post data to ReelData object."""
        try:
            # Extract metrics
            views = post.get("videoViewCount", 0) or post.get("videoPlayCount", 0) or 0
            likes = post.get("likesCount", 0)
            comments = post.get("commentsCount", 0)
            
            # If no views but has likes, estimate
            if views == 0 and likes > 0:
                views = likes * 10
            
            # Extract other data
            caption = post.get("caption", "") or ""
            url = post.get("url", "") or f"https://instagram.com/p/{post.get('shortCode', '')}"
            
            # Get thumbnail
            thumbnail_url = None
            if post.get("displayUrl"):
                thumbnail_url = post.get("displayUrl")
            elif post.get("thumbnailUrl"):
                thumbnail_url = post.get("thumbnailUrl")
            
            # Get video URL
            video_url = post.get("videoUrl")

            # Get author avatar URL
            author_avatar = None
            if post.get("ownerProfilePicUrl"):
                author_avatar = post.get("ownerProfilePicUrl")
            elif post.get("profilePictureUrl"):
                author_avatar = post.get("profilePictureUrl")
            
            # Create ReelData
            reel = ReelData(
                id=post.get("id", ""),
                title=caption[:100] if caption else "No caption",
                author=post.get("ownerFullName", "Unknown"),
                author_username=f"@{post.get('ownerUsername', 'unknown')}",
                url=url,
                video_url=video_url,
                views=views,
                likes=likes,
                comments=comments,
                shares=0,  # Instagram doesn't provide
                hashtags=self._extract_hashtags(caption),
                engagement_rate=0,
                date=datetime.fromisoformat(
                    post.get("timestamp", datetime.now().isoformat())
                ) if post.get("timestamp") else datetime.now(),
                transcript=post.get("alt"),
                thumbnail_url=thumbnail_url,
                duration=post.get("videoDuration", 0),
                author_avatar_url=author_avatar
            )
            
            # Calculate engagement rate
            if reel.views > 0:
                reel.engagement_rate = ((reel.likes + reel.comments) / reel.views) * 100
            
            return reel
            
        except Exception as e:
            logger.error(f"Error converting reel data: {e}")
            return None
    
    def _extract_hashtags(self, text: str) -> List[str]:
        """Extract hashtags from text."""
        import re
        hashtags = re.findall(r'#\w+', text)
        return [tag.lower() for tag in hashtags]
    
    def _extract_popular_hashtags(self, reels: List[ReelData]) -> List[Dict[str, Any]]:
        """Extract most popular hashtags from reels."""
        hashtag_counts = {}
        
        for reel in reels:
            for tag in reel.hashtags:
                hashtag_counts[tag] = hashtag_counts.get(tag, 0) + 1
        
        # Sort by count
        popular = sorted(hashtag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return [
            {"name": tag, "count": count, "er": 0}
            for tag, count in popular
        ]
    
    def _generate_insights(self, reels: List[ReelData], query_name: str) -> List[str]:
        """Generate insights from reels data."""
        insights = []
        
        if not reels:
            return ["Не найдено подходящих Reels для анализа"]
        
        # Top performing
        top_reel = max(reels, key=lambda r: r.views)
        insights.append(
            f"Топ Reel: {top_reel.views:,} просмотров, {top_reel.likes:,} лайков"
        )
        
        # Average metrics
        avg_views = sum(r.views for r in reels) / len(reels)
        avg_likes = sum(r.likes for r in reels) / len(reels)
        insights.append(
            f"В среднем: {int(avg_views):,} просмотров, {int(avg_likes):,} лайков"
        )
        
        # Duration insight
        durations = [r.duration for r in reels if r.duration > 0]
        if durations:
            avg_duration = sum(durations) / len(durations)
            insights.append(
                f"Средняя длительность: {int(avg_duration)} секунд"
            )
        
        # Best time (mock for now)
        insights.append("Лучшее время публикации: 19:00-21:00 MSK")
        
        return insights
    
    def _generate_recommendations(self, reels: List[ReelData]) -> List[str]:
        """Generate recommendations based on analysis."""
        recommendations = []
        
        if not reels:
            return ["Попробуйте другие ключевые слова или период"]
        
        # Hashtag recommendations
        popular_tags = self._extract_popular_hashtags(reels)
        if popular_tags:
            top_tags = [tag["name"] for tag in popular_tags[:5]]
            recommendations.append(
                f"Используйте хештеги: {', '.join(top_tags)}"
            )
        
        # Duration recommendation
        durations = [r.duration for r in reels if r.duration > 0]
        if durations:
            avg_duration = sum(durations) / len(durations)
            if avg_duration < 15:
                recommendations.append("Попробуйте более длинные видео (15-30 сек)")
            elif avg_duration > 30:
                recommendations.append("Оптимальная длительность: 15-30 секунд")
            else:
                recommendations.append(f"Продолжайте с длительностью ~{int(avg_duration)} сек")
        
        # Engagement tips
        high_er_reels = [r for r in reels if r.engagement_rate > 5]
        if high_er_reels:
            recommendations.append("Добавляйте призыв к действию в первые 3 секунды")
        
        return recommendations
    
    def _calculate_cost(self, items_processed: int) -> float:
        """Calculate estimated cost based on items processed."""
        # Rough estimate: $0.00025 per item
        return items_processed * 0.00025


# Global instance
apify_direct_service = ApifyDirectService()