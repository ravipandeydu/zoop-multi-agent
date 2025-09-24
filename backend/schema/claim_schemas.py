from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class ClaimData(BaseModel):
    """Schema for claim data used by agents"""
    claim_id: str
    type: str
    date: Optional[str] = None
    amount: float
    description: str
    customer_id: str
    policy_number: str
    incident_location: Optional[str] = None
    police_report: Optional[str] = None
    injuries_reported: bool = False
    other_party_involved: bool = False
    timestamp_submitted: str
    customer_tenure_days: Optional[int] = None
    previous_claims_count: int = 0


class ClaimSubmissionRequest(BaseModel):
    """Schema for claim submission API requests"""
    claim_id: str
    type: str
    date: Optional[str] = None  # Optional field
    amount: float
    description: str
    customer_id: str
    policy_number: str
    incident_location: Optional[str] = None  # Optional field
    police_report: Optional[str] = None  # Optional field
    injuries_reported: bool = False
    other_party_involved: bool = False
    timestamp_submitted: str
    customer_tenure_days: Optional[int] = None  # Optional field
    previous_claims_count: int = 0


class ClaimSubmissionResponse(BaseModel):
    """Schema for claim submission API responses"""
    success: bool
    message: str
    claim_id: str
    workflow_id: str = None
    processing_started: bool = False