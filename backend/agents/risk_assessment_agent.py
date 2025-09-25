from datetime import datetime, timedelta
from typing import Dict, Any, List


class RiskAssessmentAgent:
    """
    Responsible for detecting potential fraud indicators
    and assigning a risk score (1–10) and level.
    Implements comprehensive fraud detection rules based on PRD requirements.
    """

    def process(self, intake_output: Dict[str, Any]) -> Dict[str, Any]:
        claim = intake_output["claim"]
        errors = intake_output["validation_errors"]

        risk_score = 2  # base score (lowered to allow for better distribution)
        risk_reasons = []

        # Get claim details for context-aware scoring
        claim_type = claim.get("type", "")
        tenure_days = claim.get("customer_tenure_days", 0)
        police_report = claim.get("police_report")
        previous_claims = claim.get("previous_claims_count", 0)

        # Rule 1: High claim amount thresholds (with context adjustments)
        amount = claim.get("amount", 0)
        if amount > 50000:
            # Reduce risk for liability claims with proper documentation and long-term customers
            if (claim_type == "liability" and police_report and tenure_days > 1000 and previous_claims == 0):
                risk_score += 1  # Minimal increase for legitimate liability claims
                risk_reasons.append("High-value liability claim (well-documented)")
            else:
                risk_score += 4
                risk_reasons.append("Very high claim amount (>$50k)")
        elif amount > 20000:
            # Similar adjustment for medium-high amounts
            if (claim_type == "liability" and police_report and tenure_days > 365):
                risk_score += 1
                risk_reasons.append("Medium-high liability claim (documented)")
            else:
                risk_score += 3
                risk_reasons.append("High claim amount (>$20k)")

        # Rule 2: New customer with significant claim
        if tenure_days < 30 and amount > 15000:
            # Exception for liability claims with police reports
            if not (claim_type == "liability" and police_report):
                risk_score += 4
                risk_reasons.append("New customer (<30 days) with high claim")
        elif tenure_days < 90 and amount > 10000:
            # Exception for liability claims with police reports
            if not (claim_type == "liability" and police_report):
                risk_score += 2
                risk_reasons.append("Recent customer (<90 days) with significant claim")

        # Rule 3: Multiple previous claims pattern
        if previous_claims > 4:
            risk_score += 3
            risk_reasons.append("Excessive previous claims (>4)")
        elif previous_claims > 2:
            risk_score += 2
            risk_reasons.append("Multiple previous claims")

        # Rule 4: Suspicious test/minimal claims
        if amount <= 1:
            risk_score += 3
            risk_reasons.append("Suspicious minimal amount claim")
        elif amount < 100 and previous_claims > 0:
            risk_score += 2
            risk_reasons.append("Low amount claim with claim history")

        # Rule 5: Missing critical information
        if errors:
            risk_score += 2
            risk_reasons.append("Incomplete or missing critical data")

        # Rule 6: Suspicious location patterns
        location = (claim.get("incident_location") or "").lower()
        if location in ["unknown location", "unknown", ""] or not location.strip():
            risk_score += 2
            risk_reasons.append("Unknown or missing incident location")

        # Rule 7: Missing police report for high-value claims
        if not police_report and amount > 10000:
            # Reduce penalty for liability claims from long-term customers
            if claim_type == "liability" and tenure_days > 1000:
                # Don't penalize - liability claims may not always need police reports
                pass
            else:
                risk_score += 2
                risk_reasons.append("High-value claim without police report")

        # Rule 8: Hit and run claims (higher fraud risk)
        description = (claim.get("description") or "").lower()
        if "hit and run" in description and not police_report:
            risk_score += 3
            risk_reasons.append("Hit and run claim without police report")

        # Rule 9: Theft claims from new customers
        if "theft" in claim_type and tenure_days < 60:
            risk_score += 3
            risk_reasons.append("Theft claim from new customer")

        # Rule 10: Claims just under common thresholds (potential fraud indicator)
        if 9900 <= amount <= 10100:
            risk_score += 2
            risk_reasons.append("Claim amount near $10k threshold")

        # Rule 11: Late reporting for time-sensitive claims
        if self._is_late_reporting(claim):
            risk_score += 1
            risk_reasons.append("Late claim reporting")

        # Rule 12: Weekend/holiday submissions (statistical fraud indicator)
        if self._is_suspicious_timing(claim):
            risk_score += 1
            risk_reasons.append("Suspicious submission timing")

        # Clamp score between 1–10
        risk_score = min(10, max(1, risk_score))

        # Enhanced risk level mapping with better distribution
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
            "fraud_indicators": len(risk_reasons),
            "assessment_timestamp": datetime.now().isoformat()
        }

    def _is_late_reporting(self, claim: Dict[str, Any]) -> bool:
        """Check if claim was reported unusually late after incident"""
        try:
            incident_date = claim.get("date")
            submitted_timestamp = claim.get("timestamp_submitted")
            
            if not incident_date or not submitted_timestamp:
                return False
                
            # Parse dates
            if isinstance(incident_date, str):
                incident_dt = datetime.fromisoformat(incident_date.replace('Z', '+00:00'))
            else:
                return False
                
            if isinstance(submitted_timestamp, str):
                submitted_dt = datetime.fromisoformat(submitted_timestamp.replace('Z', '+00:00'))
            else:
                return False
            
            # Check if reported more than 7 days after incident
            return (submitted_dt - incident_dt).days > 7
            
        except (ValueError, TypeError):
            return False

    def _is_suspicious_timing(self, claim: Dict[str, Any]) -> bool:
        """Check for suspicious submission timing patterns"""
        try:
            submitted_timestamp = claim.get("timestamp_submitted")
            if not submitted_timestamp:
                return False
                
            submitted_dt = datetime.fromisoformat(submitted_timestamp.replace('Z', '+00:00'))
            
            # Check for very late night submissions (potential fraud indicator)
            hour = submitted_dt.hour
            return hour >= 22 or hour <= 5  # 10 PM to 5 AM
            
        except (ValueError, TypeError):
            return False
