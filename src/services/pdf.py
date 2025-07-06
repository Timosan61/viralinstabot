"""PDF generation service."""

import os
from pathlib import Path
from datetime import datetime
from typing import Optional
import asyncio
from jinja2 import Template
from weasyprint import HTML, CSS
from src.domain.models import AnalysisResult, QueryPayload
from src.utils.logger import get_logger
from src.utils.formatters import (
    format_number, format_currency, format_datetime, format_engagement_rate
)
from src.utils.config import config


logger = get_logger(__name__)


class PDFService:
    """Service for generating PDF reports."""
    
    def __init__(self):
        """Initialize PDF service."""
        self.template_path = Path("templates/report_mobile.html")
        self.reports_dir = Path("data/reports")
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.max_size_mb = config.limits.pdf_max_size_mb
    
    async def generate_report(
        self,
        analysis_result: AnalysisResult,
        user_id: int
    ) -> str:
        """
        Generate PDF report from analysis result.
        
        Args:
            analysis_result: Analysis data
            user_id: Telegram user ID
            
        Returns:
            Path to generated PDF file
        """
        try:
            # Load template
            template_content = self._load_template()
            
            # Prepare context data
            context = self._prepare_context(analysis_result)
            
            # Render HTML
            html_content = self._render_html(template_content, context)
            
            # Generate PDF
            pdf_path = await self._generate_pdf(html_content, user_id)
            
            # Check file size
            file_size_mb = pdf_path.stat().st_size / (1024 * 1024)
            if file_size_mb > self.max_size_mb:
                logger.warning(f"PDF size {file_size_mb:.1f}MB exceeds limit")
                # Try to optimize
                pdf_path = await self._optimize_pdf(pdf_path)
            
            logger.info(f"Generated PDF report: {pdf_path}")
            return str(pdf_path)
            
        except Exception as e:
            logger.error(f"Error generating PDF: {e}")
            raise
    
    def _load_template(self) -> str:
        """Load HTML template."""
        if not self.template_path.exists():
            raise FileNotFoundError(f"Template not found: {self.template_path}")
        
        with open(self.template_path, "r", encoding="utf-8") as f:
            return f.read()
    
    def _prepare_context(self, analysis_result: AnalysisResult) -> dict:
        """Prepare context data for template."""
        query = analysis_result.query
        
        # Find the top reel by views
        top_reel = max(analysis_result.reels, key=lambda r: r.views) if analysis_result.reels else None

        # Calculate total likes and comments
        total_likes = sum(reel.likes for reel in analysis_result.reels)
        total_comments = sum(reel.comments for reel in analysis_result.reels)
        
        # Format reels data for new template
        reels = []
        for i, reel in enumerate(analysis_result.reels, 1):
            is_top = reel.id == top_reel.id if top_reel else False
            reels.append({
                "id": reel.id,
                "index": i,
                "reelUrl": reel.url,
                "video_url": reel.video_url, # Pass video url for the handler
                "is_top_reel": is_top,
                "previewImage": reel.thumbnail_url or "https://via.placeholder.com/200x355",
                "author": {
                    "username": reel.author_username,
                    "avatar": reel.author_avatar_url
                },
                "metrics": {
                    "views": format_number(reel.views),
                    "likes": format_number(reel.likes),
                    "comments": str(reel.comments),
                    "er": f"{reel.engagement_rate:.2f}%"
                },
                "caption": reel.title or "Без описания",
                "ctaButton": {"label": "Сценарий"}
            })
        
        # Get username from first reel or use query topic
        username = analysis_result.reels[0].author_username if analysis_result.reels else f"@{query.topic}"
        
        # Get avatar from first reel or use default
        avatar_url = None
        if analysis_result.reels and analysis_result.reels[0].author_avatar_url:
            avatar_url = analysis_result.reels[0].author_avatar_url
        
        # Build context for new template
        context = {
            "header": {
                "title": "Аналитика Reels",
                "type": "user",
                "username": username,
                "avatar": avatar_url,  # Use actual avatar or None
                "metrics": {
                    "followers": 0,  # Will be updated when we have this data
                    "views": format_number(analysis_result.total_views),
                    "likes": format_number(total_likes),
                    "totalComments": total_comments,
                    "selectionSize": len(analysis_result.reels),
                    "period": f"{query.period} дней" if query.period else "Все время",
                    "reportDate": datetime.now().strftime("%d.%m.%Y"),
                    "averageER": f"{analysis_result.average_er:.1f}%"
                },
                "buttons": [
                    {"label": "Excel", "action": "download_excel"},
                    {"label": "CSV", "action": "download_csv"},
                    {"label": "JSON", "action": "download_json"}
                ]
            },
            "reels": reels
        }
        
        return context
    
    def _render_html(self, template_content: str, context: dict) -> str:
        """Render HTML from template."""
        template = Template(template_content)
        return template.render(**context)
    
    async def _generate_pdf(self, html_content: str, user_id: int) -> Path:
        """Generate PDF file from HTML."""
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{user_id}_{timestamp}.pdf"
        pdf_path = self.reports_dir / filename
        
        # Run WeasyPrint in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self._write_pdf,
            html_content,
            str(pdf_path)
        )
        
        return pdf_path
    
    def _write_pdf(self, html_content: str, output_path: str) -> None:
        """Write PDF file (blocking operation)."""
        try:
            # Generate PDF with minimal parameters to avoid library conflicts
            html_doc = HTML(string=html_content)
            
            # Try direct write without additional parameters
            with open(output_path, 'wb') as pdf_file:
                html_doc.write_pdf(pdf_file)
                
        except Exception as e:
            logger.error(f"WeasyPrint error: {e}")
            # Fallback: create a simple text-based PDF alternative
            self._create_fallback_pdf(html_content, output_path)
    
    def _create_fallback_pdf(self, html_content: str, output_path: str) -> None:
        """Create a simple fallback when WeasyPrint fails."""
        try:
            # Simple HTML to text conversion and basic PDF creation
            from html import unescape
            import re
            
            # Strip HTML tags and convert to plain text
            text = re.sub(r'<[^>]+>', '', html_content)
            text = unescape(text)
            
            # Create a minimal HTML for PDF
            simple_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: Arial; margin: 20px; }}
                    h1 {{ color: #333; }}
                </style>
            </head>
            <body>
                <h1>Vision Analysis Report</h1>
                <pre>{text}</pre>
            </body>
            </html>
            """
            
            # Try WeasyPrint again with simplified content
            simple_doc = HTML(string=simple_html)
            with open(output_path, 'wb') as pdf_file:
                simple_doc.write_pdf(pdf_file)
                
        except Exception as fallback_error:
            logger.error(f"Fallback PDF creation also failed: {fallback_error}")
            raise
    
    def _get_print_styles(self) -> str:
        """Get additional print styles."""
        return """
        @page {
            size: A4;
            margin: 10mm;
        }
        
        @media print {
            body {
                font-size: 10pt;
            }
            
            .page-break {
                page-break-before: always;
            }
            
            .no-print {
                display: none;
            }
        }
        """
    
    async def _optimize_pdf(self, pdf_path: Path) -> Path:
        """Optimize PDF size if needed."""
        # For now, just return the original
        # In production, could use tools like ghostscript
        return pdf_path
    
    def cleanup_old_reports(self, days: int = 30) -> int:
        """
        Clean up old PDF reports.
        
        Args:
            days: Delete reports older than this many days
            
        Returns:
            Number of deleted files
        """
        cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
        deleted_count = 0
        
        for pdf_file in self.reports_dir.glob("*.pdf"):
            try:
                if pdf_file.stat().st_mtime < cutoff_date:
                    pdf_file.unlink()
                    deleted_count += 1
            except Exception as e:
                logger.error(f"Error deleting {pdf_file}: {e}")
        
        return deleted_count


    async def create_scenario_report(
        self,
        user_id: int,
        vision_analysis: str,
        audio_transcript: Optional[str],
        scenario: str
    ) -> str:
        """
        Generate a PDF report for a generated scenario.
        
        Args:
            user_id: Telegram user ID
            vision_analysis: The text of the vision analysis.
            audio_transcript: The text of the audio transcript.
            scenario: The generated scenario text.
            
        Returns:
            Path to the generated PDF file.
        """
        try:
            # Load scenario template
            template_path = Path("templates/scenario_report.html")
            if not template_path.exists():
                raise FileNotFoundError(f"Template not found: {template_path}")
            with open(template_path, "r", encoding="utf-8") as f:
                template_content = f.read()

            # Prepare context
            context = {
                "vision_analysis": vision_analysis,
                "audio_transcript": audio_transcript,
                "scenario": scenario.replace("\n", "<br>")
            }
            
            # Render HTML
            html_content = self._render_html(template_content, context)
            
            # Generate PDF
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"scenario_{user_id}_{timestamp}.pdf"
            pdf_path = self.reports_dir / filename
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._write_pdf,
                html_content,
                str(pdf_path)
            )
            
            logger.info(f"Generated scenario report: {pdf_path}")
            return str(pdf_path)

        except Exception as e:
            logger.error(f"Error generating scenario PDF: {e}")
            raise

    async def create_vision_analysis_report(
        self,
        user_id: int,
        reel_data,
        vision_analysis: str,
        audio_analysis: str = "",
        patterns: str = "",
        scenario: str = ""
    ) -> str:
        """
        Generate a PDF report for Vision Analysis with scenario.
        
        Args:
            user_id: Telegram user ID
            reel_data: ReelData object with reel information
            vision_analysis: Vision analysis text
            audio_analysis: Audio analysis text
            patterns: Extracted patterns text
            scenario: Generated scenario text
            
        Returns:
            Path to the generated PDF file.
        """
        try:
            # Load vision analysis template (reuse scenario template for now)
            template_path = Path("templates/scenario_report.html")
            if not template_path.exists():
                raise FileNotFoundError(f"Template not found: {template_path}")
            with open(template_path, "r", encoding="utf-8") as f:
                template_content = f.read()

            # Prepare context with reel information
            context = {
                "title": f"AI Vision Анализ: {reel_data.title[:50]}..." if reel_data.title else "Vision Analysis",
                "reel_url": reel_data.url,
                "reel_stats": f"👀 {reel_data.views:,} | ❤️ {reel_data.likes:,} | 💬 {reel_data.comments:,}",
                "vision_analysis": vision_analysis.replace("\n", "<br>") if vision_analysis else "Анализ не выполнен",
                "audio_transcript": audio_analysis.replace("\n", "<br>") if audio_analysis else "Аудио анализ отсутствует",
                "patterns": patterns.replace("\n", "<br>") if patterns else "Паттерны не найдены", 
                "scenario": scenario.replace("\n", "<br>") if scenario else "Сценарий не сгенерирован"
            }
            
            # Render HTML
            html_content = self._render_html(template_content, context)
            
            # Generate PDF
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"vision_analysis_{user_id}_{timestamp}.pdf"
            pdf_path = self.reports_dir / filename
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._write_pdf,
                html_content,
                str(pdf_path)
            )
            
            logger.info(f"Generated vision analysis report: {pdf_path}")
            return str(pdf_path)

        except Exception as e:
            logger.error(f"Error generating vision analysis PDF: {e}")
            raise


# Global PDF service instance
pdf_service = PDFService()