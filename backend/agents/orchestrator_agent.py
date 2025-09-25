from langgraph.graph import StateGraph, END
from typing import Dict, Any, TypedDict, Literal
import asyncio
import logging
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from enum import Enum

# Import the detailed agents we wrote earlier
from agents.intake_agent import IntakeAgent
from agents.risk_assessment_agent import RiskAssessmentAgent
from agents.routing_agent import RoutingAgent

# Configure logging for workflow progress
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WorkflowStatus(Enum):
    """Workflow status enumeration"""
    INITIATED = "initiated"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY_PENDING = "retry_pending"

class AgentStatus(Enum):
    """Agent processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


# -------------------------------
# Define Enhanced State Schema
# -------------------------------

class WorkflowState(TypedDict):
    """Enhanced state schema for the workflow with comprehensive tracking"""
    # Original claim data
    claim_id: str
    type: str
    date: str
    amount: float
    description: str
    customer_id: str
    policy_number: str
    incident_location: str
    police_report: str
    injuries_reported: bool
    other_party_involved: bool
    timestamp_submitted: str
    customer_tenure_days: int
    previous_claims_count: int
    
    # Processing results
    validation_errors: list
    risk_score: int
    risk_level: str
    risk_reasons: list
    priority: str
    adjuster_tier: str
    error: str
    
    # Workflow control and tracking
    processing_mode: str  # "fast_track", "standard", "complex"
    parallel_results: dict  # Store results from parallel processing
    workflow_status: str  # Current workflow status
    agent_statuses: dict  # Track individual agent statuses
    processing_start_time: float  # Timestamp when processing started
    processing_end_time: float  # Timestamp when processing completed
    total_processing_time: float  # Total time taken
    retry_count: int  # Number of retries attempted
    max_retries: int  # Maximum retries allowed
    workflow_log: list  # Detailed log of workflow steps
    inter_agent_communication: list  # Log of agent communications
    current_agent: str  # Currently processing agent
    next_agent: str  # Next agent in the pipeline


# -------------------------------
# Enhanced Orchestrator Class
# -------------------------------

class OrchestratorAgent:
    """
    Enhanced Orchestrator Agent that coordinates the flow between agents,
    handles inter-agent communication, manages parallel vs sequential execution,
    implements error handling and retry logic, and logs workflow progress.
    """
    
    def __init__(self, max_retries: int = 3):
        self.intake_agent = IntakeAgent()
        self.risk_agent = RiskAssessmentAgent()
        self.routing_agent = RoutingAgent()
        self.max_retries = max_retries
        self.workflow_metrics = {
            "total_claims_processed": 0,
            "successful_claims": 0,
            "failed_claims": 0,
            "average_processing_time": 0.0,
            "retry_statistics": {}
        }
    
    def initialize_workflow_state(self, claim_data: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize workflow state with tracking fields"""
        current_time = time.time()
        
        # Initialize with claim data and add tracking fields
        state = {**claim_data}
        state.update({
            "workflow_status": WorkflowStatus.INITIATED.value,
            "agent_statuses": {
                "intake": AgentStatus.PENDING.value,
                "risk_assessment": AgentStatus.PENDING.value,
                "routing": AgentStatus.PENDING.value
            },
            "processing_start_time": current_time,
            "processing_end_time": 0.0,
            "total_processing_time": 0.0,
            "retry_count": 0,
            "max_retries": self.max_retries,
            "workflow_log": [
                {
                    "timestamp": current_time,
                    "event": "workflow_initiated",
                    "claim_id": claim_data.get("claim_id"),
                    "details": "Workflow started for claim processing"
                }
            ],
            "inter_agent_communication": [],
            "current_agent": "orchestrator",
            "next_agent": "intake",
            "validation_errors": [],
            "parallel_results": {}
        })
        
        logger.info(f"Workflow initiated for claim {claim_data.get('claim_id')}")
        return state
    
    def log_workflow_event(self, state: Dict[str, Any], event: str, agent: str, details: str):
        """Log workflow events for tracking and debugging"""
        log_entry = {
            "timestamp": time.time(),
            "event": event,
            "agent": agent,
            "claim_id": state.get("claim_id"),
            "details": details
        }
        
        if "workflow_log" not in state:
            state["workflow_log"] = []
        
        state["workflow_log"].append(log_entry)
        logger.info(f"[{state.get('claim_id')}] {agent}: {event} - {details}")
    
    def log_inter_agent_communication(self, state: Dict[str, Any], from_agent: str, to_agent: str, message: str, data: Dict[str, Any] = None):
        """Log communication between agents"""
        comm_entry = {
            "timestamp": time.time(),
            "from_agent": from_agent,
            "to_agent": to_agent,
            "message": message,
            "data": data or {},
            "claim_id": state.get("claim_id")
        }
        
        if "inter_agent_communication" not in state:
            state["inter_agent_communication"] = []
        
        state["inter_agent_communication"].append(comm_entry)
        logger.info(f"[{state.get('claim_id')}] Communication: {from_agent} -> {to_agent}: {message}")
    
    def handle_agent_error(self, state: Dict[str, Any], agent_name: str, error: Exception) -> Dict[str, Any]:
        """Enhanced error handling with retry logic"""
        retry_count = state.get("retry_count", 0)
        max_retries = state.get("max_retries", self.max_retries)
        
        error_msg = f"Agent {agent_name} failed: {str(error)}"
        
        # Log the error
        self.log_workflow_event(state, "agent_error", agent_name, error_msg)
        
        # Update agent status
        if "agent_statuses" not in state:
            state["agent_statuses"] = {}
        state["agent_statuses"][agent_name] = AgentStatus.FAILED.value
        
        # Implement retry logic
        if retry_count < max_retries:
            state["retry_count"] = retry_count + 1
            state["agent_statuses"][agent_name] = AgentStatus.RETRYING.value
            state["workflow_status"] = WorkflowStatus.RETRY_PENDING.value
            
            self.log_workflow_event(
                state, 
                "retry_initiated", 
                "orchestrator", 
                f"Retry {retry_count + 1}/{max_retries} for agent {agent_name}"
            )
            
            logger.warning(f"Retrying agent {agent_name} (attempt {retry_count + 1}/{max_retries})")
            return state
        else:
            # Max retries exceeded
            state["workflow_status"] = WorkflowStatus.FAILED.value
            state["error"] = f"Max retries exceeded for agent {agent_name}: {error_msg}"
            
            self.log_workflow_event(
                state, 
                "workflow_failed", 
                "orchestrator", 
                f"Max retries exceeded for agent {agent_name}"
            )
            
            logger.error(f"Workflow failed for claim {state.get('claim_id')}: {error_msg}")
            return state
    
    def update_workflow_metrics(self, state: Dict[str, Any]):
        """Update orchestrator metrics"""
        self.workflow_metrics["total_claims_processed"] += 1
        
        if state.get("workflow_status") == WorkflowStatus.COMPLETED.value:
            self.workflow_metrics["successful_claims"] += 1
        else:
            self.workflow_metrics["failed_claims"] += 1
        
        # Update average processing time
        processing_time = state.get("total_processing_time", 0.0)
        if processing_time > 0:
            total_time = (self.workflow_metrics["average_processing_time"] * 
                         (self.workflow_metrics["total_claims_processed"] - 1) + processing_time)
            self.workflow_metrics["average_processing_time"] = total_time / self.workflow_metrics["total_claims_processed"]
        
        # Update retry statistics
        retry_count = state.get("retry_count", 0)
        if retry_count > 0:
            if retry_count not in self.workflow_metrics["retry_statistics"]:
                self.workflow_metrics["retry_statistics"][retry_count] = 0
            self.workflow_metrics["retry_statistics"][retry_count] += 1
    
    def get_workflow_metrics(self) -> Dict[str, Any]:
        """Get current workflow metrics"""
        return self.workflow_metrics.copy()


