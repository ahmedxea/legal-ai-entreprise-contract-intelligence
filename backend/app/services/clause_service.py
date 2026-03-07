"""
Clause Service - Manages clause templates and library
"""
import logging
from typing import List, Optional, Dict, Any
import json

from app.models.schemas import ClauseTemplate, Industry, GoverningLaw, Language, RiskLevel

logger = logging.getLogger(__name__)


class ClauseService:
    """Service for managing clause templates"""
    
    def __init__(self):
        self.templates_cache = self._load_default_templates()
    
    async def get_templates(
        self,
        industry: Optional[Industry] = None,
        jurisdiction: Optional[GoverningLaw] = None,
        language: Language = Language.ENGLISH
    ) -> List[ClauseTemplate]:
        """
        Get clause templates matching criteria
        
        Args:
            industry: Filter by industry
            jurisdiction: Filter by governing law
            language: Filter by language
            
        Returns:
            List of matching templates
        """
        templates = self.templates_cache
        
        # Filter by criteria
        if industry:
            templates = [t for t in templates if industry in t.industry]
        
        if jurisdiction:
            templates = [t for t in templates if t.jurisdiction == jurisdiction]
        
        if language:
            templates = [t for t in templates if t.language == language]
        
        return templates
    
    def _load_default_templates(self) -> List[ClauseTemplate]:
        """Load default clause templates"""
        
        # Sample templates for MVP
        templates = [
            ClauseTemplate(
                id="conf_001",
                type="Confidentiality",
                industry=[Industry.TECHNOLOGY, Industry.FINANCE],
                jurisdiction=GoverningLaw.QATAR,
                language=Language.ENGLISH,
                template="""CONFIDENTIALITY

Each party agrees to keep confidential all Confidential Information disclosed by the other party and shall not disclose such information to any third party without prior written consent, except as required by law.

"Confidential Information" means all non-public information disclosed by either party.

This obligation shall survive for a period of [X] years after termination of this Agreement.""",
                legal_basis="Qatar Civil Code Article 123",
                risk_level=RiskLevel.LOW
            ),
            ClauseTemplate(
                id="term_001",
                type="Termination",
                industry=[Industry.SERVICES, Industry.CONSTRUCTION],
                jurisdiction=GoverningLaw.QATAR,
                language=Language.ENGLISH,
                template="""TERMINATION

Either party may terminate this Agreement:
(a) For convenience upon [30] days written notice
(b) For cause if the other party materially breaches and fails to cure within [15] days
(c) Immediately if the other party becomes insolvent

Upon termination, all outstanding payments shall become immediately due.""",
                risk_level=RiskLevel.LOW
            ),
            ClauseTemplate(
                id="liability_001",
                type="Limitation of Liability",
                industry=[Industry.TECHNOLOGY, Industry.SERVICES],
                jurisdiction=GoverningLaw.QATAR,
                language=Language.ENGLISH,
                template="""LIMITATION OF LIABILITY

To the maximum extent permitted by law, neither party shall be liable for indirect, incidental, consequential, or punitive damages.

The total liability of either party shall not exceed the total fees paid under this Agreement in the twelve (12) months preceding the claim.

This limitation shall not apply to: (a) death or personal injury, (b) fraud, or (c) willful misconduct.""",
                risk_level=RiskLevel.MEDIUM
            ),
            ClauseTemplate(
                id="dispute_001",
                type="Dispute Resolution",
                industry=[Industry.CONSTRUCTION, Industry.FINANCE],
                jurisdiction=GoverningLaw.QATAR,
                language=Language.ENGLISH,
                template="""DISPUTE RESOLUTION

Any dispute arising from this Agreement shall be resolved as follows:

1. Negotiation: The parties shall first attempt to resolve the dispute through good faith negotiation
2. Mediation: If unresolved within [30] days, the parties shall attempt mediation
3. Arbitration: If mediation fails, the dispute shall be resolved by arbitration in accordance with Qatar International Court and Dispute Resolution Centre (QICDRC) rules

The seat of arbitration shall be Doha, Qatar. The language shall be English/Arabic.""",
                legal_basis="Qatar Arbitration Law",
                risk_level=RiskLevel.LOW
            ),
        ]
        
        return templates
