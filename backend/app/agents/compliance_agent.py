"""
Compliance Agent - Checks for missing clauses and compliance issues
"""
import logging
from typing import Dict, Any, List
import json

from app.services.ollama_service import ollama_service
from app.models.schemas import Language

logger = logging.getLogger(__name__)


class ComplianceAgent:
    """Agent for checking contract compliance"""
    
    def __init__(self):
        self.openai_service = ollama_service
        self.standard_clauses = self._get_standard_clauses()
    
    async def check_compliance(
        self,
        contract_text: str,
        extracted_data: Dict[str, Any],
        language: Language,
        industry: str = None
    ) -> Dict[str, Any]:
        """
        Check contract compliance with standards
        
        Args:
            contract_text: Full contract text
            extracted_data: Previously extracted data
            language: Contract language
            industry: Industry sector
            
        Returns:
            Compliance check results
        """
        logger.info(f"Checking compliance for contract (industry: {industry})")
        
        lang_instruction = (
            "The contract is in Arabic." if language == Language.ARABIC else "The contract is in English."
        )
        
        industry_clauses = self._get_industry_specific_clauses(industry)
        
        system_prompt = f"""You are a contract compliance specialist.
{lang_instruction}

Check if the contract contains the following standard clauses and evaluate their completeness:

**Essential Clauses:**
{json.dumps(self.standard_clauses, indent=2)}

**Industry-Specific Clauses ({industry or 'General'}):**
{json.dumps(industry_clauses, indent=2)}

For each clause type, determine:
1. **Status:** "present" (clause exists and is complete), "incomplete" (clause exists but lacks detail), or "missing" (clause not found)
2. **Description:** What was found or what is missing
3. **Recommendation:** Suggested action if missing or incomplete

Also provide:
- compliance_score: Overall score from 0-100 based on clause coverage
- critical_missing: List of critical clauses that are missing
- recommendations: High-priority actions to improve compliance

Return analysis in JSON format."""
        
        try:
            context = f"""Contract Text (First 10000 chars):
{contract_text[:10000]}

Contract Type: {extracted_data.get('contract_type', 'Unknown')}
Parties: {', '.join([p.get('name', '') for p in extracted_data.get('parties', [])])}
Value: {extracted_data.get('contract_value', 'Not specified')}

Check the contract for presence and completeness of standard clauses."""
            
            response = await self.openai_service.chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": context}
                ],
                temperature=0.1,
                max_tokens=3000,
                response_format={"type": "json_object"}
            )
            
            analysis = json.loads(response)
            
            # Ensure required structure
            if "compliance_items" not in analysis:
                analysis["compliance_items"] = []
            if "compliance_score" not in analysis:
                analysis["compliance_score"] = self._calculate_compliance_score(
                    analysis.get("compliance_items", [])
                )
            if "critical_missing" not in analysis:
                analysis["critical_missing"] = []
            if "recommendations" not in analysis:
                analysis["recommendations"] = []
            
            logger.info(f"Compliance check complete: Score {analysis['compliance_score']}/100")
            return analysis
            
        except Exception as e:
            logger.error(f"Error in compliance check: {e}", exc_info=True)
            return {
                "compliance_items": [],
                "compliance_score": 0,
                "critical_missing": [],
                "recommendations": [],
                "error": str(e)
            }
    
    def _get_standard_clauses(self) -> List[str]:
        """Get list of standard clauses to check"""
        return [
            "Parties and Definitions",
            "Scope of Work / Services",
            "Payment Terms",
            "Term and Termination",
            "Confidentiality / NDA",
            "Intellectual Property Rights",
            "Warranties and Representations",
            "Limitation of Liability",
            "Indemnification",
            "Force Majeure",
            "Dispute Resolution / Arbitration",
            "Governing Law and Jurisdiction",
            "Notices",
            "Amendment / Modification",
            "Entire Agreement",
            "Severability"
        ]
    
    def _get_industry_specific_clauses(self, industry: str) -> List[str]:
        """Get industry-specific clauses"""
        industry_clauses_map = {
            "construction": [
                "Performance Bond",
                "Insurance Requirements",
                "Delay Penalties / Liquidated Damages",
                "Quality Standards",
                "Safety Requirements",
                "Change Orders",
                "Site Access",
                "Material Specifications"
            ],
            "technology": [
                "Service Level Agreements (SLA)",
                "Data Protection / GDPR",
                "Software Licensing",
                "Maintenance and Support",
                "Cybersecurity Requirements",
                "Source Code Escrow",
                "API Usage Terms"
            ],
            "finance": [
                "Regulatory Compliance",
                "Anti-Money Laundering (AML)",
                "Know Your Customer (KYC)",
                "Audit Rights",
                "Financial Reporting",
                "Interest Rates and Fees",
                "Default and Remedies"
            ],
            "healthcare": [
                "HIPAA Compliance / Patient Privacy",
                "Medical Liability Insurance",
                "Quality of Care Standards",
                "Credentialing Requirements",
                "Emergency Procedures",
                "Medical Records Management"
            ],
        }
        
        if industry:
            return industry_clauses_map.get(industry.lower(), [])
        return []
    
    def _calculate_compliance_score(self, compliance_items: List[Dict]) -> float:
        """Calculate overall compliance score"""
        if not compliance_items:
            return 0.0
        
        present = sum(1 for item in compliance_items if item.get("status") == "present")
        incomplete = sum(1 for item in compliance_items if item.get("status") == "incomplete")
        total = len(compliance_items)
        
        # Present clauses = full points, incomplete = 50% points
        score = ((present * 1.0) + (incomplete * 0.5)) / total * 100
        return round(score, 2)