# Initialize orchestrator instance
orchestrator = OrchestratorAgent()


# -------------------------------
# Enhanced LangGraph Node Functions
# -------------------------------

def intake_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Enhanced intake node with comprehensive tracking and error handling"""
    try:
        # Update current agent and status
        state["current_agent"] = "intake"
        state["agent_statuses"]["intake"] = AgentStatus.PROCESSING.value
        state["workflow_status"] = WorkflowStatus.IN_PROGRESS.value
        
        # Log agent start
        orchestrator.log_workflow_event(state, "agent_started", "intake", "Starting intake processing")
        
        # Process with intake agent - pass only claim data
        claim_data = {k: v for k, v in state.items() if k not in [
            "workflow_status", "agent_statuses", "processing_start_time", 
            "processing_end_time", "total_processing_time", "retry_count", 
            "max_retries", "workflow_log", "inter_agent_communication", 
            "current_agent", "next_agent", "validation_errors", "parallel_results"
        ]}
        result = orchestrator.intake_agent.process(claim_data)
        
        # Determine processing mode based on claim characteristics
        processing_mode = determine_processing_mode(state)
        
        # Log inter-agent communication
        orchestrator.log_inter_agent_communication(
            state, 
            "intake", 
            "orchestrator", 
            f"Intake completed, processing mode: {processing_mode}",
            {"validation_errors": result.get("validation_errors", [])}
        )
        
        # Merge results and update state
        enhanced_result = {**state}
        enhanced_result.update(result)
        enhanced_result["processing_mode"] = processing_mode
        enhanced_result["parallel_results"] = {}
        enhanced_result["agent_statuses"]["intake"] = AgentStatus.COMPLETED.value
        
        # Determine next agent
        if processing_mode == "fast_track":
            enhanced_result["next_agent"] = "fast_track"
        elif processing_mode == "standard":
            enhanced_result["next_agent"] = "parallel_processing"
        else:
            enhanced_result["next_agent"] = "risk_assessment"
        
        orchestrator.log_workflow_event(state, "agent_completed", "intake", f"Intake processing completed, next: {enhanced_result['next_agent']}")
        
        return enhanced_result
        
    except Exception as e:
        return orchestrator.handle_agent_error(state, "intake", e)


def risk_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Enhanced risk assessment node with tracking"""
    try:
        # Update current agent and status
        state["current_agent"] = "risk_assessment"
        state["agent_statuses"]["risk_assessment"] = AgentStatus.PROCESSING.value
        
        orchestrator.log_workflow_event(state, "agent_started", "risk_assessment", "Starting risk assessment")
        
        # Create input for risk agent
        risk_input = {
            "claim": state,
            "validation_errors": state.get("validation_errors", [])
        }
        
        # Process with risk agent
        result = orchestrator.risk_agent.process(risk_input)
        
        # Log communication
        orchestrator.log_inter_agent_communication(
            state,
            "risk_assessment",
            "orchestrator", 
            f"Risk assessment completed: {result.get('risk_level')} risk",
            {"risk_score": result.get("risk_score"), "risk_reasons": result.get("risk_reasons", [])}
        )
        
        # Merge results
        enhanced_state = {**state}
        enhanced_state.update(result)
        enhanced_state["agent_statuses"]["risk_assessment"] = AgentStatus.COMPLETED.value
        enhanced_state["next_agent"] = "routing"
        
        orchestrator.log_workflow_event(state, "agent_completed", "risk_assessment", f"Risk level: {result.get('risk_level')}")
        
        return enhanced_state
        
    except Exception as e:
        return orchestrator.handle_agent_error(state, "risk_assessment", e)


