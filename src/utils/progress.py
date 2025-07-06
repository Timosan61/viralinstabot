"""Progress tracking utilities for long-running operations."""

import asyncio
from typing import Optional, Callable
from datetime import datetime, timedelta


class ProgressTracker:
    """Track progress of multi-stage operations."""
    
    def __init__(self, message_updater: Callable):
        """Initialize progress tracker.
        
        Args:
            message_updater: Async function to update message with new text
        """
        self.message_updater = message_updater
        self.current_progress = 0
        self.current_stage = ""
        self.start_time = datetime.now()
        self.stages = {
            "init": (0, 5, "🔄 Инициализация запроса"),
            "send_request": (5, 10, "📤 Отправка запроса к API"),
            "wait_actor": (10, 70, "⏳ Анализ данных Instagram"),
            "fetch_results": (70, 80, "📥 Получение результатов"),
            "process_data": (80, 85, "🔍 Обработка данных"),
            "generate_pdf": (85, 95, "📄 Генерация PDF отчета"),
            "save_db": (95, 100, "💾 Сохранение результатов")
        }
        
    async def update(self, stage: str, sub_progress: float = 0.0):
        """Update progress for a specific stage.
        
        Args:
            stage: Stage identifier
            sub_progress: Progress within the stage (0.0 to 1.0)
        """
        if stage not in self.stages:
            return
            
        start_pct, end_pct, description = self.stages[stage]
        stage_range = end_pct - start_pct
        
        # Calculate overall progress
        self.current_progress = int(start_pct + (stage_range * sub_progress))
        self.current_stage = description
        
        # Create progress bar
        progress_bar = self._create_progress_bar(self.current_progress)
        
        # Calculate elapsed and estimated time
        elapsed = datetime.now() - self.start_time
        elapsed_seconds = elapsed.total_seconds()
        
        # Estimate remaining time (simple linear estimation)
        if self.current_progress > 0:
            total_estimated = (elapsed_seconds / self.current_progress) * 100
            remaining_seconds = total_estimated - elapsed_seconds
            remaining_text = self._format_time(remaining_seconds)
        else:
            remaining_text = "вычисляется..."
        
        # Format message
        if self.current_progress < 100:
            text = (
                f"{self.current_stage}\n"
                f"📊 Прогресс: {self.current_progress}%\n"
                f"{progress_bar}\n"
                f"⏱ Осталось: ~{remaining_text}"
            )
        else:
            text = (
                f"✅ Анализ завершен!\n"
                f"{progress_bar} 100%\n"
                f"⏱ Время выполнения: {self._format_time(elapsed_seconds)}"
            )
        
        # Update message
        try:
            await self.message_updater(text)
        except Exception:
            # Ignore update errors (e.g., message not modified)
            pass
    
    def _create_progress_bar(self, progress: int, width: int = 10) -> str:
        """Create visual progress bar."""
        filled = int((progress / 100) * width)
        empty = width - filled
        return f"[{'█' * filled}{'░' * empty}]"
    
    def _format_time(self, seconds: float) -> str:
        """Format seconds into human-readable time."""
        if seconds < 0:
            return "0 сек"
        
        if seconds < 60:
            return f"{int(seconds)} сек"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            secs = int(seconds % 60)
            return f"{minutes} мин {secs} сек"
        else:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            return f"{hours} ч {minutes} мин"


class ApifyProgressTracker(ProgressTracker):
    """Progress tracker specifically for Apify actor runs."""
    
    async def track_actor_run(self, client, run_id: str, max_attempts: int = 90):
        """Track progress of Apify actor run.
        
        Args:
            client: HTTP client
            run_id: Apify run ID
            max_attempts: Maximum attempts to check status
            
        Returns:
            Final status of the run
        """
        base_url = "https://api.apify.com/v2"
        
        for attempt in range(max_attempts):
            response = await client.get(
                f"{base_url}/actor-runs/{run_id}",
                headers={"Authorization": f"Bearer {client.headers.get('Authorization', '')}"}
            )
            response.raise_for_status()
            
            data = response.json()["data"]
            status = data["status"]
            
            # Calculate sub-progress based on attempt
            sub_progress = min(attempt / max_attempts, 0.9)  # Max 90% for waiting
            await self.update("wait_actor", sub_progress)
            
            if status == "SUCCEEDED":
                await self.update("wait_actor", 1.0)
                return status
            elif status in ["FAILED", "ABORTED", "TIMED-OUT"]:
                raise Exception(f"Actor run {status}")
            
            await asyncio.sleep(2)
        
        raise Exception("Actor run timed out")