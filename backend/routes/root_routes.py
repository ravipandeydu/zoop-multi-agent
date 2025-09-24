from fastapi import APIRouter

router = APIRouter(tags=["root"])


@router.get("/")
async def read_root():
    """Root endpoint that returns system information"""
    return {
        "message": "Multi-Agent FNOL Claim Processing System",
        "description": "Real-time orchestration of intake, risk assessment, and routing agents",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "submit_claim": "POST /api/claims/submit",
            "get_claim_status": "GET /api/claims/{claim_id}/status", 
            "list_claims": "GET /api/claims",
            "system_health": "GET /api/system/health",
            "system_metrics": "GET /api/system/metrics"
        },
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc"
        },
        "agents": {
            "intake": "Validates and extracts claim data",
            "risk_assessment": "Analyzes fraud indicators and calculates risk scores",
            "routing": "Determines processing paths and adjuster assignments",
            "orchestrator": "Coordinates workflow between all agents"
        }
    }