def routing_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Enhanced routing node with tracking"""
    try:
        # Update current agent and status
        state["current_agent"] = "routing"
        state["agent_statuses"]["routing"] = AgentStatus.PROCESSING.value
        
        orchestrator.log_workflow_event(state, "agent_started", "routing", "Starting routing decision")
        
        # Create input for routing agent
        routing_input = {
            "claim": state,
            "risk_score": state.get("risk_score"),
            "risk_level": state.get("risk_level"),
            "risk_reasons": state.get("risk_reasons", []),
            "validation_errors": state.get("validation_errors", [])
        }
        
        # Process with routing agent
        result = orchestrator.routing_agent.process(routing_input)
        
        # Log communication
        orchestrator.log_inter_agent_communication(
            state,
            "routing",
            "orchestrator",
            f"Routing completed: {result.get('priority')} priority, {result.get('adjuster_tier')} tier",
            {"priority": result.get("priority"), "adjuster_tier": result.get("adjuster_tier")}
        )
        
        # Merge results and finalize workflow
        enhanced_state = {**state}
        enhanced_state.update(result)
        enhanced_state["agent_statuses"]["routing"] = AgentStatus.COMPLETED.value
        enhanced_state["workflow_status"] = WorkflowStatus.COMPLETED.value
        enhanced_state["processing_end_time"] = time.time()
        enhanced_state["total_processing_time"] = enhanced_state["processing_end_time"] - enhanced_state.get("processing_start_time", 0)
        enhanced_state["current_agent"] = "completed"
        enhanced_state["next_agent"] = "none"
        
        orchestrator.log_workflow_event(
            state, 
            "workflow_completed", 
            "orchestrator", 
            f"Workflow completed in {enhanced_state['total_processing_time']:.2f}s"
        )
        
        # Update metrics
        orchestrator.update_workflow_metrics(enhanced_state)
        
        return enhanced_state
        
    except Exception as e:
        return orchestrator.handle_agent_error(state, "routing", e)


def determine_processing_mode(claim: Dict[str, Any]) -> str:
    """Determine if claim should use fast-track, standard, or complex processing"""
    # Fast-track criteria: simple claims, low amounts, no injuries
    if (claim.get("type") in ["auto_glass", "windshield"] and 
        claim.get("amount", 0) < 1000 and 
        not claim.get("injuries_reported", False)):
        return "fast_track"
    
    # Complex criteria: high amounts, injuries, or multiple parties
    if (claim.get("amount", 0) > 25000 or 
        claim.get("injuries_reported", False) or 
        claim.get("other_party_involved", False) or
        claim.get("type") in ["liability", "medical_payment"]):
        return "complex"
    
    return "standard"


def parallel_processing_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Enhanced parallel processing with comprehensive tracking"""
    try:
        state["current_agent"] = "parallel_processing"
        orchestrator.log_workflow_event(state, "parallel_processing_started", "orchestrator", "Starting parallel processing")
        
        # First run risk assessment - pass only claim data
        claim_data = {k: v for k, v in state.items() if k not in [
            "workflow_status", "agent_statuses", "processing_start_time", 
            "processing_end_time", "total_processing_time", "retry_count", 
            "max_retries", "workflow_log", "inter_agent_communication", 
            "current_agent", "next_agent", "parallel_results"
        ]}
        
        state["agent_statuses"]["risk_assessment"] = AgentStatus.PROCESSING.value
        
        risk_input = {
            "claim": claim_data,
            "validation_errors": state.get("validation_errors", [])
        }
        risk_result = orchestrator.risk_agent.process(risk_input)
        
        # Then run routing with risk assessment results
        routing_result = orchestrator.routing_agent.process(risk_result)
        
        # Log parallel completion
        orchestrator.log_inter_agent_communication(
            state,
            "parallel_processing",
            "orchestrator",
            "Parallel processing completed",
            {"risk_result": risk_result, "preliminary_routing": routing_result}
        )
        
        # Merge results
        merged_state = {**state}
        merged_state.update(risk_result)
        merged_state.update(routing_result)
        
        # Preserve validation errors from intake
        if "validation_errors" in state and state["validation_errors"]:
            merged_state["validation_errors"] = state["validation_errors"]
        
        merged_state["agent_statuses"]["risk_assessment"] = AgentStatus.COMPLETED.value
        merged_state["parallel_results"] = {
            "risk": risk_result,
            "preliminary_routing": routing_result
        }
        merged_state["next_agent"] = "final_routing"
        
        orchestrator.log_workflow_event(state, "parallel_processing_completed", "orchestrator", "Parallel processing completed successfully")
        
        return merged_state
        
    except Exception as e:
        return orchestrator.handle_agent_error(state, "parallel_processing", e)


