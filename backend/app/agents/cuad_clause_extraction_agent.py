"""
CUAD Clause Extraction Agent

Extracts structured clause information from contracts using LLM.
Based on the Contract Understanding Atticus Dataset (CUAD) methodology.

This agent:
1. Identifies presence of specific clause types  
2. Extracts clause text and location
3. Returns structured JSON output
4. Focuses on 15 high-priority CUAD clause categories

The LLM is used ONLY for extraction, NOT for risk evaluation.
Risk evaluation is performed by the deterministic RiskEvaluationEngine.
"""

import logging
import json
from typing import Dict, Any
from app.services.ollama_service import ollama_service
from app.models.schemas import Language
from app.models.clause_schema import (
    ContractAnalysisSchema,
    ClauseAnalysis,
    ClauseType
)

logger = logging.getLogger(__name__)


class CUADClauseExtractionAgent:
    """
    Extract CUAD-based clause information from contracts
    
    Uses LLM for clause detection and text extraction only.
    Risk evaluation is performed separately by RiskEvaluationEngine.
    """
    
    def __init__(self, ai_service=None):
        """Initialize the clause extraction agent"""
        self.ai_service = ai_service or ollama_service
    
    async def extract_clauses(
        self,
        contract_id: str,
        contract_text: str,
        language: Language = Language.ENGLISH
    ) -> ContractAnalysisSchema:
        """
        Extract all CUAD clause types from contract
        
        Args:
            contract_id: Unique contract identifier
            contract_text: Full contract text
            language: Contract language
            
        Returns:
            ContractAnalysisSchema with extracted clauses (risk evaluation NOT included)
        """
        logger.info(f"Starting CUAD clause extraction for contract {contract_id}")
        
        # Truncate text if too long (keep first ~20000 characters for context)
        if len(contract_text) > 20000:
            contract_text = contract_text[:20000]
            logger.info("Contract text truncated to 20000 characters")
        
        # Extract contract metadata first
        metadata = await self._extract_metadata(contract_text, language)
        
        # Extract each clause type
        clauses = await self._extract_all_clauses(contract_text, language)
        
        # Build structured analysis
        analysis = ContractAnalysisSchema(
            contract_id=contract_id,
            contract_parties=metadata.get("parties", []),
            effective_date=metadata.get("effective_date"),
            expiration_date=metadata.get("expiration_date"),
            governing_law=clauses.get("governing_law", ClauseAnalysis(present=False)),
            confidentiality=clauses.get("confidentiality", ClauseAnalysis(present=False)),
            termination=clauses.get("termination", ClauseAnalysis(present=False)),
            liability=clauses.get("liability", ClauseAnalysis(present=False)),
            indemnification=clauses.get("indemnification", ClauseAnalysis(present=False)),
            payment_terms=clauses.get("payment_terms", ClauseAnalysis(present=False)),
            intellectual_property=clauses.get("intellectual_property", ClauseAnalysis(present=False)),
            data_protection=clauses.get("data_protection", ClauseAnalysis(present=False)),
            force_majeure=clauses.get("force_majeure", ClauseAnalysis(present=False)),
            # New clauses (v2.0)
            non_compete=clauses.get("non_compete", ClauseAnalysis(present=False)),
            exclusivity=clauses.get("exclusivity", ClauseAnalysis(present=False)),
            change_of_control=clauses.get("change_of_control", ClauseAnalysis(present=False)),
            anti_assignment=clauses.get("anti_assignment", ClauseAnalysis(present=False)),
            audit_rights=clauses.get("audit_rights", ClauseAnalysis(present=False)),
            post_termination_services=clauses.get("post_termination_services", ClauseAnalysis(present=False))
        )
        
        logger.info(f"Clause extraction completed for contract {contract_id}")
        return analysis
    
    async def _extract_metadata(self, contract_text: str, language: Language) -> Dict[str, Any]:
        """
        Extract contract metadata (parties, dates)
        
        Args:
            contract_text: Contract text
            language: Contract language
            
        Returns:
            Dictionary with parties and key dates
        """
        lang_instruction = (
            "The contract is in Arabic. Extract information accordingly."
            if language == Language.ARABIC
            else "The contract is in English."
        )
        
        system_prompt = f"""You are a legal contract analyst. Extract basic contract metadata.
{lang_instruction}

Extract the following in JSON format:
- parties: Array of party names (just the organization/company names)
- effective_date: Contract effective date (YYYY-MM-DD format if found, otherwise null)
- expiration_date: Contract expiration/end date (YYYY-MM-DD format if found, otherwise null)

Return only the JSON, no additional text."""
        
        try:
            result = await self.ai_service.structured_extraction(
                prompt=system_prompt,
                context=contract_text[:5000],  # First 5000 chars usually contain metadata
                schema={
                    "parties": ["string"],
                    "effective_date": "string or null",
                    "expiration_date": "string or null"
                }
            )
            return result
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}", exc_info=True)
            return {"parties": [], "effective_date": None, "expiration_date": None}
    
    async def _extract_all_clauses(
        self,
        contract_text: str,
        language: Language
    ) -> Dict[str, ClauseAnalysis]:
        """
        Extract all CUAD clause types in one LLM call
        
        Args:
            contract_text: Contract text
            language: Contract language
            
        Returns:
            Dictionary mapping clause types to ClauseAnalysis objects
        """
        lang_instruction = (
            "The contract is in Arabic."
            if language == Language.ARABIC
            else "The contract is in English."
        )
        
        system_prompt = f"""You are a legal contract analyst trained on the CUAD (Contract Understanding Atticus Dataset).

{lang_instruction}

Analyze this contract and identify the following 15 clause types. For EACH clause type, determine:
1. Is it present in the contract? (true/false)
2. If present, extract the relevant text (first 500 characters maximum)
3. If present, note the section/location where it was found

CLAUSE TYPES TO IDENTIFY:

1. **Governing Law**: Which jurisdiction's laws govern the contract
   - Look for phrases like: "governed by", "laws of", "jurisdiction"

2. **Confidentiality / Non-Disclosure**: Protects confidential information
   - Look for: "confidential", "non-disclosure", "proprietary information"

3. **Termination**: How the contract can be terminated
   - Look for: "termination", "terminate", "end this agreement", "notice period"

4. **Liability / Limitation of Liability**: Liability limits and caps
   - Look for: "liability", "liable", "limitation of liability", "damages"

5. **Indemnification**: Who indemnifies whom for what
   - Look for: "indemnify", "indemnification", "hold harmless"

6. **Payment Terms**: Payment amounts, schedules, methods
   - Look for: "payment", "fees", "price", "invoice", "pay"

7. **Intellectual Property**: IP ownership and rights
   - Look for: "intellectual property", "IP", "copyright", "patent", "trademark", "ownership"

8. **Data Protection / Privacy**: Data privacy and protection obligations
   - Look for: "data protection", "privacy", "GDPR", "CCPA", "personal data"

9. **Force Majeure**: Extraordinary events clause
   - Look for: "force majeure", "act of god", "unforeseen circumstances"

10. **Non-Compete**: Restrictions on competing with counterparty
   - Look for: "non-compete", "shall not compete", "competition", "competitive restriction"

11. **Exclusivity**: Exclusive dealing or sole sourcing requirements
   - Look for: "exclusive", "non-exclusive", "sole", "only party", "exclusively"

12. **Change of Control**: Rights/obligations upon M&A or ownership change
   - Look for: "change of control", "merger", "acquisition", "change in ownership"

13. **Anti-Assignment**: Restrictions on assigning/transferring the contract
   - Look for: "assignment", "assign", "transfer", "may not assign"

14. **Audit Rights**: Right to audit compliance or records
   - Look for: "audit", "right to audit", "inspect", "examination of records"

15. **Post-Termination Services**: Obligations after contract ends
   - Look for: "post-termination", "after termination", "transition", "wind down"

Return a JSON object with this EXACT structure:
{{
  "governing_law": {{
    "present": true/false,
    "text": "extracted clause text or null",
    "location": "Section name/number or null"
  }},
  "confidentiality": {{ ... }},
  "termination": {{ ... }},
  "liability": {{ ... }},
  "indemnification": {{ ... }},
  "payment_terms": {{ ... }},
  "intellectual_property": {{ ... }},
  "data_protection": {{ ... }},
  "force_majeure": {{ ... }}
}}

Return ONLY the JSON, no additional text."""
        
        try:
            result = await self.ai_service.structured_extraction(
                prompt=system_prompt,
                context=contract_text,
                schema={
                    "governing_law": {
                        "present": "boolean",
                        "text": "string or null",
                        "location": "string or null"
                    },
                    "confidentiality": {
                        "present": "boolean",
                        "text": "string or null",
                        "location": "string or null"
                    },
                    "termination": {
                        "present": "boolean",
                        "text": "string or null",
                        "location": "string or null"
                    },
                    "liability": {
                        "present": "boolean",
                        "text": "string or null",
                        "location": "string or null"
                    },
                    "indemnification": {
                        "present": "boolean",
                        "text": "string or null",
                        "location": "string or null"
                    },
                    "payment_terms": {
                        "present": "boolean",
                        "text": "string or null",
                        "location": "string or null"
                    },
                    "intellectual_property": {
                        "present": "boolean",
                        "text": "string or null",
                        "location": "string or null"
                    },
                    "data_protection": {
                        "present": "boolean",
                        "text": "string or null",
                        "location": "string or null"
                    },
                    "force_majeure": {
                        "present": "boolean",
                        "text": "string or null",
                        "location": "string or null"
                    },
                    "non_compete": {
                        "present": "boolean",
                        "text": "string or null",
                        "location": "string or null"
                    },
                    "exclusivity": {
                        "present": "boolean",
                        "text": "string or null",
                        "location": "string or null"
                    },
                    "change_of_control": {
                        "present": "boolean",
                        "text": "string or null",
                        "location": "string or null"
                    },
                    "anti_assignment": {
                        "present": "boolean",
                        "text": "string or null",
                        "location": "string or null"
                    },
                    "audit_rights": {
                        "present": "boolean",
                        "text": "string or null",
                        "location": "string or null"
                    },
                    "post_termination_services": {
                        "present": "boolean",
                        "text": "string or null",
                        "location": "string or null"
                    }
                }
            )
            
            # Convert JSON to ClauseAnalysis objects
            clauses = {}
            for clause_type, data in result.items():
                clauses[clause_type] = ClauseAnalysis(
                    present=data.get("present", False),
                    text=data.get("text"),
                    location=data.get("location")
                )
            
            return clauses
            
        except Exception as e:
            logger.error(f"Error extracting clauses: {e}", exc_info=True)
            # Return empty clauses on error
            return {
                clause_type.value: ClauseAnalysis(present=False)
                for clause_type in ClauseType
            }
    
    async def extract_specific_clause(
        self,
        contract_text: str,
        clause_type: ClauseType,
        language: Language = Language.ENGLISH
    ) -> ClauseAnalysis:
        """
        Extract a single specific clause type
        
        Useful for re-extraction or targeted extraction
        
        Args:
            contract_text: Contract text
            clause_type: Specific clause type to extract
            language: Contract language
            
        Returns:
            ClauseAnalysis for the specific clause
        """
        clause_descriptions = {
            ClauseType.GOVERNING_LAW: "Specifies which jurisdiction's laws govern the contract",
            ClauseType.CONFIDENTIALITY: "Protects confidential and proprietary information",
            ClauseType.TERMINATION: "Defines how and when the contract can be terminated",
            ClauseType.LIABILITY: "Defines liability limits and damage caps",
            ClauseType.INDEMNIFICATION: "Defines indemnification obligations",
            ClauseType.PAYMENT_TERMS: "Specifies payment amounts, schedules, and methods",
            ClauseType.INTELLECTUAL_PROPERTY: "Defines IP ownership and rights",
            ClauseType.DATA_PROTECTION: "Addresses data privacy and protection obligations",
            ClauseType.FORCE_MAJEURE: "Addresses extraordinary events and circumstances"
        }
        
        lang_instruction = (
            "The contract is in Arabic."
            if language == Language.ARABIC
            else "The contract is in English."
        )
        
        description = clause_descriptions.get(clause_type, "Contract clause")
        
        system_prompt = f"""You are a legal contract analyst.

{lang_instruction}

Find and extract the **{clause_type.value.replace('_', ' ').title()}** clause from this contract.

Description: {description}

Return JSON:
{{
  "present": true/false,
  "text": "extracted clause text (max 500 chars) or null",
  "location": "section name/number or null"
}}

Return ONLY the JSON."""
        
        try:
            result = await self.ai_service.structured_extraction(
                prompt=system_prompt,
                context=contract_text,
                schema={
                    "present": "boolean",
                    "text": "string or null",
                    "location": "string or null"
                }
            )
            
            return ClauseAnalysis(
                present=result.get("present", False),
                text=result.get("text"),
                location=result.get("location")
            )
            
        except Exception as e:
            logger.error(f"Error extracting {clause_type.value}: {e}", exc_info=True)
            return ClauseAnalysis(present=False)


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

async def extract_contract_clauses(
    contract_id: str,
    contract_text: str,
    language: Language = Language.ENGLISH
) -> ContractAnalysisSchema:
    """
    Extract CUAD clauses from contract
    
    Convenience function for clause extraction
    
    Args:
        contract_id: Contract ID
        contract_text: Contract text
        language: Contract language
        
    Returns:
        ContractAnalysisSchema with extracted clauses
    """
    agent = CUADClauseExtractionAgent()
    return await agent.extract_clauses(contract_id, contract_text, language)
