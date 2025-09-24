from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime

from db.database import get_db
from models.claim_models import Claim, ClaimStatus
from models.workflow_models import WorkflowLog, AgentResult
from agents.orchestrator_agent import workflow as langgraph_orchestrator
from schema.claim_schemas import ClaimSubmissionRequest, ClaimSubmissionResponse

router = APIRouter(prefix="/api/claims", tags=["claims"])

# Initialize LangGraph orchestrator
orchestrator = langgraph_orchestrator


@router.post("/submit", response_model=ClaimSubmissionResponse)
async def submit_claim(
    claim_data: ClaimSubmissionRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Submit a new claim for processing through the multi-agent workflow
    """
    try:
        # Convert Pydantic model to dict
        claim_dict = claim_data.model_dump()
        
        # Start workflow processing in background
        background_tasks.add_task(
            process_claim_workflow_background,
            claim_dict,
            db
        )
        
        return ClaimSubmissionResponse(
            success=True,
            message="Claim submitted successfully and processing started",
            claim_id=claim_data.claim_id,
            workflow_id=f"WF-{int(datetime.now().timestamp())}-{claim_data.claim_id}",
            processing_started=True
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit claim: {str(e)}")


async def process_claim_workflow_background(claim_data: Dict[str, Any], db: AsyncSession):
    """Background task to process claim workflow using LangGraph"""
    try:
        await orchestrator.process_claim_async(claim_data, db)
    except Exception as e:
        print(f"Background workflow processing failed: {str(e)}")


@router.get("/{claim_id}/status")
async def get_claim_status(claim_id: str, db: AsyncSession = Depends(get_db)):
    """
    Get the current processing status and workflow progress for a claim
    """
    try:
        # Query the database directly for claim status
        claim = await db.scalar(select(Claim).where(Claim.claim_id == claim_id))
        
        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")
        
        # Get workflow logs for this claim
        workflow_logs = await db.scalars(
            select(WorkflowLog).where(WorkflowLog.claim_id == claim.id).order_by(WorkflowLog.started_at.desc())
        )
        workflow_logs_list = workflow_logs.all()
        
        # Get agent results for this claim
        agent_results = await db.scalars(
            select(AgentResult).where(AgentResult.claim_id == claim.id)
        )
        agent_results_list = agent_results.all()
        
        # Build status response
        status_response = {
            "success": True,
            "claim_id": claim.claim_id,
            "status": claim.status.value,
            "created_at": claim.created_at.isoformat() if claim.created_at else None,
            "updated_at": claim.updated_at.isoformat() if claim.updated_at else None,
            "workflow_progress": {
                "total_steps": len(workflow_logs_list),
                "completed_steps": len([log for log in workflow_logs_list if log.status == "completed"]),
                "current_step": workflow_logs_list[0].agent_type if workflow_logs_list else None,
                "last_updated": workflow_logs_list[0].started_at.isoformat() if workflow_logs_list else None
            },
            "agent_results": [
                {
                    "agent_type": result.agent_type,
                    "risk_score": result.risk_score,
                    "risk_level": result.risk_level,
                    "priority": result.priority,
                    "adjuster_tier": result.adjuster_tier,
                    "processing_path": result.processing_path,
                    "is_valid": result.is_valid
                }
                for result in agent_results_list[:5]  # Latest 5 results
            ],
            "claim_details": {
                "type": claim.type,
                "amount": float(claim.amount) if claim.amount else None,
                "customer_id": claim.customer_id,
                "policy_number": claim.policy_number
            }
        }
        
        return status_response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get claim status: {str(e)}")


@router.get("")
async def list_claims(
    status: str = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """
    List all claims with optional status filtering
    """
    try:
        query = select(Claim)
        
        if status:
            try:
                status_enum = ClaimStatus(status.upper())
                query = query.where(Claim.status == status_enum)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        query = query.offset(offset).limit(limit).order_by(Claim.timestamp_submitted.desc())
        
        result = await db.execute(query)
        claims = result.scalars().all()
        
        # Get total count
        count_query = select(func.count(Claim.id))
        if status:
            count_query = count_query.where(Claim.status == status_enum)
        
        count_result = await db.execute(count_query)
        total_count = count_result.scalar()
        
        return {
            "claims": [
                {
                    "id": claim.id,
                    "claim_id": claim.claim_id,
                    "type": claim.type,
                    "amount": claim.amount,
                    "status": claim.status.value if claim.status else None,
                    "customer_id": claim.customer_id,
                    "timestamp_submitted": claim.timestamp_submitted.isoformat() if claim.timestamp_submitted else None,
                    "description": claim.description[:100] + "..." if len(claim.description or "") > 100 else claim.description
                }
                for claim in claims
            ],
            "total_count": total_count,
            "limit": limit,
            "offset": offset
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list claims: {str(e)}")