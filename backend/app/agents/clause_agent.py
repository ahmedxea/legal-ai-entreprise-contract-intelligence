"""
Clause Generation Agent - Generates contract clauses based on parameters
"""
import logging
from typing import Dict, Any, List
import json

from app.services.ollama_service import ollama_service
from app.services.clause_service import ClauseService
from app.models.schemas import Industry, GoverningLaw, Language

logger = logging.getLogger(__name__)


class ClauseGenerationAgent:
    """Agent for generating contract clauses"""
    
    def __init__(self):
        self.openai_service = ollama_service
        self.clause_service = ClauseService()
    
    async def generate_clauses(
        self,
        industry: Industry,
        governing_law: GoverningLaw,
        language: Language,
        clause_types: List[str],
        custom_parameters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate contract clauses based on parameters
        
        Args:
            industry: Industry sector
            governing_law: Governing law jurisdiction
            language: Clause language
            clause_types: Types of clauses to generate
            custom_parameters: Additional customization
            
        Returns:
            List of generated clauses
        """
        logger.info(f"Generating clauses for {industry.value} / {governing_law.value}")
        
        generated_clauses = []
        
        for clause_type in clause_types:
            try:
                clause = await self._generate_single_clause(
                    clause_type=clause_type,
                    industry=industry,
                    governing_law=governing_law,
                    language=language,
                    custom_parameters=custom_parameters or {}
                )
                generated_clauses.append(clause)
                
            except Exception as e:
                logger.error(f"Error generating clause {clause_type}: {e}")
                generated_clauses.append({
                    "type": clause_type,
                    "content": f"Error generating {clause_type} clause",
                    "error": str(e)
                })
        
        return generated_clauses
    
    async def _generate_single_clause(
        self,
        clause_type: str,
        industry: Industry,
        governing_law: GoverningLaw,
        language: Language,
        custom_parameters: Dict
    ) -> Dict[str, Any]:
        """Generate a single clause"""
        
        # Get template guidance
        template_guidance = self._get_clause_guidance(clause_type, industry, governing_law)
        
        lang_instruction = (
            "Generate the clause in Arabic with professional legal terminology."
            if language == Language.ARABIC
            else "Generate the clause in English."
        )
        
        system_prompt = f"""You are an expert legal drafter specializing in {governing_law.value} contract law.

Task: Draft a {clause_type} clause for a {industry.value} contract.

Requirements:
- Must comply with {governing_law.value} legal standards
- Use clear, unambiguous language
- Include all necessary legal protections
- Be balanced and fair to both parties
- {lang_instruction}

Guidance for this clause type:
{template_guidance}

Custom Parameters:
{json.dumps(custom_parameters, indent=2)}

Provide the clause text only, professionally drafted."""
        
        try:
            clause_text = await self.openai_service.chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Draft a {clause_type} clause"}
                ],
                temperature=0.5,
                max_tokens=1000
            )
            
            return {
                "type": clause_type,
                "content": clause_text,
                "industry": industry.value,
                "governing_law": governing_law.value,
                "language": language.value,
                "metadata": {
                    "generated": True,
                    "custom_parameters": custom_parameters
                }
            }
            
        except Exception as e:
            logger.error(f"Error in clause generation: {e}")
            raise
    
    def _get_clause_guidance(
        self,
        clause_type: str,
        industry: Industry,
        governing_law: GoverningLaw
    ) -> str:
        """Get guidance for specific clause type"""
        
        guidance_map = {
            "confidentiality": """
Should include:
- Definition of confidential information
- Obligations of receiving party
- Exceptions (public knowledge, required by law)
- Duration of obligation
- Remedies for breach
""",
            "termination": """
Should include:
- Termination for convenience (notice period)
- Termination for cause (breach conditions)
- Notice requirements
- Effects of termination
- Survival of obligations
""",
            "payment": """
Should include:
- Payment amount and schedule
- Payment method
- Late payment consequences
- Currency
- Tax treatment
""",
            "liability": """
Should include:
- Cap on liability (if any)
- Exclusions (consequential damages, etc.)
- Exceptions to limitations
- Insurance requirements
- Indemnification
""",
            "dispute_resolution": """
Should include:
- Escalation process
- Mediation/arbitration requirements  
- Venue and governing law
- Cost allocation
- Interim relief provisions
""",
            "force_majeure": """
Should include:
- Definition of force majeure events
- Notice requirements
- Suspension of obligations
- Right to terminate if prolonged
- Mitigation obligations
""",
        }
        
        generic_guidance = guidance_map.get(clause_type.lower(), "Draft a comprehensive, legally sound clause.")
        
        jurisdiction_notes = self._get_jurisdiction_notes(governing_law, clause_type)
        industry_notes = self._get_industry_notes(industry, clause_type)
        
        return f"{generic_guidance}\n\nJurisdiction Notes:\n{jurisdiction_notes}\n\nIndustry Notes:\n{industry_notes}"
    
    def _get_jurisdiction_notes(self, governing_law: GoverningLaw, clause_type: str) -> str:
        """Get jurisdiction-specific notes"""
        if governing_law == GoverningLaw.QATAR:
            return "Ensure compliance with Qatar Civil Code and Commercial Law. Consider Sharia principles if applicable."
        elif governing_law == GoverningLaw.UK:
            return "Follow English law principles. Consider Unfair Contract Terms Act."
        elif governing_law == GoverningLaw.UAE:
            return "Comply with UAE Civil Transactions Law. Arabic may be required."
        return "Apply general international contract principles."
    
    def _get_industry_notes(self, industry: Industry, clause_type: str) -> str:
        """Get industry-specific notes"""
        if industry == Industry.CONSTRUCTION and clause_type.lower() in ["payment", "termination"]:
            return "Include provisions for milestone payments, retention, and project delays."
        elif industry == Industry.TECHNOLOGY and clause_type.lower() in ["confidentiality", "liability"]:
            return "Address data protection, IP rights, and SLA requirements."
        return "Apply industry best practices."
