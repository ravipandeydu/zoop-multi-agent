from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.database import Base
from enum import Enum


class AgentType(str, Enum):
    INTAKE = "intake"
    RISK_ASSESSMENT = "risk_assessment"
    ROUTING = "routing"
    DOCUMENTATION = "documentation"
    ORCHESTRATOR = "orchestrator"


class WorkflowLog(Base):
    __tablename__ = "workflow_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(Integer, ForeignKey("claims.id"), nullable=False)
    agent_type = Column(String, nullable=False)
    status = Column(String, nullable=False)  # started, completed, failed
    started_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    
    # Relationships
    claim = relationship("Claim", back_populates="workflow_logs")


class AgentResult(Base):
    __tablename__ = "agent_results"
    
    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(Integer, ForeignKey("claims.id"), nullable=False)
    agent_type = Column(String, nullable=False)
    
    # Intake Agent Results
    validation_errors = Column(Text, nullable=True)  # JSON string of errors
    is_valid = Column(Boolean, default=True)
    
    # Risk Assessment Results
    risk_score = Column(Float, nullable=True)
    risk_level = Column(String, nullable=True)
    fraud_indicators = Column(Text, nullable=True)  # JSON string of indicators
    
    # Routing Results
    priority = Column(String, nullable=True)
    adjuster_tier = Column(String, nullable=True)
    processing_path = Column(String, nullable=True)
    
    # Documentation Results
    summary = Column(Text, nullable=True)
    documentation = Column(Text, nullable=True)  # Generated documentation content
    key_points = Column(Text, nullable=True)  # JSON string of key points
    
    # Common fields
    result_data = Column(Text, nullable=True)  # JSON string for additional data
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    claim = relationship("Claim", back_populates="agent_results")