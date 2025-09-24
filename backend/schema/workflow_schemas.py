from pydantic import BaseModel
from typing import List, Dict, Any


class WorkflowStatusResponse(BaseModel):
    """Schema for workflow status API responses"""
    claim_id: str
    status: str
    workflow_logs: List[Dict[str, Any]]
    agent_results: List[Dict[str, Any]]
    current_step: str
    progress_percentage: int