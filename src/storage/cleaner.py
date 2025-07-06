"""Database cleaner for old reports."""

import asyncio
import os
from pathlib import Path
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from src.storage.sqlite import db
from src.utils.logger import get_logger
from src.utils.config import config


logger = get_logger(__name__)


class ReportCleaner:
    """Clean old reports from database and filesystem."""
    
    def __init__(self):
        """Initialize cleaner."""
        self.scheduler = AsyncIOScheduler()
        self.retention_days = config.database.report_retention_days
        self.reports_dir = Path("data/reports")
    
    async def cleanup_reports(self) -> None:
        """Clean up old reports."""
        try:
            logger.info("Starting report cleanup")
            
            # Delete from database
            deleted_count = await db.cleanup_old_reports(self.retention_days)
            
            # Delete old PDF files
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            deleted_files = 0
            
            if self.reports_dir.exists():
                for pdf_file in self.reports_dir.glob("*.pdf"):
                    try:
                        # Check file modification time
                        file_mtime = datetime.fromtimestamp(pdf_file.stat().st_mtime)
                        if file_mtime < cutoff_date:
                            pdf_file.unlink()
                            deleted_files += 1
                    except Exception as e:
                        logger.error(f"Error deleting file {pdf_file}: {e}")
            
            logger.info(
                f"Cleanup completed: {deleted_count} records, "
                f"{deleted_files} files deleted"
            )
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def start(self) -> None:
        """Start scheduled cleanup."""
        # Run cleanup daily at 3 AM
        self.scheduler.add_job(
            self.cleanup_reports,
            trigger="cron",
            hour=3,
            minute=0,
            id="cleanup_reports",
            replace_existing=True
        )
        
        # Also run cleanup on startup
        self.scheduler.add_job(
            self.cleanup_reports,
            id="startup_cleanup",
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info("Report cleaner started")
    
    def stop(self) -> None:
        """Stop scheduled cleanup."""
        self.scheduler.shutdown()
        logger.info("Report cleaner stopped")


# Global cleaner instance
cleaner = ReportCleaner()