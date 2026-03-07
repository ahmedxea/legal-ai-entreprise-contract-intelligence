"""
Risk Analysis Agent - Identifies risks and unusual clauses
"""
import logging
from typing import Dict, Any, List
import json

from app.services.ollama_service import ollama_service
from app.models.schemas import Language, RiskLevel

logger = logging.getLogger(__name__)


class RiskAnalysisAgent:
    """Agent for analyzing contract risks"""
    
    def __init__(self):
        self.openai_service = ollama_service
    
    async def analyze_risks(
        self,
        contract_text: str,
        extracted_data: Dict[str, Any],
        language: Language,
        industry: str = None
    ) -> Dict[str, Any]:
        """
        Analyze contract for risks
        
        Args:
            contract_text: Full contract text
            extracted_data: Previously extracted structured data
            language: Contract language
            industry: Industry sector
            
        Returns:
            Risk analysis results
        """
        logger.info(f"Analyzing risks for contract (industry: {industry})")
        
        lang_instruction = (
            "The contract is in Arabic." if language == Language.ARABIC else "The contract is in English."
        )
        
        industry_context = (
            f"\nThis is a {industry} contract. Consider industry-specific risks."
            if industry else ""
        )
        
        system_prompt = f"""You are an expert legal risk analyst specializing in contract review.
{lang_instruction}{industry_context}

Analyze the contract for the following risks:

1. **High-Risk Clauses:**
   - Unlimited liability
   - Unreasonable indemnification
   - Automatic renewal without notice
   - Unfair termination conditions
   - Excessive penalties
   - One-sided obligations
   - IP rights issues

2. **Unusual Terms:**
   - Non-standard payment terms
   - Uncommon governing law
   - Unusual jurisdiction clauses
   - Non-market-standard provisions

3. **Missing Standard Clauses:**
   - Confidentiality clause
   - Force majeure
   - Dispute resolution
   - Termination rights
   - Limitation of liability
   - Data protection (if applicable)
   - Insurance requirements

4. **Inconsistencies:**
   - Contradictory terms
   - Undefined terms used in obligations
   - Ambiguous language

For each risk identified, provide:
- risk_type: Category of risk
- severity: "low", "medium", "high", or "critical"
- description: Clear explanation of the risk
- clause_reference: Quote the relevant clause (if applicable)
- recommendation: Suggested action or mitigation

Also calculate an overall_risk_score from 0-10 (10 being highest risk)."""

        try:
            # Create context with extracted data
            context = f"""Contract Text (First 8000 chars):
{contract_text[:8000]}

Extracted Key Information:
- Parties: {json.dumps(extracted_data.get('parties', []))}
- Dates: {json.dumps(extracted_data.get('key_dates', []))}
- Financial Terms: {json.dumps(extracted_data.get('financial_terms', []))}
- Governing Law: {extracted_data.get('governing_law', 'Not specified')}

Analyze the contract for risks and provide your analysis in JSON format."""
            
            response = await self.openai_service.chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": context}
                ],
                temperature=0.2,
                max_tokens=4000,
                response_format={"type": "json_object"}
            )
            
            analysis = json.loads(response)
            
            # Ensure required fields
            if "risks" not in analysis:
                analysis["risks"] = []
            if "overall_risk_score" not in analysis:
                analysis["overall_risk_score"] = self._calculate_risk_score(analysis["risks"])
            
            logger.info(f"Risk analysis complete: {len(analysis['risks'])} risks identified, score: {analysis['overall_risk_score']}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error in risk analysis: {e}", exc_info=True)
            return {
                "risks": [],
                "overall_risk_score": 0,
                "error": str(e)
            }
    
    def _calculate_risk_score(self, risks: List[Dict]) -> float:
        """Calculate overall risk score based on identified risks"""
        if not risks:
            return 0.0
        
        severity_weights = {
            "low": 1,
            "medium": 3,
            "high": 6,
            "critical": 10
        }
        
        total_weight = sum(
            severity_weights.get(risk.get("severity", "low"), 1)
            for risk in risks
        )
        
        # Normalize to 0-10 scale
        score = min(10.0, total_weight / max(1, len(risks)))
        return round(score, 2)
