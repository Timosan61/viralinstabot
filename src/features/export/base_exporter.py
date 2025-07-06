"""Base class for data exporters."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List
from pathlib import Path
import os
from datetime import datetime

from src.domain.models import AnalysisResult


class BaseExporter(ABC):
    """Abstract base class for data exporters."""
    
    def __init__(self, output_dir: str = "exports"):
        """Initialize exporter with output directory."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    @abstractmethod
    def export(self, data: AnalysisResult, raw_data: List[Dict[str, Any]]) -> Path:
        """Export data to specific format.
        
        Args:
            data: Processed analysis result
            raw_data: Raw data from Apify API
            
        Returns:
            Path to exported file
        """
        pass
    
    def _generate_filename(self, extension: str, username: str = None) -> str:
        """Generate unique filename with timestamp.
        
        Args:
            extension: File extension (e.g., 'xlsx', 'csv', 'json')
            username: Optional username for filename
            
        Returns:
            Generated filename
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if username:
            return f"reels_analysis_{username}_{timestamp}.{extension}"
        return f"reels_analysis_{timestamp}.{extension}"
    
    def _prepare_export_data(self, data: AnalysisResult, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prepare data for export in tabular format.
        
        Args:
            data: Processed analysis result
            raw_data: Raw data from Apify API
            
        Returns:
            List of dictionaries ready for export
        """
        export_data = []
        
        # Handle case when raw_data is empty or has fewer items
        raw_data = raw_data or []
        
        for i, reel in enumerate(data.reels, 1):
            # Get corresponding raw data if available
            raw_reel = raw_data[i-1] if i-1 < len(raw_data) else {}
            
            export_row = {
                "№": i,
                "URL": reel.url,
                "Автор": reel.author_username,
                "Название": reel.title or "Без описания",
                "Просмотры": reel.views,
                "Лайки": reel.likes,
                "Комментарии": reel.comments,
                "Репосты": reel.shares,
                "ER%": round(reel.engagement_rate, 2),
                "Дата": reel.date.strftime("%Y-%m-%d %H:%M"),
                "Хештеги": ", ".join(reel.hashtags) if reel.hashtags else "",
                "Транскрипция": reel.transcript or "",
                # Дополнительные поля из raw_data (если доступны)
                "ID": reel.id or raw_reel.get("id", ""),
                "Тип": raw_reel.get("type", "Reel"),
                "Превью": reel.thumbnail_url or raw_reel.get("thumbnail_url", ""),
                "Длительность": reel.duration or raw_reel.get("video_duration", 0),
                "Локация": raw_reel.get("location", {}).get("name", "") if isinstance(raw_reel.get("location"), dict) else "",
                "Музыка": raw_reel.get("music", {}).get("title", "") if isinstance(raw_reel.get("music"), dict) else "",
            }
            export_data.append(export_row)
        
        return export_data