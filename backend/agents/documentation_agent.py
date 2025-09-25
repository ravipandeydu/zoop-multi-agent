from datetime import datetime
from typing import Dict, Any, List, Optional
import json
import logging
import os
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import ChatOpenAI


# -------------------------------
# Documentation Agent
# -------------------------------
class DocumentationAgent:
    """
    Responsible for generating comprehensive documentation and summaries
    for processed claims using LLM capabilities. Creates structured
    documentation including summaries, key points, and detailed reports.
    """

    def __init__(self, model_name: str = "gpt-3.5-turbo", api_key: Optional[str] = None):
        """
        Initialize the Documentation Agent with ChatGPT configuration.
        
        Args:
            model_name: Name of the OpenAI model to use (default: gpt-3.5-turbo)
            api_key: OpenAI API key (if not provided, will use OPENAI_API_KEY env var)
        """
        self.model_name = model_name
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass api_key parameter.")
        
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=0.3,
            api_key=self.api_key,
            max_tokens=2000
        )
        self.logger = logging.getLogger(__name__)
        
        # Initialize prompt templates
        self._setup_prompts()

    def _setup_prompts(self):
        """Setup prompt templates for different documentation tasks."""
        
        # Summary generation prompt
        self.summary_prompt = ChatPromptTemplate.from_template("""
        You are an expert insurance claim documentation specialist. Generate a concise, professional summary of the following claim information.

        Claim Details:
        - Claim ID: {claim_id}
        - Type: {claim_type}
        - Amount: ${amount}
        - Date: {date}
        - Description: {description}
        - Location: {location}
        - Customer ID: {customer_id}
        - Policy Number: {policy_number}

        Processing Results:
        - Risk Score: {risk_score}/10
        - Risk Level: {risk_level}
        - Priority: {priority}
        - Adjuster Tier: {adjuster_tier}
        - Processing Path: {processing_path}

        Generate a professional 2-3 sentence summary that captures the essential information and processing outcome.
        """)

        # Key points extraction prompt
        self.key_points_prompt = ChatPromptTemplate.from_template("""
        You are an expert insurance claim analyst. Extract and organize the key points from the following claim information.

        Claim Details:
        - Claim ID: {claim_id}
        - Type: {claim_type}
        - Amount: ${amount}
        - Date: {date}
        - Description: {description}
        - Location: {location}
        - Injuries Reported: {injuries_reported}
        - Police Report: {police_report}
        - Other Party Involved: {other_party_involved}

        Risk Assessment:
        - Risk Score: {risk_score}/10
        - Risk Level: {risk_level}
        - Fraud Indicators: {fraud_indicators}

        Routing Decision:
        - Priority: {priority}
        - Adjuster Tier: {adjuster_tier}
        - Processing Path: {processing_path}

        Extract and return a JSON object with the following structure:
        {{
            "claim_overview": "Brief overview of the claim",
            "key_facts": ["fact1", "fact2", "fact3"],
            "risk_factors": ["factor1", "factor2"],
            "processing_notes": ["note1", "note2"],
            "next_steps": ["step1", "step2"]
        }}
        """)

        # Detailed documentation prompt
        self.documentation_prompt = ChatPromptTemplate.from_template("""
        You are an expert insurance documentation specialist. Create a comprehensive, professional documentation report for the following claim.

        Claim Information:
        - Claim ID: {claim_id}
        - Type: {claim_type}
        - Amount: ${amount}
        - Date: {date}
        - Description: {description}
        - Location: {location}
        - Customer ID: {customer_id}
        - Policy Number: {policy_number}
        - Submission Time: {timestamp_submitted}

        Additional Details:
        - Injuries Reported: {injuries_reported}
        - Police Report: {police_report}
        - Other Party Involved: {other_party_involved}
        - Customer Tenure: {customer_tenure_days} days
        - Previous Claims: {previous_claims_count}

        Processing Results:
        - Validation Status: {validation_status}
        - Risk Score: {risk_score}/10 ({risk_level})
        - Fraud Indicators: {fraud_indicators}
        - Priority Level: {priority}
        - Assigned Adjuster Tier: {adjuster_tier}
        - Processing Path: {processing_path}

        Create a comprehensive documentation report with the following sections:
        1. CLAIM SUMMARY
        2. INCIDENT DETAILS
        3. RISK ASSESSMENT
        4. PROCESSING DECISION
        5. RECOMMENDATIONS

        Format the response as a professional insurance documentation report.
        """)

    def process(self, claim_data: Dict[str, Any], processing_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive documentation for a processed claim.
        
        Args:
            claim_data: Original claim information
            processing_results: Results from intake, risk assessment, and routing agents
            
        Returns:
            Dictionary containing generated documentation, summary, and key points
        """
        try:
            self.logger.info(f"Starting documentation generation for claim {claim_data.get('claim_id')}")
            
            # Prepare data for LLM prompts
            prompt_data = self._prepare_prompt_data(claim_data, processing_results)
            
            # Generate summary
            summary = self._generate_summary(prompt_data)
            
            # Extract key points
            key_points = self._extract_key_points(prompt_data)
            
            # Generate detailed documentation
            documentation = self._generate_documentation(prompt_data)
            
            result = {
                "agent_type": "documentation",
                "claim_id": claim_data.get("claim_id"),
                "timestamp": datetime.now().isoformat(),
                "summary": summary,
                "key_points": key_points,
                "documentation": documentation,
                "status": "completed",
                "processing_time_ms": None  # Will be set by orchestrator
            }
            
            self.logger.info(f"Documentation generation completed for claim {claim_data.get('claim_id')}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in documentation generation: {str(e)}")
            return {
                "agent_type": "documentation",
                "claim_id": claim_data.get("claim_id"),
                "timestamp": datetime.now().isoformat(),
                "summary": None,
                "key_points": None,
                "documentation": None,
                "status": "failed",
                "error": str(e)
            }

    def _prepare_prompt_data(self, claim_data: Dict[str, Any], processing_results: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare and format data for LLM prompts."""
        
        # Extract processing results
        intake_result = processing_results.get("intake", {})
        risk_result = processing_results.get("risk_assessment", {})
        routing_result = processing_results.get("routing", {})
        
        return {
            # Claim data
            "claim_id": claim_data.get("claim_id", "N/A"),
            "claim_type": claim_data.get("type", "N/A"),
            "amount": claim_data.get("amount", 0),
            "date": claim_data.get("date", "N/A"),
            "description": claim_data.get("description", "N/A"),
            "location": claim_data.get("incident_location", "N/A"),
            "customer_id": claim_data.get("customer_id", "N/A"),
            "policy_number": claim_data.get("policy_number", "N/A"),
            "timestamp_submitted": claim_data.get("timestamp_submitted", "N/A"),
            "injuries_reported": claim_data.get("injuries_reported", "No"),
            "police_report": claim_data.get("police_report", "No"),
            "other_party_involved": claim_data.get("other_party_involved", "No"),
            "customer_tenure_days": claim_data.get("customer_tenure_days", "N/A"),
            "previous_claims_count": claim_data.get("previous_claims_count", 0),
            
            # Processing results
            "validation_status": "Valid" if intake_result.get("is_valid", True) else "Invalid",
            "risk_score": risk_result.get("risk_score", "N/A"),
            "risk_level": risk_result.get("risk_level", "N/A"),
            "fraud_indicators": json.dumps(risk_result.get("fraud_indicators", [])),
            "priority": routing_result.get("priority", "N/A"),
            "adjuster_tier": routing_result.get("adjuster_tier", "N/A"),
            "processing_path": routing_result.get("processing_path", "N/A")
        }

    def _generate_summary(self, prompt_data: Dict[str, Any]) -> str:
        """Generate a concise claim summary using LLM."""
        try:
            chain = self.summary_prompt | self.llm
            response = chain.invoke(prompt_data)
            # Extract content from AIMessage object
            if hasattr(response, 'content'):
                return response.content.strip()
            else:
                return str(response).strip()
        except Exception as e:
            self.logger.error(f"Error generating summary: {str(e)}")
            return f"Summary generation failed for claim {prompt_data.get('claim_id')}"

    def _extract_key_points(self, prompt_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract key points from claim data using LLM."""
        try:
            parser = JsonOutputParser()
            chain = self.key_points_prompt | self.llm | parser
            response = chain.invoke(prompt_data)
            return response
        except Exception as e:
            self.logger.error(f"Error extracting key points: {str(e)}")
            return {
                "claim_overview": f"Key points extraction failed for claim {prompt_data.get('claim_id')}",
                "key_facts": [],
                "risk_factors": [],
                "processing_notes": [],
                "next_steps": []
            }

    def _generate_documentation(self, prompt_data: Dict[str, Any]) -> str:
        """Generate detailed documentation using LLM."""
        try:
            chain = self.documentation_prompt | self.llm
            response = chain.invoke(prompt_data)
            # Extract content from AIMessage object
            if hasattr(response, 'content'):
                return response.content.strip()
            else:
                return str(response).strip()
        except Exception as e:
            self.logger.error(f"Error generating documentation: {str(e)}")
            return f"Documentation generation failed for claim {prompt_data.get('claim_id')}"

    def get_agent_info(self) -> Dict[str, Any]:
        """Return agent information and capabilities."""
        return {
            "agent_type": "documentation",
            "model": self.model_name,
            "capabilities": [
                "claim_summary_generation",
                "key_points_extraction", 
                "detailed_documentation",
                "professional_reporting"
            ],
            "description": "Generates comprehensive documentation and summaries for processed insurance claims using LLM"
        }