"""
Legal Advisory Agent - Provides legal opinions and comparisons with regulations
"""
import logging
from typing import Dict, Any, List
import json

from app.services.ollama_service import ollama_service
from app.models.schemas import Language, GoverningLaw

logger = logging.getLogger(__name__)


class LegalAdvisoryAgent:
    """Agent for providing legal opinions and regulatory compliance advice"""
    
    def __init__(self):
        self.openai_service = ollama_service
    
    async def provide_legal_opinion(
        self,
        contract_text: str,
        extracted_data: Dict[str, Any],
        language: Language,
        governing_law: str = None
    ) -> Dict[str, Any]:
        """
        Provide legal advisory and opinions on contract
        
        Args:
            contract_text: Full contract text
            extracted_data: Previously extracted data
            language: Contract language
            governing_law: Governing law jurisdiction
            
        Returns:
            Legal opinions and advice
        """
        logger.info(f"Providing legal opinion (governing law: {governing_law})")
        
        lang_instruction = (
            "The contract is in Arabic. Provide analysis in English with Arabic legal terminology where appropriate."
            if language == Language.ARABIC
            else "The contract is in English."
        )
        
        jurisdiction_context = self._get_jurisdiction_context(governing_law)
        
        system_prompt = f"""You are an expert legal advisor specializing in contract law with deep knowledge of international and regional regulations.
{lang_instruction}

{jurisdiction_context}

Your task is to:

1. **Analyze Key Clauses:**
   - Examine critical clauses for legal soundness
   - Identify potential enforceability issues
   - Flag ambiguous or problematic language

2. **Provide Legal Opinions:**
   - Comment on the fairness and balance of obligations
   - Assess the reasonableness of liability provisions
   - Evaluate dispute resolution mechanisms
   - Comment on indemnification clauses

3. **Compare with Regulatory Standards:**
   - Identify requirements under applicable laws
   - Flag potential regulatory compliance issues
   - Suggest alignment with best practices
   - Note any specific legal requirements for the jurisdiction

4. **Recommend Improvements:**
   - Suggest clause modifications for better protection
   - Recommend additional clauses if needed
   - Advise on risk mitigation strategies

Provide your analysis in JSON format with:
- legal_opinions: Array of opinions with topic, opinion, legal_basis, recommendation, and severity
- regulatory_compliance: Compliance assessment
- recommendations: List of actionable recommendations"""
        
        try:
            context = f"""Contract Overview:
- Type: {extracted_data.get('contract_type', 'Unknown')}
- Parties: {', '.join([p.get('name', '') for p in extracted_data.get('parties', [])])}
- Governing Law: {governing_law or 'Not specified'}
- Value: {extracted_data.get('contract_value', 'Not specified')}

Contract Text (First 10000 chars):
{contract_text[:10000]}

Key Financial Terms:
{json.dumps(extracted_data.get('financial_terms', []), indent=2)}

Key Obligations:
{json.dumps(extracted_data.get('obligations', []), indent=2)}"""
            
            response = await self.openai_service.chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": context}
                ],
                temperature=0.3,
                max_tokens=4000,
                response_format={"type": "json_object"}
            )
            
            analysis = json.loads(response)
            
            # Ensure required structure
            if "legal_opinions" not in analysis:
                analysis["legal_opinions"] = []
            if "regulatory_compliance" not in analysis:
                analysis["regulatory_compliance"] = {}
            if "recommendations" not in analysis:
                analysis["recommendations"] = []
            
            logger.info(f"Legal opinion complete: {len(analysis['legal_opinions'])} opinions provided")
            return analysis
            
        except Exception as e:
            logger.error(f"Error in legal advisory: {e}", exc_info=True)
            return {
                "legal_opinions": [],
                "regulatory_compliance": {},
                "recommendations": [],
                "error": str(e)
            }
    
    def _get_jurisdiction_context(self, governing_law: str) -> str:
        """Get jurisdiction-specific legal context"""
        jurisdiction_knowledge = {
            "qatar": """Qatar Legal Context:
- Governed by Qatar Civil Code (Law No. 22 of 2004)
- Commercial contracts regulated by Commercial Law (Law No. 27 of 2006)
- Qatar Financial Centre (QFC) has separate legal framework
- Islamic law (Sharia) principles may apply
- Key requirements: Arabic language for certain contracts, specific formalities for commercial transactions
- Labor contracts must comply with Labor Law No. 14 of 2004
- Data protection: Personal Data Privacy Law (Law No. 13 of 2016)""",
            
            "uk": """UK Legal Context:
- Governed by English contract law principles
- Subject to common law precedents
- Consumer Rights Act 2015 for consumer contracts
- Unfair Contract Terms Act 1977 for business contracts
- Late Payment legislation for commercial contracts
- GDPR and Data Protection Act 2018 for data processing
- Strong emphasis on freedom of contract with statutory protections""",
            
            "uae": """UAE Legal Context:
- Federal Law No. 5 of 1985 (Civil Transactions Law)
- Commercial Transactions Law (Federal Law No. 18 of 1993)
- Free zones may have separate regulations
- Islamic law principles applicable
- Arabic may be required for official purposes
- Recent reforms to modernize commercial law
- Data Protection Law requirements""",
        }
        
        if governing_law:
            law_key = governing_law.lower().strip()
            return jurisdiction_knowledge.get(law_key, "General international contract law principles apply.")
        
        return "No specific governing law identified. General contract law principles  apply."
