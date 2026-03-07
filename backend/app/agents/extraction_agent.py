"""
Extraction Agent - Extracts structured data from contract text
"""
import logging
from typing import Dict, Any
import json

from app.services.ollama_service import ollama_service
from app.models.schemas import Language

logger = logging.getLogger(__name__)


class ExtractionAgent:
    """Agent for extracting structured data from contracts"""
    
    def __init__(self):
        self.openai_service = ollama_service
    
    async def extract_data(self, contract_text: str, language: Language) -> Dict[str, Any]:
        """
        Extract structured data from contract
        
        Args:
            contract_text: Full contract text
            language: Contract language
            
        Returns:
            Extracted structured data
        """
        logger.info(f"Extracting data from contract (language: {language.value})")
        
        lang_instruction = (
            "The contract is in Arabic. Extract information accordingly."
            if language == Language.ARABIC
            else "The contract is in English."
        )
        
        system_prompt = f"""You are an expert contract analyst. Extract comprehensive structured information from the contract text.
{lang_instruction}

Extract the following information in strict JSON format:

**Document Metadata:**
- contract_title: Name/title of the agreement
- contract_type: Type (NDA, SaaS, Employment, Procurement, Partnership, License, etc.)
- status: Current status if mentioned (Draft/Active/Terminated)
- language: Document language

**Parties & Entities:**
- parties: Array of contracting parties with their roles and contact info
- organizations: All organization/company names mentioned
- people: All person names mentioned
- addresses: All addresses found

**Critical Dates:**
- effective_date: When contract becomes active
- execution_date: When contract was signed
- expiration_date: When agreement ends
- key_dates: Other important dates (milestones, renewal dates, etc.)

**Financial Information:**
- contract_value: Total monetary value if specified
- currency: Primary currency used
- financial_terms: Payment amounts, schedules, penalties
- money_amounts: All monetary values mentioned with context
- percentages: All percentages mentioned with context

**Legal & Governance:**
- governing_law: Legal jurisdiction (e.g., "New York", "UK", "Delaware")
- jurisdiction: Where disputes will be resolved
- locations: All geographic locations mentioned

**Obligations & Responsibilities:**
- obligations: Key obligations with party, action, and deadline

Be precise and extract actual values from the text. If information is not found, use null or empty array."""
        
        schema = {
            # Document Metadata
            "contract_title": "string or null",
            "contract_type": "string or null",
            "status": "string or null",
            "language": "string or null",
            
            # Parties & Named Entities (NER)
            "parties": [
                {"name": "string", "role": "string", "contact": "string or null"}
            ],
            "organizations": ["string"],  # All companies/orgs mentioned
            "people": ["string"],  # All person names
            "addresses": ["string"],  # All addresses
            
            # Critical Dates
            "effective_date": "string or null",
            "execution_date": "string or null",
            "expiration_date": "string or null",
            "key_dates": [
                {"date_type": "string", "date": "string", "description": "string or null"}
            ],
            
            # Financial Information
            "contract_value": "number or null",
            "currency": "string or null",
            "financial_terms": [
                {
                    "description": "string",
                    "amount": "number or null",
                    "currency": "string",
                    "payment_schedule": "string or null"
                }
            ],
            "money_amounts": [
                {"amount": "string", "context": "string"}
            ],
            "percentages": [
                {"percentage": "string", "context": "string"}
            ],
            
            # Legal & Governance
            "governing_law": "string or null",
            "jurisdiction": "string or null",
            "locations": ["string"],  # All geographic locations
            
            # Obligations
            "obligations": [
                {"party": "string", "action": "string", "deadline": "string or null"}
            ]
        }
        
        try:
            # Truncate text if too long (keep first ~16000 characters)
            truncated_text = contract_text[:16000] if len(contract_text) > 16000 else contract_text
            
            extracted_data = await self.openai_service.structured_extraction(
                prompt=system_prompt,
                context=truncated_text,
                schema=schema
            )
            
            logger.info(f"Successfully extracted data: {len(extracted_data.get('parties', []))} parties found")
            return extracted_data
            
        except Exception as e:
            logger.error(f"Error extracting data: {e}", exc_info=True)
            # Return empty structure on error
            return {
                # Document Metadata
                "contract_title": None,
                "contract_type": None,
                "status": None,
                "language": language.value,
                
                # Parties & Named Entities
                "parties": [],
                "organizations": [],
                "people": [],
                "addresses": [],
                
                # Critical Dates
                "effective_date": None,
                "execution_date": None,
                "expiration_date": None,
                "key_dates": [],
                
                # Financial Information
                "contract_value": None,
                "currency": None,
                "financial_terms": [],
                "money_amounts": [],
                "percentages": [],
                
                # Legal & Governance
                "governing_law": None,
                "jurisdiction": None,
                "locations": [],
                
                # Obligations
                "obligations": []
            }
