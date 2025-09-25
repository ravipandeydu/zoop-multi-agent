from datetime import datetime
from typing import Dict, Any, List, Union
import re
import json


# -------------------------------
# Intake Agent
# -------------------------------
class IntakeAgent:
    """
    Responsible for parsing incoming claim data (JSON/text format),
    extracting key information, validating data completeness,
    and returning a structured claim object.
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

    OPTIONAL_FIELDS = [
        "police_report",
        "injuries_reported",
        "other_party_involved",
        "customer_tenure_days",
        "previous_claims_count",
    ]

    CLAIM_TYPES = [
        "auto_collision", "auto_accident", "auto_theft", "auto_glass", "auto_comprehensive",
        "property_damage", "flood", "liability", "medical", "medical_payment"
    ]

    def process(self, claim_input: Union[Dict[str, Any], str]) -> Dict[str, Any]:
        """
        Process incoming claim data in JSON or text format.
        
        Args:
            claim_input: Either a dictionary (JSON) or string (text description)
            
        Returns:
            Structured claim object with validation results
        """
        errors: List[str] = []
        warnings: List[str] = []
        
        # Parse input based on type
        if isinstance(claim_input, str):
            claim = self._parse_text_claim(claim_input)
            if not claim:
                errors.append("failed_to_parse_text_input")
                claim = {}
        else:
            claim = claim_input.copy()

        # Extract and highlight key information
        key_info = self._extract_key_information(claim)
        
        # Validate required fields
        field_errors = self._validate_required_fields(claim)
        errors.extend(field_errors)
        
        # Validate data types and formats
        validation_errors = self._validate_data_types(claim)
        errors.extend(validation_errors)
        
        # Business rule validation
        business_errors = self._validate_business_rules(claim)
        errors.extend(business_errors)
        
        # Generate suggestions for missing fields
        suggestions = self._generate_suggestions(claim, errors)
        
        # Normalize data
        normalized_claim = self._normalize_claim_data(claim)

        structured_claim = {
            "claim": normalized_claim,
            "key_information": key_info,
            "validation_errors": errors,
            "warnings": warnings,
            "suggestions": suggestions,
            "is_valid": len(errors) == 0,
            "completeness_score": self._calculate_completeness_score(normalized_claim),
        }

        return structured_claim

    def _parse_text_claim(self, text: str) -> Dict[str, Any]:
        """
        Parse unstructured text claim description and extract structured data.
        """
        claim = {}
        
        # Try to extract claim ID
        claim_id_match = re.search(r'claim[_\s]*id[:\s]*([A-Z0-9-]+)', text, re.IGNORECASE)
        if claim_id_match:
            claim["claim_id"] = claim_id_match.group(1)
        
        # Try to extract claim type
        for claim_type in self.CLAIM_TYPES:
            if claim_type.replace("_", " ") in text.lower() or claim_type in text.lower():
                claim["type"] = claim_type
                break
        
        # Try to extract amount
        amount_match = re.search(r'\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', text)
        if amount_match:
            amount_str = amount_match.group(1).replace(",", "")
            try:
                claim["amount"] = float(amount_str)
            except ValueError:
                pass
        
        # Try to extract date
        date_patterns = [
            r'(\d{4}-\d{2}-\d{2})',  # YYYY-MM-DD
            r'(\d{1,2}/\d{1,2}/\d{4})',  # MM/DD/YYYY
            r'(\d{1,2}-\d{1,2}-\d{4})',  # MM-DD-YYYY
        ]
        for pattern in date_patterns:
            date_match = re.search(pattern, text)
            if date_match:
                claim["date"] = date_match.group(1)
                break
        
        # Use the entire text as description if no specific description found
        claim["description"] = text
        
        return claim

    def _extract_key_information(self, claim: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract and highlight key information as specified in PRD.
        """
        return {
            "claim_type": claim.get("type"),
            "incident_date": claim.get("date"),
            "claim_amount": claim.get("amount"),
            "description": claim.get("description"),
            "customer_id": claim.get("customer_id"),
            "policy_number": claim.get("policy_number"),
        }

    def _validate_required_fields(self, claim: Dict[str, Any]) -> List[str]:
        """
        Validate presence of required fields.
        """
        errors = []
        for field in self.REQUIRED_FIELDS:
            value = claim.get(field)
            if value is None or value == "" or value == "null":
                # Use PRD-compliant error naming
                if field == "incident_location":
                    errors.append("missing_location")
                else:
                    errors.append(f"missing_{field}")
        return errors

    def _validate_data_types(self, claim: Dict[str, Any]) -> List[str]:
        """
        Validate data types and formats.
        """
        errors = []
        
        # Validate amount is numeric
        if claim.get("amount") is not None:
            try:
                amount = float(claim["amount"])
                if amount < 0:
                    errors.append("invalid_amount_negative")
            except (ValueError, TypeError):
                errors.append("invalid_amount_format")
        
        # Validate date format
        if claim.get("date"):
            try:
                if claim["date"] != "null":
                    datetime.fromisoformat(str(claim["date"]).replace("/", "-"))
            except (ValueError, TypeError):
                errors.append("invalid_date_format")
        
        # Validate claim type
        if claim.get("type") and claim["type"] not in self.CLAIM_TYPES:
            errors.append("invalid_claim_type")
        
        return errors

    def _validate_business_rules(self, claim: Dict[str, Any]) -> List[str]:
        """
        Apply business rule validation.
        """
        errors = []
        
        # Date shouldn't be in the future
        if claim.get("date"):
            try:
                claim_date = datetime.fromisoformat(str(claim["date"]).replace("/", "-"))
                if claim_date > datetime.now():
                    errors.append("future_date_not_allowed")
            except (ValueError, TypeError):
                pass  # Already caught in data type validation
        
        # Amount should be reasonable (not extremely high or low)
        if claim.get("amount"):
            try:
                amount = float(claim["amount"])
                if amount > 1000000:  # Over $1M
                    errors.append("amount_requires_special_handling")
                elif amount <= 0:
                    errors.append("invalid_amount_zero_or_negative")
            except (ValueError, TypeError):
                pass  # Already caught in data type validation
        
        return errors

    def _generate_suggestions(self, claim: Dict[str, Any], errors: List[str]) -> List[str]:
        """
        Generate helpful suggestions for missing or invalid fields.
        """
        suggestions = []
        
        if "missing_date" in errors:
            suggestions.append("Please provide the incident date in YYYY-MM-DD format")
        
        if "missing_incident_location" in errors:
            suggestions.append("Please specify where the incident occurred")
        
        if "missing_amount" in errors:
            suggestions.append("Please provide the estimated claim amount")
        
        if "invalid_amount_format" in errors:
            suggestions.append("Amount should be a valid number (e.g., 1500.00)")
        
        if "invalid_date_format" in errors:
            suggestions.append("Date should be in YYYY-MM-DD format")
        
        return suggestions

    def _normalize_claim_data(self, claim: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize and clean claim data.
        """
        normalized = claim.copy()
        
        # Normalize date format
        if normalized.get("date") and normalized["date"] != "null":
            try:
                date_obj = datetime.fromisoformat(str(normalized["date"]).replace("/", "-"))
                normalized["date"] = date_obj.isoformat()
            except (ValueError, TypeError):
                pass  # Keep original if can't parse
        
        # Normalize amount to float
        if normalized.get("amount"):
            try:
                normalized["amount"] = float(normalized["amount"])
            except (ValueError, TypeError):
                pass  # Keep original if can't convert
        
        # Ensure boolean fields are properly typed
        for field in ["injuries_reported", "other_party_involved"]:
            if field in normalized and normalized[field] is not None:
                if isinstance(normalized[field], str):
                    normalized[field] = normalized[field].lower() in ["true", "yes", "1"]
        
        return normalized

    def _calculate_completeness_score(self, claim: Dict[str, Any]) -> float:
        """
        Calculate completeness score based on required and optional fields.
        """
        total_fields = len(self.REQUIRED_FIELDS) + len(self.OPTIONAL_FIELDS)
        completed_fields = 0
        
        # Count required fields (weighted more heavily)
        for field in self.REQUIRED_FIELDS:
            if claim.get(field) and claim[field] != "null" and claim[field] != "":
                completed_fields += 2  # Required fields count double
        
        # Count optional fields
        for field in self.OPTIONAL_FIELDS:
            if claim.get(field) and claim[field] != "null" and claim[field] != "":
                completed_fields += 1
        
        # Adjust total to account for weighted required fields
        adjusted_total = len(self.REQUIRED_FIELDS) * 2 + len(self.OPTIONAL_FIELDS)
        
        return min(1.0, completed_fields / adjusted_total)
