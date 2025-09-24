from langgraph.graph import StateGraph
from typing import Dict, Any, TypedDict

# Import the detailed agents we wrote earlier
from agents import IntakeAgent, RiskAssessmentAgent, RoutingAgent


# -------------------------------
# Define State Schema
# -------------------------------

class WorkflowState(TypedDict):
    """State schema for the workflow"""
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
    # Additional fields that get added during processing
    validation_errors: list
    risk_score: int
    risk_level: str
    risk_reasons: list
    priority: str
    adjuster_tier: str
    error: str


# -------------------------------
# Wrap agents for LangGraph nodes
# -------------------------------

intake_agent = IntakeAgent()
risk_agent = RiskAssessmentAgent()
routing_agent = RoutingAgent()


def intake_node(state: Dict[str, Any]) -> Dict[str, Any]:
    return intake_agent.process(state)


def risk_node(state: Dict[str, Any]) -> Dict[str, Any]:
    return risk_agent.process(state)


def routing_node(state: Dict[str, Any]) -> Dict[str, Any]:
    return routing_agent.process(state)


def error_node(err: Exception, state: Dict[str, Any]) -> Dict[str, Any]:
    return {"error": str(err), "failed_claim": state}


# -------------------------------
# Build LangGraph workflow
# -------------------------------

graph = StateGraph(WorkflowState)

# Add nodes (agents)
graph.add_node("intake", intake_node)
graph.add_node("risk", risk_node)
graph.add_node("routing", routing_node)
graph.add_node("error", error_node)

# Define flow (edges)
graph.add_edge("intake", "risk")
graph.add_edge("risk", "routing")

# Entry point
graph.set_entry_point("intake")

# Compile workflow
workflow = graph.compile()


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

    result = workflow.invoke(sample_claim)
    print("\n=== Final Workflow Result ===")
    print(result)
