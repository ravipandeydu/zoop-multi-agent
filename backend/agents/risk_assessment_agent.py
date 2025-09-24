from datetime import datetime
from typing import Dict, Any, List


class RiskAssessmentAgent:
    """
    Responsible for detecting potential fraud indicators
    and assigning a risk score (1–10) and level.
    """

    def process(self, intake_output: Dict[str, Any]) -> Dict[str, Any]:
        claim = intake_output["claim"]
        errors = intake_output["validation_errors"]

        risk_score = 3  # base score
        risk_reasons = []

        # Rule 1: High claim amount
        if claim.get("amount", 0) > 20000:
            risk_score += 3
            risk_reasons.append("High claim amount")

        # Rule 2: New customer with high claim
        if claim.get("customer_tenure_days", 0) < 90 and claim.get("amount", 0) > 10000:
            risk_score += 3
            risk_reasons.append("New customer with high claim")

        # Rule 3: Multiple previous claims
        if claim.get("previous_claims_count", 0) > 2:
            risk_score += 2
            risk_reasons.append("Multiple previous claims")

        # Rule 4: Suspicious low amount test claim
        if claim.get("amount", 0) <= 1:
            risk_score += 2
            risk_reasons.append("Suspicious test claim")

        # Rule 5: Missing critical fields increases risk
        if errors:
            risk_score += 2
            risk_reasons.append("Incomplete data")

        # Clamp score between 1–10
        risk_score = min(10, max(1, risk_score))

        # Risk level mapping
        if risk_score <= 3:
            risk_level = "LOW"
        elif 4 <= risk_score <= 6:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"

        return {
            "claim": claim,
            "validation_errors": errors,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_reasons": risk_reasons,
        }
