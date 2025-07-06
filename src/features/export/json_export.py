"""JSON export functionality."""

import json
from pathlib import Path
from typing import Any, Dict, List
from datetime import datetime

from .base_exporter import BaseExporter
from src.domain.models import AnalysisResult


class JsonExporter(BaseExporter):
    """Export data to JSON format."""
    
    def export(self, data: AnalysisResult, raw_data: List[Dict[str, Any]]) -> Path:
        """Export complete data to JSON file including all raw data.
        
        Args:
            data: Processed analysis result
            raw_data: Raw data from Apify API
            
        Returns:
            Path to exported JSON file
        """
        # Generate filename
        username = data.reels[0].author_username if data.reels else "unknown"
        filename = self._generate_filename("json", username.replace("@", ""))
        filepath = self.output_dir / filename
        
        # Prepare export data with both processed and raw data
        export_data = {
            "metadata": {
                "exported_at": datetime.now().isoformat(),
                "query": {
                    "topic": data.query.topic,
                    "period": data.query.period,
                    "geo": data.query.geo,
                    "user_id": data.query.user_id
                },
                "summary": {
                    "total_reels": len(data.reels),
                    "total_views": data.total_views,
                    "average_er": data.average_er,
                    "popular_hashtags": data.popular_hashtags,
                    "insights": data.insights,
                    "recommendations": data.recommendations,
                    "usage_cost_usd": data.usage_cost_usd
                }
            },
            "processed_data": [
                {
                    "index": i,
                    "id": reel.id,
                    "url": reel.url,
                    "title": reel.title,
                    "author": reel.author,
                    "author_username": reel.author_username,
                    "views": reel.views,
                    "likes": reel.likes,
                    "comments": reel.comments,
                    "shares": reel.shares,
                    "engagement_rate": reel.engagement_rate,
                    "hashtags": reel.hashtags,
                    "date": reel.date.isoformat(),
                    "transcript": reel.transcript
                }
                for i, reel in enumerate(data.reels, 1)
            ],
            "raw_data": raw_data
        }
        
        # Write JSON file with proper formatting
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)
        
        return filepath