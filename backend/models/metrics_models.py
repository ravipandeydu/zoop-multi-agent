from sqlalchemy import Column, Integer, Float, DateTime
from sqlalchemy.sql import func
from db.database import Base


class ProcessingMetrics(Base):
    __tablename__ = "processing_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, default=func.now())
    total_claims_processed = Column(Integer, default=0)
    average_processing_time_ms = Column(Float, default=0.0)
    success_rate = Column(Float, default=0.0)
    high_risk_claims_count = Column(Integer, default=0)
    fraud_detected_count = Column(Integer, default=0)