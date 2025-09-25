from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.database import Base
from datetime import datetime
from enum import Enum


class ClaimStatus(str, Enum):
    SUBMITTED = "SUBMITTED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class Priority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    URGENT = "urgent"


class AdjusterTier(str, Enum):
    STANDARD = "standard"
    SENIOR = "senior"
    FRAUD_SPECIALIST = "fraud_specialist"


class Claim(Base):
    __tablename__ = "claims"
    
    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(String, unique=True, index=True, nullable=False)
    type = Column(String, nullable=False)
    date = Column(String, nullable=True)  # Can be null for incomplete claims
    amount = Column(Float, nullable=False)
    description = Column(Text, nullable=False)
    customer_id = Column(String, nullable=False)
    policy_number = Column(String, nullable=False)
    incident_location = Column(String, nullable=True)
    police_report = Column(String, nullable=True)
    injuries_reported = Column(Boolean, default=False)
    other_party_involved = Column(Boolean, default=False)
    timestamp_submitted = Column(DateTime, nullable=False)
    customer_tenure_days = Column(Integer, nullable=True)
    previous_claims_count = Column(Integer, default=0)
    
    # Processing status and results
    status = Column(SQLEnum(ClaimStatus), default=ClaimStatus.SUBMITTED)
    risk_level = Column(SQLEnum(RiskLevel), nullable=True)
    priority = Column(SQLEnum(Priority), nullable=True)
    adjuster_tier = Column(SQLEnum(AdjusterTier), nullable=True)
    validation_errors = Column(Text, nullable=True)  # JSON string of validation errors
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    workflow_logs = relationship("WorkflowLog", back_populates="claim")
    agent_results = relationship("AgentResult", back_populates="claim")