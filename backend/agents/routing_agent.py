from datetime import datetime
from typing import Dict, Any, List


class RoutingAgent:
    """
    Routing Agent - Determines claim processing path based on type and risk
    
    Responsibilities:
    - Determine claim processing path based on type and risk
    - Assign priority level (urgent/normal/low)
    - Select appropriate adjuster tier (fraud_specialist/senior/standard)
    - Output: Comprehensive routing decision
    
    Priority Levels:
    - urgent: Injuries, liability, medical, high-risk fraud, high-value claims
    - normal: Standard claims with medium risk
    - low: Simple claims with low risk (e.g., auto glass)
    
    Adjuster Tiers:
    - fraud_specialist: High-risk fraud cases
    - senior: High-value claims, liability with injuries, urgent medical
    - standard: Regular claims
    """

    # Configuration thresholds
    HIGH_VALUE_THRESHOLD = 50000  # Claims above this amount require senior adjuster
    MEDIUM_VALUE_THRESHOLD = 10000  # Claims above this get elevated priority

    def process(self, risk_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process risk assessment output and determine routing decision
        
        Args:
            risk_output: Output from RiskAssessmentAgent containing claim, risk_level, etc.
            
        Returns:
            Dict containing routing decision with priority, adjuster_tier, and reasoning
        """
        claim = risk_output["claim"]
        risk_level = risk_output["risk_level"]
        validation_errors = risk_output.get("validation_errors", [])
        
        # Initialize default routing decision
        decision = {
            "priority": "normal",
            "adjuster_tier": "standard",
        }
        
        routing_reasons = []
        
        # Get claim amount for value-based routing
        claim_amount = claim.get("amount", 0)
        
        # Priority 1: Urgent cases - Injuries and liability
        if claim.get("injuries_reported") or claim.get("type") in ["liability", "medical_payment"]:
            decision["priority"] = "urgent"
            decision["adjuster_tier"] = "senior"
            routing_reasons.append("Urgent: Injuries reported or liability/medical claim type")
        
        # Priority 2: High-risk fraud cases
        elif risk_level == "HIGH":
            decision["priority"] = "urgent"
            decision["adjuster_tier"] = "fraud_specialist"
            routing_reasons.append("Urgent: High fraud risk detected")
        
        # Priority 3: High-value claims (regardless of risk)
        elif claim_amount >= self.HIGH_VALUE_THRESHOLD:
            decision["priority"] = "urgent"
            decision["adjuster_tier"] = "senior"
            routing_reasons.append(f"Urgent: High-value claim (${claim_amount:,} >= ${self.HIGH_VALUE_THRESHOLD:,})")
        
        # Priority 4: Medium-value claims with medium/high risk
        elif claim_amount >= self.MEDIUM_VALUE_THRESHOLD and risk_level in ["MEDIUM", "HIGH"]:
            decision["priority"] = "normal"
            decision["adjuster_tier"] = "senior"
            routing_reasons.append(f"Elevated: Medium-value claim (${claim_amount:,}) with {risk_level} risk")
        
        # Priority 5: Medium risk cases
        elif risk_level == "MEDIUM":
            decision["priority"] = "normal"
            decision["adjuster_tier"] = "standard"
            routing_reasons.append("Standard: Medium risk level")
        
        # Priority 6: Low-priority simple claims
        elif claim.get("type") == "auto_glass" and risk_level == "LOW":
            decision["priority"] = "low"
            decision["adjuster_tier"] = "standard"
            routing_reasons.append("Low priority: Simple auto glass claim with low risk")
        
        # Default case
        else:
            routing_reasons.append(f"Standard routing: {risk_level} risk, ${claim_amount:,} claim")
        
        # Special handling for claims with validation errors
        if validation_errors:
            if decision["priority"] == "low":
                decision["priority"] = "normal"
            routing_reasons.append(f"Priority elevated due to validation errors: {', '.join(validation_errors)}")
        
        # Handle specific claim types that need special attention
        special_types = {
            "auto_theft": "Theft claims require careful verification",
            "flood": "Natural disaster claims need specialized handling",
            "fire": "Fire claims require detailed investigation"
        }
        
        claim_type = claim.get("type", "")
        if claim_type in special_types:
            if decision["adjuster_tier"] == "standard" and claim_amount >= self.MEDIUM_VALUE_THRESHOLD:
                decision["adjuster_tier"] = "senior"
            routing_reasons.append(special_types[claim_type])
        
        # Construct comprehensive routing decision
        routing_decision = {
            "claim_id": claim.get("claim_id", "unknown"),
            "risk_level": risk_level,
            "priority": decision["priority"],
            "adjuster_tier": decision["adjuster_tier"],
            "validation_errors": validation_errors,  # Keep original validation errors
            "risk_reasons": risk_output.get("risk_reasons", []),
            "routing_reasons": routing_reasons,
            "claim_amount": claim_amount,
            "processing_path": self._determine_processing_path(decision, claim_type, claim_amount),
            "estimated_processing_time": self._estimate_processing_time(decision, validation_errors),
            "timestamp": datetime.now().isoformat()
        }

        return routing_decision
    
    def _determine_processing_path(self, decision: Dict[str, str], claim_type: str, amount: float) -> str:
        """Determine the specific processing path for the claim"""
        if decision["priority"] == "urgent":
            if decision["adjuster_tier"] == "fraud_specialist":
                return "fraud_investigation"
            elif decision["adjuster_tier"] == "senior":
                return "senior_review"
        elif decision["priority"] == "low":
            return "fast_track"
        elif amount >= self.MEDIUM_VALUE_THRESHOLD:
            return "detailed_review"
        else:
            return "standard_processing"
    
    def _estimate_processing_time(self, decision: Dict[str, str], validation_errors: List[str]) -> str:
        """Estimate processing time based on routing decision"""
        base_time = {
            "urgent": "24-48 hours",
            "normal": "3-5 business days",
            "low": "1-2 business days"
        }
        
        estimated = base_time.get(decision["priority"], "3-5 business days")
        
        # Add time for validation issues
        if validation_errors:
            estimated += " (additional time needed for data validation)"
        
        # Add time for fraud investigation
        if decision["adjuster_tier"] == "fraud_specialist":
            estimated = "5-10 business days (fraud investigation)"
            
        return estimated
