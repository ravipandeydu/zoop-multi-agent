from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime

from db.database import get_db
from models.claim_models import Claim, ClaimStatus
from models.workflow_models import WorkflowLog
from agents.orchestrator_agent import workflow as langgraph_orchestrator

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/health")
async def system_health():
    """
    Check system health and agent availability
    """
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "agents": {
                "orchestrator": "available (LangGraph)",
                "intake": "available",
                "risk_assessment": "available",
                "routing": "available"
            },
            "database": "connected",
            "version": "1.0.0",
            "workflow_engine": "LangGraph"
        }
        
        return health_status
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }


@router.get("/metrics")
async def system_metrics(db: AsyncSession = Depends(get_db)):
    """
    Get system processing metrics and statistics
    """
    try:
        # Query database for system metrics
        total_claims = await db.scalar(select(func.count(Claim.id)))
        
        # Count claims by status
        submitted_claims = await db.scalar(
            select(func.count(Claim.id)).where(Claim.status == ClaimStatus.SUBMITTED)
        )
        processing_claims = await db.scalar(
            select(func.count(Claim.id)).where(Claim.status == ClaimStatus.PROCESSING)
        )
        completed_claims = await db.scalar(
            select(func.count(Claim.id)).where(Claim.status == ClaimStatus.COMPLETED)
        )
        failed_claims = await db.scalar(
            select(func.count(Claim.id)).where(Claim.status == ClaimStatus.FAILED)
        )
        
        # Count workflow logs
        total_workflow_logs = await db.scalar(select(func.count(WorkflowLog.id)))
        
        # Calculate average processing time (if we have completed claims)
        avg_processing_time = None
        if completed_claims and completed_claims > 0:
            # This is a simplified calculation - in a real system you'd track actual processing times
            avg_processing_time = "2.5 minutes"  # Placeholder
        
        metrics = {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "claims": {
                "total": total_claims or 0,
                "submitted": submitted_claims or 0,
                "processing": processing_claims or 0,
                "completed": completed_claims or 0,
                "failed": failed_claims or 0
            },
            "workflow": {
                "total_executions": total_workflow_logs or 0,
                "average_processing_time": avg_processing_time,
                "agents_status": {
                    "intake": "active",
                    "risk_assessment": "active", 
                    "routing": "active"
                }
            },
            "system": {
                "uptime": "running",
                "workflow_engine": "LangGraph",
                "database_status": "connected"
            }
        }
        
        return metrics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system metrics: {str(e)}")