def final_routing_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Enhanced final routing with optimization tracking"""
    try:
        state["current_agent"] = "final_routing"
        state["agent_statuses"]["routing"] = AgentStatus.PROCESSING.value
        
        orchestrator.log_workflow_event(state, "agent_started", "final_routing", "Starting final routing with parallel optimization")
        
        # Create routing input
        routing_input = {
            "claim": state,
            "risk_score": state.get("risk_score"),
            "risk_level": state.get("risk_level"),
            "risk_reasons": state.get("risk_reasons", []),
            "validation_errors": state.get("validation_errors", [])
        }
        
        final_result = orchestrator.routing_agent.process(routing_input)
        
        # Merge results and finalize
        enhanced_state = {**state}
        enhanced_state.update(final_result)
        enhanced_state["agent_statuses"]["routing"] = AgentStatus.COMPLETED.value
        enhanced_state["workflow_status"] = WorkflowStatus.COMPLETED.value  # Explicitly set to completed
        enhanced_state["processing_end_time"] = time.time()
        enhanced_state["total_processing_time"] = enhanced_state["processing_end_time"] - enhanced_state.get("processing_start_time", 0)
        enhanced_state["current_agent"] = "completed"
        enhanced_state["next_agent"] = "none"
        
        # Add optimization tracking
        if "parallel_results" in state and "preliminary_routing" in state["parallel_results"]:
            prelim = state["parallel_results"]["preliminary_routing"]
            enhanced_state["processing_optimization"] = {
                "parallel_processing_used": True,
                "preliminary_routing": prelim,
                "final_routing_adjustment": "optimized_based_on_risk",
                "efficiency_gain": "parallel_execution"
            }
        
        orchestrator.log_workflow_event(
            state,
            "workflow_completed",
            "orchestrator", 
            f"Optimized workflow completed in {enhanced_state['total_processing_time']:.2f}s with status: {enhanced_state['workflow_status']}"
        )
        
        # Update metrics
        orchestrator.update_workflow_metrics(enhanced_state)
        
        return enhanced_state
        
    except Exception as e:
        return orchestrator.handle_agent_error(state, "final_routing", e)


def fast_track_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Enhanced fast-track processing with tracking"""
    try:
        state["current_agent"] = "fast_track"
        orchestrator.log_workflow_event(state, "fast_track_started", "orchestrator", "Starting fast-track processing")
        
        # Simplified processing for low-risk claims
        fast_result = {
            **state,
            "risk_score": 2,
            "risk_level": "LOW",
            "risk_reasons": ["Fast-track processing - low complexity"],
            "priority": "low",
            "adjuster_tier": "standard",
            "processing_path": "fast_track",
            "workflow_status": WorkflowStatus.COMPLETED.value,
            "processing_end_time": time.time(),
            "current_agent": "completed",
            "next_agent": "none"
        }
        
        fast_result["total_processing_time"] = fast_result["processing_end_time"] - fast_result.get("processing_start_time", 0)
        
        orchestrator.log_workflow_event(
            state,
            "workflow_completed",
            "orchestrator",
            f"Fast-track completed in {fast_result['total_processing_time']:.2f}s"
        )
        
        # Update metrics
        orchestrator.update_workflow_metrics(fast_result)
        
        return fast_result
        
    except Exception as e:
        return orchestrator.handle_agent_error(state, "fast_track", e)


