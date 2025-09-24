from datetime import datetime
from typing import Dict, Any, List


# -------------------------------
# Intake Agent
# -------------------------------
class IntakeAgent:
    """
    Responsible for parsing incoming claim data,
    validating required fields, and returning a structured claim object.
    """

    REQUIRED_FIELDS = [
        "claim_id",
        "type",
        "date",
        "amount",
        "description",
        "customer_id",
        "policy_number",
        "incident_location",
        "timestamp_submitted",
    ]

    def process(self, claim: Dict[str, Any]) -> Dict[str, Any]:
        errors: List[str] = []

        # Validate required fields
        for field in self.REQUIRED_FIELDS:
            if not claim.get(field):
                errors.append(f"missing_{field}")

        # Normalize date if present
        if claim.get("date"):
            try:
                claim["date"] = str(datetime.fromisoformat(claim["date"]))
            except Exception:
                errors.append("invalid_date_format")

        structured_claim = {
            "claim": claim,
            "validation_errors": errors,
            "is_valid": len(errors) == 0,
        }

        return structured_claim
