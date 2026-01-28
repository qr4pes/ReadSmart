from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class AnalysisRequest(Base):
    """Model to track user analysis requests"""
    __tablename__ = "analysis_requests"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(2048), nullable=False)
    user_ip = Column(String(45), nullable=True)  # Support IPv6
    requested_at = Column(DateTime(timezone=True), server_default=func.now())

    # Analysis results
    is_out_of_context = Column(String(50), nullable=True)  # Yes/No/Uncertain
    is_propaganda = Column(String(50), nullable=True)  # Yes/No/Uncertain
    credibility_score = Column(Float, nullable=True)  # 0-100
    content_context = Column(Text, nullable=True)  # General description

    # Metadata
    analysis_duration = Column(Float, nullable=True)  # Seconds
    status = Column(String(20), default="pending")  # pending, completed, failed
    error_message = Column(Text, nullable=True)

    # Store detailed analysis results
    detailed_results = Column(JSON, nullable=True)

    def __repr__(self):
        return f"<AnalysisRequest(id={self.id}, url={self.url}, status={self.status})>"