def error_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Enhanced error handling node with comprehensive logging"""
    error_msg = state.get("error", "Unknown error occurred")
    
    orchestrator.log_workflow_event(
        state,
        "error_handling",
        "orchestrator",
        f"Error node activated: {error_msg}"
    )
    
    enhanced_error_state = {
        **state,
        "error": error_msg,
        "processing_status": "failed",
        "retry_recommended": state.get("retry_count", 0) < state.get("max_retries", 3),
        "fallback_processing": "manual_review",
        "workflow_status": WorkflowStatus.FAILED.value,
        "processing_end_time": time.time(),
        "current_agent": "error_handler",
        "next_agent": "none"
    }
    
    enhanced_error_state["total_processing_time"] = enhanced_error_state["processing_end_time"] - enhanced_error_state.get("processing_start_time", 0)
    
    # Update metrics for failed workflow
    orchestrator.update_workflow_metrics(enhanced_error_state)
    
    return enhanced_error_state


def final_routing_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Final routing that considers both risk assessment and preliminary routing"""
    orchestrator = OrchestratorAgent()
    
    # Create the expected input format for the routing agent
    routing_input = {
        "claim": state.get("claim", state),  # Use state["claim"] if available, otherwise fallback to state
        "risk_score": state.get("risk_score"),
        "risk_level": state.get("risk_level"),
        "risk_reasons": state.get("risk_reasons", []),
        "validation_errors": state.get("validation_errors", [])
    }
    final_result = orchestrator.routing_agent.process(routing_input)
    
    # Merge routing results back into state
    enhanced_state = {**state}
    enhanced_state.update(final_result)
    
    # Preserve validation errors from intake
    if "validation_errors" in state and state["validation_errors"]:
        enhanced_state["validation_errors"] = state["validation_errors"]
    
    # If we have preliminary routing, we can compare and optimize
    if "parallel_results" in state and "preliminary_routing" in state["parallel_results"]:
        prelim = state["parallel_results"]["preliminary_routing"]
        
        # Log the efficiency gain from parallel processing
        enhanced_state["processing_optimization"] = {
            "parallel_processing_used": True,
            "preliminary_routing": prelim,
            "final_routing_adjustment": "optimized_based_on_risk"
        }
    
    return enhanced_state


