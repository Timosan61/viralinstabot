"""SQLAlchemy models."""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Text, 
    Boolean, JSON, Enum as SQLEnum, Index
)
from sqlalchemy.ext.declarative import declarative_base
from src.domain.models import ReportStatus


Base = declarative_base()


class UserModel(Base):
    """User model."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    requests_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index("idx_user_telegram_id", "telegram_id"),
    )


class ReportModel(Base):
    """Report model."""
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    topic = Column(String(255), nullable=False)
    period = Column(Integer, nullable=False)
    geo = Column(String(10), nullable=False)
    payload_json = Column(Text, nullable=False)  # JSON serialized QueryPayload
    result_json = Column(Text, nullable=True)    # JSON serialized AnalysisResult
    pdf_path = Column(String(500), nullable=True)
    price_rub = Column(Float, nullable=False)
    usage_stats_json = Column(Text, nullable=True)  # Apify usage statistics
    status = Column(SQLEnum(ReportStatus), default=ReportStatus.PENDING)
    error_message = Column(Text, nullable=True)
    
    __table_args__ = (
        Index("idx_report_user_id", "user_id"),
        Index("idx_report_created_at", "created_at"),
        Index("idx_report_status", "status"),
    )


class RequestLogModel(Base):
    """Request log model."""
    __tablename__ = "request_logs"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    request_type = Column(String(50), nullable=False)  # text, voice, callback
    request_text = Column(Text, nullable=True)
    is_voice = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    processing_time_ms = Column(Integer, nullable=True)
    
    __table_args__ = (
        Index("idx_request_log_user_id", "user_id"),
        Index("idx_request_log_created_at", "created_at"),
    )


class UserContextModel(Base):
    """User context model."""
    __tablename__ = "user_contexts"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    context_data = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index("idx_context_user_id", "user_id"),
        Index("idx_context_user_name", "user_id", "name"),
    )