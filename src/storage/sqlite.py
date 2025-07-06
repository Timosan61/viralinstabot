"""SQLite storage implementation."""

import json
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update, delete, and_, func
from src.storage.models import Base, UserModel, ReportModel, RequestLogModel
from src.domain.models import QueryPayload, AnalysisResult, Report, ReportStatus
from src.utils.logger import get_logger
from src.utils.config import config


logger = get_logger(__name__)


class Database:
    """Database manager."""
    
    def __init__(self, database_url: Optional[str] = None):
        """Initialize database."""
        self.database_url = database_url or config.database.url
        self.engine = create_async_engine(
            self.database_url,
            echo=config.debug,
            future=True
        )
        self.async_session = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    async def init_db(self) -> None:
        """Initialize database tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized")
    
    async def close(self) -> None:
        """Close database connection."""
        await self.engine.dispose()
    
    # User methods
    
    async def get_or_create_user(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
    ) -> UserModel:
        """Get or create user."""
        async with self.async_session() as session:
            # Try to get existing user
            result = await session.execute(
                select(UserModel).where(UserModel.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()
            
            if user:
                # Update user info if changed
                if username != user.username or first_name != user.first_name:
                    user.username = username
                    user.first_name = first_name
                    user.last_name = last_name
                    user.updated_at = datetime.utcnow()
                    await session.commit()
            else:
                # Create new user
                user = UserModel(
                    telegram_id=telegram_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name
                )
                session.add(user)
                await session.commit()
                logger.info(f"Created new user: {telegram_id}")
            
            return user
    
    async def get_user_requests_count(self, telegram_id: int) -> int:
        """Get user requests count."""
        async with self.async_session() as session:
            result = await session.execute(
                select(func.count(ReportModel.id))
                .join(UserModel, UserModel.id == ReportModel.user_id)
                .where(UserModel.telegram_id == telegram_id)
            )
            return result.scalar() or 0
    
    async def increment_user_requests(self, telegram_id: int) -> None:
        """Increment user requests count."""
        async with self.async_session() as session:
            await session.execute(
                update(UserModel)
                .where(UserModel.telegram_id == telegram_id)
                .values(requests_count=UserModel.requests_count + 1)
            )
            await session.commit()
    
    # Report methods
    
    async def create_report(
        self,
        user_id: int,
        query_payload: QueryPayload,
        price_rub: float
    ) -> ReportModel:
        """Create new report."""
        async with self.async_session() as session:
            report = ReportModel(
                user_id=user_id,
                topic=query_payload.topic,
                period=query_payload.period,
                geo=query_payload.geo,
                payload_json=json.dumps(query_payload.to_dict()),
                price_rub=price_rub,
                status=ReportStatus.PENDING
            )
            session.add(report)
            await session.commit()
            await session.refresh(report)
            logger.info(f"Created report {report.id} for user {user_id}")
            return report
    
    async def update_report(
        self,
        report_id: int,
        analysis_result: Optional[AnalysisResult] = None,
        pdf_path: Optional[str] = None,
        status: Optional[ReportStatus] = None,
        error_message: Optional[str] = None,
        usage_stats: Optional[dict] = None
    ) -> None:
        """Update report."""
        async with self.async_session() as session:
            values = {}
            
            if analysis_result:
                # Serialize reels data
                reels_data = []
                for reel in analysis_result.reels:
                    reel_dict = {
                        "id": reel.id,
                        "title": reel.title,
                        "author": reel.author,
                        "author_username": reel.author_username,
                        "url": reel.url,
                        "views": reel.views,
                        "likes": reel.likes,
                        "comments": reel.comments,
                        "shares": reel.shares,
                        "engagement_rate": reel.engagement_rate,
                        "date": reel.date.isoformat(),
                        "transcript": reel.transcript,
                        "hashtags": reel.hashtags,
                        "thumbnail_url": reel.thumbnail_url,
                        "duration": reel.duration,
                        "author_avatar_url": reel.author_avatar_url
                    }
                    reels_data.append(reel_dict)
                
                values["result_json"] = json.dumps({
                    "total_views": analysis_result.total_views,
                    "average_er": analysis_result.average_er,
                    "reels_count": len(analysis_result.reels),
                    "reels": reels_data,  # Include actual reels data
                    "popular_hashtags": analysis_result.popular_hashtags,
                    "insights": analysis_result.insights,
                    "recommendations": analysis_result.recommendations,
                    "usage_cost_usd": analysis_result.usage_cost_usd
                })
            
            if pdf_path:
                values["pdf_path"] = pdf_path
            
            if status:
                values["status"] = status
            
            if error_message:
                values["error_message"] = error_message
            
            if usage_stats:
                values["usage_stats_json"] = json.dumps(usage_stats)
            
            if values:
                await session.execute(
                    update(ReportModel)
                    .where(ReportModel.id == report_id)
                    .values(**values)
                )
                await session.commit()
                logger.info(f"Updated report {report_id}")
    
    async def get_report(self, report_id: int) -> Optional[ReportModel]:
        """Get report by ID."""
        async with self.async_session() as session:
            result = await session.execute(
                select(ReportModel).where(ReportModel.id == report_id)
            )
            return result.scalar_one_or_none()
    
    async def get_user_reports(
        self,
        telegram_id: int,
        limit: int = 10,
        offset: int = 0
    ) -> List[ReportModel]:
        """Get user reports."""
        async with self.async_session() as session:
            result = await session.execute(
                select(ReportModel)
                .join(UserModel, UserModel.id == ReportModel.user_id)
                .where(UserModel.telegram_id == telegram_id)
                .order_by(ReportModel.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            return result.scalars().all()
    
    async def get_last_user_report(self, user_id: int) -> Optional[ReportModel]:
        """Get last user report."""
        async with self.async_session() as session:
            result = await session.execute(
                select(ReportModel)
                .where(ReportModel.user_id == user_id)
                .where(ReportModel.status == ReportStatus.COMPLETED)
                .order_by(ReportModel.created_at.desc())
                .limit(1)
            )
            report = result.scalar_one_or_none()
            if report and report.result_json:
                # Deserialize the analysis result
                import json
                from src.domain.models import AnalysisResult, ReelData
                from datetime import datetime
                
                result_data = json.loads(report.result_json)
                
                # Create ReelData objects from stored data
                reels = []
                if 'reels' in result_data:
                    for reel_data in result_data['reels']:
                        reel = ReelData(
                            id=reel_data.get('id', ''),
                            title=reel_data.get('title', ''),
                            author=reel_data.get('author', ''),
                            author_username=reel_data.get('author_username', ''),
                            url=reel_data.get('url', ''),
                            views=reel_data.get('views', 0),
                            likes=reel_data.get('likes', 0),
                            comments=reel_data.get('comments', 0),
                            shares=reel_data.get('shares', 0),
                            engagement_rate=reel_data.get('engagement_rate', 0.0),
                            date=datetime.fromisoformat(reel_data.get('date', datetime.now().isoformat())),
                            transcript=reel_data.get('transcript'),
                            hashtags=reel_data.get('hashtags', []),
                            thumbnail_url=reel_data.get('thumbnail_url'),
                            duration=reel_data.get('duration'),
                            author_avatar_url=reel_data.get('author_avatar_url')
                        )
                        reels.append(reel)
                
                # Create AnalysisResult
                analysis_result = AnalysisResult(
                    query=QueryPayload(
                        topic=report.topic,
                        period=report.period,
                        geo=report.geo,
                        user_id=report.user_id
                    ),
                    reels=reels,
                    total_views=result_data.get('total_views', 0),
                    average_er=result_data.get('average_er', 0.0),
                    popular_hashtags=result_data.get('popular_hashtags', []),
                    insights=result_data.get('insights', []),
                    recommendations=result_data.get('recommendations', []),
                    usage_cost_usd=result_data.get('usage_cost_usd', 0.0),
                    created_at=report.created_at
                )
                
                # Store analysis result in report object for easier access
                report.analysis_result = analysis_result
                
            return report
    
    async def cleanup_old_reports(self, days: int = 30) -> int:
        """Delete reports older than specified days."""
        async with self.async_session() as session:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get reports to delete
            result = await session.execute(
                select(ReportModel)
                .where(ReportModel.created_at < cutoff_date)
            )
            reports_to_delete = result.scalars().all()
            
            # Delete reports
            if reports_to_delete:
                await session.execute(
                    delete(ReportModel)
                    .where(ReportModel.created_at < cutoff_date)
                )
                await session.commit()
                
                deleted_count = len(reports_to_delete)
                logger.info(f"Deleted {deleted_count} old reports")
                return deleted_count
            
            return 0
    
    # Request log methods
    
    async def log_request(
        self,
        user_id: int,
        request_type: str,
        request_text: Optional[str] = None,
        is_voice: bool = False,
        processing_time_ms: Optional[int] = None
    ) -> None:
        """Log user request."""
        async with self.async_session() as session:
            log = RequestLogModel(
                user_id=user_id,
                request_type=request_type,
                request_text=request_text,
                is_voice=is_voice,
                processing_time_ms=processing_time_ms
            )
            session.add(log)
            await session.commit()


# Global database instance
db = Database()