def fast_track_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Fast-track processing for simple claims - minimal risk assessment"""
    # Simplified processing for low-risk claims
    fast_result = {
        **state,
        "risk_score": 2,  # Default low risk
        "risk_level": "LOW",
        "risk_reasons": ["Fast-track processing - low complexity"],
        "priority": "low",
        "adjuster_tier": "standard",
        "processing_path": "fast_track"
    }
    return fast_result


def route_processing_mode(state: Dict[str, Any]) -> Literal["fast_track", "parallel", "sequential"]:
    """Conditional routing based on processing mode"""
    mode = state.get("processing_mode", "standard")
    
    if mode == "fast_track":
        return "fast_track"
    elif mode == "standard":
        return "parallel"  # Use parallel processing for standard claims
    else:  # complex
        return "sequential"  # Use sequential for complex claims that need careful analysis


def error_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Enhanced error handling node"""
    error_msg = state.get("error", "Unknown error occurred")
    
    return {
        **state,
        "error": error_msg,
        "processing_status": "failed",
        "retry_recommended": True,
        "fallback_processing": "manual_review"
    }


# -------------------------------
# Build Enhanced LangGraph workflow
# -------------------------------

graph = StateGraph(WorkflowState)

# Add all nodes
graph.add_node("intake", intake_node)
graph.add_node("risk", risk_node)
graph.add_node("routing", routing_node)
graph.add_node("parallel_processing", parallel_processing_node)
graph.add_node("final_routing", final_routing_node)
graph.add_node("fast_track", fast_track_node)
graph.add_node("error", error_node)

# Entry point
graph.set_entry_point("intake")

# Conditional routing from intake
graph.add_conditional_edges(
    "intake",
    route_processing_mode,
    {
        "fast_track": "fast_track",
        "parallel": "parallel_processing", 
        "sequential": "risk"
    }
)

# Fast-track goes directly to end
graph.add_edge("fast_track", END)

# Parallel processing goes to final routing
graph.add_edge("parallel_processing", "final_routing")
graph.add_edge("final_routing", END)

# Sequential processing (for complex claims)
graph.add_edge("risk", "routing")
graph.add_edge("routing", END)

# Compile workflow
app = graph.compile()

# Export workflow for use in routes
workflow = app


# -------------------------------
# Process Claim Function
# -------------------------------

def process_claim(claim_data: Dict[str, Any]) -> Dict[str, Any]:
    """Main entry point for processing claims through the orchestrator"""
    try:
        # Initialize workflow state
        initial_state = orchestrator.initialize_workflow_state(claim_data)
        
        # Process through the workflow
        result = app.invoke(initial_state)
        
        # Log final workflow metrics
        orchestrator.log_workflow_event(
            result,
            "workflow_completed",
            "orchestrator",
            f"Final status: {result.get('workflow_status', 'completed')}"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Workflow execution failed: {str(e)}")
        return {
            "error": str(e),
            "processing_status": "failed",
            "workflow_status": WorkflowStatus.FAILED.value
        }


# -------------------------------
# Example Run
# -------------------------------

if __name__ == "__main__":
    # Example claim
    sample_claim = {
        "claim_id": "CLM-2024-003",
        "type": "auto_theft",
        "date": "2024-01-14",
        "amount": 35000,
        "description": "Vehicle stolen from driveway overnight",
        "customer_id": "CUST-789",
        "policy_number": "POL-567-NEW",
        "incident_location": "789 Elm St, Downtown",
        "police_report": "RPT-2024-234",
        "injuries_reported": False,
        "other_party_involved": False,
        "timestamp_submitted": "2024-01-14T07:45:00Z",
        "customer_tenure_days": 25,
        "previous_claims_count": 0,
    }

    result = process_claim(sample_claim)
    print("\n=== Final Workflow Result ===")
    print(result)
    
    # Print workflow metrics
    print("\n=== Workflow Metrics ===")
    metrics = orchestrator.get_workflow_metrics()
    print(metrics)
