from datetime import datetime
from typing import Dict, Any, List


class RoutingAgent:
    """
    Responsible for deciding claim processing path:
    - Priority level
    - Adjuster tier
    """

    def process(self, risk_output: Dict[str, Any]) -> Dict[str, Any]:
        claim = risk_output["claim"]
        risk_level = risk_output["risk_level"]
        validation_errors = risk_output["validation_errors"]

        decision = {
            "priority": "normal",
            "adjuster_tier": "standard",
        }

        # Urgent if injuries are reported or liability/medical
        if claim.get("injuries_reported") or claim.get("type") in [
            "liability",
            "medical_payment",
        ]:
            decision["priority"] = "urgent"
            decision["adjuster_tier"] = "senior"

        # High risk → urgent, fraud specialist
        elif risk_level == "HIGH":
            decision["priority"] = "urgent"
            decision["adjuster_tier"] = "fraud_specialist"

        # Medium risk with incomplete data → standard but normal
        elif risk_level == "MEDIUM":
            decision["priority"] = "normal"
            decision["adjuster_tier"] = "standard"

        # Low risk, simple claim types (auto_glass) → low priority
        if claim.get("type") == "auto_glass" and risk_level == "LOW":
            decision["priority"] = "low"
            decision["adjuster_tier"] = "standard"

        routing_decision = {
            "claim_id": claim["claim_id"],
            "risk_level": risk_level,
            "priority": decision["priority"],
            "adjuster_tier": decision["adjuster_tier"],
            "validation_errors": validation_errors,
            "risk_reasons": risk_output["risk_reasons"],
        }

        return routing_decision
