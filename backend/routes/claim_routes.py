from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime
import logging
import json

from db.database import get_db
from models.claim_models import Claim, ClaimStatus
from models.workflow_models import WorkflowLog, AgentResult
from agents.orchestrator_agent import workflow as langgraph_orchestrator
from schema.claim_schemas import ClaimSubmissionRequest, ClaimSubmissionResponse

router = APIRouter(prefix="/api/claims", tags=["claims"])

# Initialize logger
logger = logging.getLogger(__name__)

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
        # Import the process_claim function
        from agents.orchestrator_agent import process_claim, WorkflowStatus
        import asyncio
        import functools
        
        # Create claim record in database first
        claim = Claim(
            claim_id=claim_data["claim_id"],
            type=claim_data["type"],
            date=claim_data.get("date"),  # Add date field
            amount=claim_data["amount"],
            description=claim_data["description"],
            customer_id=claim_data["customer_id"],
            policy_number=claim_data["policy_number"],
            incident_location=claim_data.get("incident_location"),
            police_report=claim_data.get("police_report"),
            injuries_reported=claim_data.get("injuries_reported", False),
            other_party_involved=claim_data.get("other_party_involved", False),
            timestamp_submitted=datetime.fromisoformat(claim_data["timestamp_submitted"].replace('Z', '+00:00')) if claim_data.get("timestamp_submitted") else datetime.now(),
            customer_tenure_days=claim_data.get("customer_tenure_days"),
            previous_claims_count=claim_data.get("previous_claims_count", 0),
            status=ClaimStatus.PROCESSING
        )
        
        db.add(claim)
        await db.commit()
        await db.refresh(claim)
        
        # Process the claim through the workflow in a thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(None, process_claim, claim_data)
        except Exception as workflow_error:
            logger.error(f"Workflow execution failed for {claim_data['claim_id']}: {str(workflow_error)}")
            result = {
                "error": str(workflow_error),
                "processing_status": "failed",
                "workflow_status": "failed"
            }
        
        # DEBUG: Log the workflow result
        logger.info(f"Workflow result for claim {claim_data['claim_id']}: {result}")
        logger.info(f"Workflow status: {result.get('workflow_status')}")
        logger.info(f"Error in result: {result.get('error')}")
        
        # Update claim status based on result
        workflow_status = result.get("workflow_status")
        logger.info(f"Checking workflow status: {workflow_status}")
        
        if workflow_status == "completed" or workflow_status == WorkflowStatus.COMPLETED.value:
            logger.info(f"Setting claim {claim_data['claim_id']} status to COMPLETED")
            claim.status = ClaimStatus.COMPLETED
            claim.risk_level = result.get("risk_level")
            claim.priority = result.get("priority")
            claim.adjuster_tier = result.get("adjuster_tier")
            # Convert validation_errors list to JSON string for SQLite
            validation_errors = result.get("validation_errors", [])
            claim.validation_errors = json.dumps(validation_errors) if validation_errors else None
        else:
            logger.info(f"Setting claim {claim_data['claim_id']} status to FAILED - workflow_status was: {workflow_status}")
            claim.status = ClaimStatus.FAILED
            
        await db.commit()
        
        # Store workflow logs and agent results
        if "workflow_log" in result:
            for log_entry in result["workflow_log"]:
                # Handle timestamp conversion safely
                timestamp = log_entry.get("timestamp")
                if timestamp:
                    if isinstance(timestamp, str):
                        started_at = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    elif isinstance(timestamp, (int, float)):
                        started_at = datetime.fromtimestamp(timestamp)
                    else:
                        started_at = datetime.now()
                else:
                    started_at = datetime.now()
                    
                workflow_log = WorkflowLog(
                    claim_id=claim.id,
                    agent_type=log_entry.get("agent", "unknown"),
                    status=log_entry.get("event", "unknown"),
                    started_at=started_at
                )
                db.add(workflow_log)
        
        # Store agent results
        for agent_name in ["intake", "risk_assessment", "routing"]:
            if f"{agent_name}_result" in result:
                agent_result = AgentResult(
                    claim_id=claim.id,
                    agent_type=agent_name
                )
                
                # Set specific fields based on agent type and result data
                result_data = result[f"{agent_name}_result"]
                if agent_name == "intake":
                    agent_result.validation_errors = json.dumps(result_data.get("validation_errors", [])) if result_data.get("validation_errors") else None
                    agent_result.is_valid = result_data.get("is_valid", True)
                elif agent_name == "risk_assessment":
                    agent_result.risk_score = result_data.get("risk_score")
                    agent_result.risk_level = result_data.get("risk_level")
                    agent_result.fraud_indicators = json.dumps(result_data.get("fraud_indicators", [])) if result_data.get("fraud_indicators") else None
                elif agent_name == "routing":
                    agent_result.priority = result_data.get("priority")
                    agent_result.adjuster_tier = result_data.get("adjuster_tier")
                    agent_result.processing_path = result_data.get("processing_path")
                
                db.add(agent_result)
        
        await db.commit()
        
    except Exception as e:
        print(f"Background workflow processing failed: {str(e)}")
        # Update claim status to failed if it exists
        try:
            claim = await db.scalar(select(Claim).where(Claim.claim_id == claim_data["claim_id"]))
            if claim:
                claim.status = ClaimStatus.FAILED
                await db.commit()
        except:
            pass


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
        
        # Parse validation errors if they exist
        validation_errors = []
        if claim.validation_errors:
            try:
                import json
                validation_errors = json.loads(claim.validation_errors)
            except:
                validation_errors = []

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
            "test_output": {
                "risk_level": claim.risk_level.value if claim.risk_level else None,
                "priority": claim.priority.value if claim.priority else None,
                "adjuster_tier": claim.adjuster_tier.value if claim.adjuster_tier else None,
                "validation_errors": validation_errors
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