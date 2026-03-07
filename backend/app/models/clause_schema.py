"""
CUAD-based Clause Schema and Risk Rules

This module defines the structured contract analysis schema
derived from the Contract Understanding Atticus Dataset (CUAD).

CUAD contains 510 commercial contracts with 13,000+ expert annotations
across 41 legal clause categories.

We focus on 15 high-value enterprise clauses for production:
- Governing Law
- Confidentiality
- Termination
- Liability
- Indemnification
- Payment Terms
- Intellectual Property
- Data Protection
- Force Majeure
- Non-Compete (NEW)
- Exclusivity (NEW)
- Change of Control (NEW)
- Anti-Assignment (NEW)
- Audit Rights (NEW)
- Post-Termination Services (NEW)

Each clause includes:
- present: boolean (found in contract)
- text: string (extracted clause text)
- risk_level: LOW | MEDIUM | HIGH | NONE
- risk_reason: explanation of risk assessment
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    """Risk severity levels"""
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ClauseType(str, Enum):
    """
    CUAD-derived clause categories for enterprise contracts
    Expanded from original 9 to 15 high-priority clauses
    """
    GOVERNING_LAW = "governing_law"
    CONFIDENTIALITY = "confidentiality"
    TERMINATION = "termination"
    LIABILITY = "liability"
    INDEMNIFICATION = "indemnification"
    PAYMENT_TERMS = "payment_terms"
    INTELLECTUAL_PROPERTY = "intellectual_property"
    DATA_PROTECTION = "data_protection"
    FORCE_MAJEURE = "force_majeure"
    # New CUAD categories (v2.0)
    NON_COMPETE = "non_compete"
    EXCLUSIVITY = "exclusivity"
    CHANGE_OF_CONTROL = "change_of_control"
    ANTI_ASSIGNMENT = "anti_assignment"
    AUDIT_RIGHTS = "audit_rights"
    POST_TERMINATION_SERVICES = "post_termination_services"


class ClauseAnalysis(BaseModel):
    """
    Structured analysis of a single clause
    """
    present: bool = Field(default=False, description="Whether clause exists in contract")
    text: Optional[str] = Field(default=None, description="Extracted clause text")
    risk_level: RiskLevel = Field(default=RiskLevel.NONE, description="Risk severity")
    risk_reason: Optional[str] = Field(default=None, description="Why this risk level was assigned")
    location: Optional[str] = Field(default=None, description="Section/page where clause found")
    
    class Config:
        use_enum_values = True


class ContractAnalysisSchema(BaseModel):
    """
    Complete structured contract analysis
    Follows CUAD methodology with risk evaluation
    """
    contract_id: str
    contract_parties: List[str] = Field(default_factory=list)
    effective_date: Optional[str] = None
    expiration_date: Optional[str] = None
    
    # CUAD-based clause analysis (15 total)
    governing_law: ClauseAnalysis = Field(default_factory=lambda: ClauseAnalysis(present=False))
    confidentiality: ClauseAnalysis = Field(default_factory=lambda: ClauseAnalysis(present=False))
    termination: ClauseAnalysis = Field(default_factory=lambda: ClauseAnalysis(present=False))
    liability: ClauseAnalysis = Field(default_factory=lambda: ClauseAnalysis(present=False))
    indemnification: ClauseAnalysis = Field(default_factory=lambda: ClauseAnalysis(present=False))
    payment_terms: ClauseAnalysis = Field(default_factory=lambda: ClauseAnalysis(present=False))
    intellectual_property: ClauseAnalysis = Field(default_factory=lambda: ClauseAnalysis(present=False))
    data_protection: ClauseAnalysis = Field(default_factory=lambda: ClauseAnalysis(present=False))
    force_majeure: ClauseAnalysis = Field(default_factory=lambda: ClauseAnalysis(present=False))
    # New clauses (v2.0)
    non_compete: ClauseAnalysis = Field(default_factory=lambda: ClauseAnalysis(present=False))
    exclusivity: ClauseAnalysis = Field(default_factory=lambda: ClauseAnalysis(present=False))
    change_of_control: ClauseAnalysis = Field(default_factory=lambda: ClauseAnalysis(present=False))
    anti_assignment: ClauseAnalysis = Field(default_factory=lambda: ClauseAnalysis(present=False))
    audit_rights: ClauseAnalysis = Field(default_factory=lambda: ClauseAnalysis(present=False))
    post_termination_services: ClauseAnalysis = Field(default_factory=lambda: ClauseAnalysis(present=False))
    
    class Config:
        use_enum_values = True


class RiskSummary(BaseModel):
    """
    Overall risk assessment for the contract
    
    Production-ready risk summary with:
    - overall_risk: Aggregated risk level
    - high_risk_items: Critical issues requiring attention
    - medium_risk_items: Moderate concerns
    - missing_clauses: Expected clauses not found
    - key_findings: Human-readable insights
    - compliance_gaps: Critical missing clauses for compliance
    - risk_flags: Specific risk indicators (NEW)
    """
    overall_risk: RiskLevel
    high_risk_items: List[Dict[str, str]] = Field(default_factory=list)
    medium_risk_items: List[Dict[str, str]] = Field(default_factory=list)
    missing_clauses: List[str] = Field(default_factory=list)
    key_findings: List[str] = Field(default_factory=list)
    compliance_gaps: List[str] = Field(default_factory=list)
    risk_flags: List[str] = Field(
        default_factory=list,
        description="Specific risk indicators: unlimited liability, missing clauses, automatic renewal, etc."
    )
    
    class Config:
        use_enum_values = True


# ============================================================================
# RISK EVALUATION RULES
# ============================================================================

class RiskRule:
    """
    Base class for risk evaluation rules
    Rules are deterministic and explainable
    """
    
    @staticmethod
    def evaluate_liability_clause(clause_text: str) -> tuple[RiskLevel, str]:
        """
        Evaluate liability clause for risk indicators
        
        HIGH RISK patterns:
        - unlimited liability
        - no limitation of liability
        - uncapped damages
        - consequential damages allowed
        
        MEDIUM RISK patterns:
        - vague liability terms
        - one-sided liability
        
        LOW RISK patterns:
        - capped liability
        - mutual liability caps
        - standard commercial limits
        """
        if not clause_text:
            return RiskLevel.NONE, "No liability clause text provided"
        
        text_lower = clause_text.lower()
        
        # HIGH RISK indicators
        high_risk_patterns = [
            "unlimited liability",
            "no limitation of liability",
            "without limit",
            "uncapped",
            "no cap on liability",
            "consequential damages"
        ]
        
        for pattern in high_risk_patterns:
            if pattern in text_lower:
                return RiskLevel.HIGH, f"Contains high-risk term: '{pattern}'"
        
        # MEDIUM RISK indicators
        medium_risk_patterns = [
            "one-sided",
            "asymmetric",
            "unilateral liability"
        ]
        
        for pattern in medium_risk_patterns:
            if pattern in text_lower:
                return RiskLevel.MEDIUM, f"Contains medium-risk term: '{pattern}'"
        
        # LOW RISK indicators
        low_risk_patterns = [
            "capped",
            "limited to",
            "not exceed",
            "maximum liability",
            "liability cap"
        ]
        
        for pattern in low_risk_patterns:
            if pattern in text_lower:
                return RiskLevel.LOW, "Contains liability cap or limitation"
        
        return RiskLevel.MEDIUM, "Liability clause present but unclear protections"
    
    @staticmethod
    def evaluate_confidentiality_clause(clause_text: str) -> tuple[RiskLevel, str]:
        """
        Evaluate confidentiality clause for completeness
        
        HIGH RISK:
        - No confidentiality protection
        
        MEDIUM RISK:
        - Vague confidentiality terms
        - Missing term duration
        - No clear obligations
        
        LOW RISK:
        - Clear confidentiality obligations
        - Defined term and scope
        - Mutual protections
        """
        if not clause_text:
            return RiskLevel.HIGH, "No confidentiality clause found"
        
        text_lower = clause_text.lower()
        
        # Check for completeness indicators
        has_duration = any(term in text_lower for term in ["years", "term of", "perpetual", "duration"])
        has_obligations = any(term in text_lower for term in ["shall not disclose", "must not", "obligation", "duty"])
        has_scope = any(term in text_lower for term in ["confidential information", "proprietary", "trade secret"])
        
        completeness_score = sum([has_duration, has_obligations, has_scope])
        
        if completeness_score >= 3:
            return RiskLevel.LOW, "Comprehensive confidentiality clause"
        elif completeness_score >= 2:
            return RiskLevel.MEDIUM, "Confidentiality clause present but may lack completeness"
        else:
            return RiskLevel.MEDIUM, "Vague or incomplete confidentiality terms"
    
    @staticmethod
    def evaluate_termination_clause(clause_text: str) -> tuple[RiskLevel, str]:
        """
        Evaluate termination clause for fairness
        
        HIGH RISK:
        - One-sided termination rights
        - No cure period
        
        MEDIUM RISK:
        - Unclear termination conditions
        - Missing notice requirements
        
        LOW RISK:
        - Mutual termination rights
        - Clear cure periods
        - Defined notice requirements
        """
        if not clause_text:
            return RiskLevel.MEDIUM, "No termination clause found"
        
        text_lower = clause_text.lower()
        
        # Check for one-sided termination
        if "at will" in text_lower or "without cause" in text_lower:
            if "either party" in text_lower or "mutual" in text_lower:
                return RiskLevel.LOW, "Mutual at-will termination rights"
            else:
                return RiskLevel.HIGH, "One-sided at-will termination"
        
        # Check for cure period
        has_cure = any(term in text_lower for term in ["cure", "remedy", "correct", "days to cure"])
        has_notice = any(term in text_lower for term in ["notice", "written notice", "days notice"])
        
        if has_cure and has_notice:
            return RiskLevel.LOW, "Clear termination process with cure period"
        elif has_notice:
            return RiskLevel.MEDIUM, "Termination clause with notice but no clear cure period"
        else:
            return RiskLevel.MEDIUM, "Unclear termination conditions"
    
    @staticmethod
    def evaluate_payment_terms(clause_text: str) -> tuple[RiskLevel, str]:
        """
        Evaluate payment terms for clarity
        
        HIGH RISK:
        - No payment terms
        - Completely vague terms
        
        MEDIUM RISK:
        - Ambiguous payment schedule
        - Missing late payment terms
        
        LOW RISK:
        - Clear payment amounts
        - Defined schedule
        - Late payment provisions
        """
        if not clause_text:
            return RiskLevel.HIGH, "No payment terms defined"
        
        text_lower = clause_text.lower()
        
        # Check for key payment components
        has_amount = any(term in text_lower for term in ["$", "usd", "amount", "fee", "price", "cost"])
        has_schedule = any(term in text_lower for term in ["monthly", "annually", "quarterly", "upon", "within", "days"])
        has_late_terms = any(term in text_lower for term in ["late payment", "interest", "penalty", "overdue"])
        
        clarity_score = sum([has_amount, has_schedule, has_late_terms])
        
        if clarity_score >= 3:
            return RiskLevel.LOW, "Comprehensive payment terms"
        elif clarity_score >= 2:
            return RiskLevel.MEDIUM, "Payment terms present but may lack completeness"
        else:
            return RiskLevel.MEDIUM, "Vague or incomplete payment terms"
    
    @staticmethod
    def evaluate_ip_clause(clause_text: str) -> tuple[RiskLevel, str]:
        """
        Evaluate intellectual property clause
        
        HIGH RISK:
        - IP ownership unclear
        - Broad IP assignment to other party
        
        MEDIUM RISK:
        - Vague IP terms
        - Missing specific allocations
        
        LOW RISK:
        - Clear IP ownership
        - Defined scope
        - Protected pre-existing IP
        """
        if not clause_text:
            return RiskLevel.MEDIUM, "No IP clause found"
        
        text_lower = clause_text.lower()
        
        # Check for IP assignment concerns
        if "all intellectual property" in text_lower and "shall belong to" in text_lower:
            if "customer" in text_lower or "client" in text_lower:
                return RiskLevel.HIGH, "Broad IP assignment to other party"
        
        # Check for protections
        has_ownership = any(term in text_lower for term in ["ownership", "owned by", "belongs to"])
        has_scope = any(term in text_lower for term in ["developed", "created", "pre-existing", "background ip"])
        has_license = any(term in text_lower for term in ["license", "right to use", "grant"])
        
        if has_ownership and has_scope:
            return RiskLevel.LOW, "Clear IP ownership and scope"
        elif has_ownership or has_license:
            return RiskLevel.MEDIUM, "IP terms present but may lack clarity"
        else:
            return RiskLevel.MEDIUM, "Vague IP terms"
    
    @staticmethod
    def evaluate_data_protection(clause_text: str) -> tuple[RiskLevel, str]:
        """
        Evaluate data protection clause for compliance
        
        LOW RISK:
        - GDPR/CCPA compliance mentioned
        - Clear data handling obligations
        
        MEDIUM RISK:
        - Generic data protection
        - Missing specific regulations
        
        HIGH RISK:
        - No data protection clause
        """
        if not clause_text:
            return RiskLevel.HIGH, "No data protection clause found"
        
        text_lower = clause_text.lower()
        
        # Check for regulatory compliance
        has_gdpr = "gdpr" in text_lower or "general data protection" in text_lower
        has_ccpa = "ccpa" in text_lower or "california consumer privacy" in text_lower
        has_obligations = any(term in text_lower for term in ["protect", "secure", "safeguard", "security measures"])
        
        if (has_gdpr or has_ccpa) and has_obligations:
            return RiskLevel.LOW, "Includes regulatory compliance and security obligations"
        elif has_obligations:
            return RiskLevel.MEDIUM, "Generic data protection without specific compliance"
        else:
            return RiskLevel.MEDIUM, "Vague data protection terms"
    
    @staticmethod
    def evaluate_non_compete(clause_text: str) -> tuple[RiskLevel, str]:
        """
        Evaluate non-compete clause for restrictiveness
        
        HIGH RISK:
        - Broad geographic restrictions
        - Long duration (>2 years)
        - Vague business restrictions
        
        MEDIUM RISK:
        - Reasonable scope and duration
        - Limited geographic area
        
        LOW RISK:
        - Narrow restrictions
        - Short duration
        - Clear carveouts
        """
        if not clause_text:
            return RiskLevel.NONE, "No non-compete clause"
        
        text_lower = clause_text.lower()
        
        # HIGH RISK indicators
        high_risk_patterns = [
            "indefinitely",
            "worldwide",
            "all businesses",
            "any business",
            "similar business",
            "five years",
            "10 years"
        ]
        
        for pattern in high_risk_patterns:
            if pattern in text_lower:
                return RiskLevel.HIGH, f"Overly broad restriction: '{pattern}'"
        
        # Check duration
        if "year" in text_lower:
            # Extract duration if possible
            if any(term in text_lower for term in ["three year", "four year", "five year"]):
                return RiskLevel.HIGH, "Long non-compete duration (3+ years)"
        
        # MEDIUM RISK indicators
        medium_risk_patterns = [
            "two year",
            "24 month",
            "compete",
            "similar products"
        ]
        
        for pattern in medium_risk_patterns:
            if pattern in text_lower:
                return RiskLevel.MEDIUM, "Non-compete clause with moderate restrictions"
        
        # LOW RISK indicators
        low_risk_patterns = [
            "one year",
            "12 month",
            "specific territory",
            "limited scope",
            "reasonable restriction"
        ]
        
        for pattern in low_risk_patterns:
            if pattern in text_lower:
                return RiskLevel.LOW, "Reasonable non-compete restrictions"
        
        return RiskLevel.MEDIUM, "Non-compete clause present - review scope"
    
    @staticmethod
    def evaluate_exclusivity(clause_text: str) -> tuple[RiskLevel, str]:
        """
        Evaluate exclusivity clause for business flexibility
        
        HIGH RISK:
        - Exclusive dealing without termination rights
        - Indefinite exclusivity
        - No performance requirements
        
        MEDIUM RISK:
        - Limited exclusivity with conditions
        - Time-bound exclusive period
        
        LOW RISK:
        - Non-exclusive arrangement
        - Exclusivity with performance minimums
        """
        if not clause_text:
            return RiskLevel.NONE, "No exclusivity clause"
        
        text_lower = clause_text.lower()
        
        # Check if non-exclusive (LOW RISK)
        if "non-exclusive" in text_lower or "not exclusive" in text_lower:
            return RiskLevel.LOW, "Non-exclusive arrangement maintains flexibility"
        
        # HIGH RISK indicators for exclusivity
        high_risk_patterns = [
            "sole and exclusive",
            "exclusively",
            "only party",
            "no other",
            "indefinite",
            "perpetual exclusive"
        ]
        
        for pattern in high_risk_patterns:
            if pattern in text_lower:
                # Check if there are performance requirements or termination rights
                has_minimums = any(term in text_lower for term in ["minimum", "quota", "target", "volume requirement"])
                has_termination = any(term in text_lower for term in ["terminate if", "termination right", "may terminate"])
                
                if not has_minimums and not has_termination:
                    return RiskLevel.HIGH, f"Restrictive exclusivity without protections: '{pattern}'"
                else:
                    return RiskLevel.MEDIUM, "Exclusivity with some protective conditions"
        
        return RiskLevel.MEDIUM, "Exclusivity clause - review business impact"
    
    @staticmethod
    def evaluate_change_of_control(clause_text: str) -> tuple[RiskLevel, str]:
        """
        Evaluate change of control clause for M&A impact
        
        HIGH RISK:
        - Automatic termination on change
        - No consent provision
        - Broad definition of control
        
        MEDIUM RISK:
        - Requires counterparty consent
        - Reasonable notice period
        
        LOW RISK:
        - No change of control restrictions
        - Automatic continuation provisions
        """
        if not clause_text:
            return RiskLevel.LOW, "No change of control restrictions"
        
        text_lower = clause_text.lower()
        
        # HIGH RISK indicators
        high_risk_patterns = [
            "automatically terminate",
            "shall terminate",
            "terminates upon",
            "void upon change",
            "null and void"
        ]
        
        for pattern in high_risk_patterns:
            if pattern in text_lower and "change of control" in text_lower:
                return RiskLevel.HIGH, f"Automatic termination on change of control: '{pattern}'"
        
        # MEDIUM RISK indicators
        medium_risk_patterns = [
            "consent",
            "approval required",
            "prior written consent",
            "may terminate"
        ]
        
        for pattern in medium_risk_patterns:
            if pattern in text_lower:
                return RiskLevel.MEDIUM, "Requires consent for change of control"
        
        return RiskLevel.LOW, "Change of control mentioned but impact unclear"
    
    @staticmethod
    def evaluate_anti_assignment(clause_text: str) -> tuple[RiskLevel, str]:
        """
        Evaluate anti-assignment clause for transfer restrictions
        
        HIGH RISK:
        - No assignment allowed without consent
        - Broad assignment restrictions
        
        MEDIUM RISK:
        - Reasonable consent requirement
        - Assignment with notice
        
        LOW RISK:
        - Free assignability
        - Assignment to affiliates allowed
        """
        if not clause_text:
            return RiskLevel.LOW, "No assignment restrictions"
        
        text_lower = clause_text.lower()
        
        # Check if assignment is freely allowed
        if "freely assignable" in text_lower or "may assign" in text_lower:
            return RiskLevel.LOW, "Assignment allowed with flexibility"
        
        # HIGH RISK indicators
        high_risk_patterns = [
            "may not assign",
            "shall not assign",
            "no assignment",
            "prohibited from assigning",
            "void if assigned"
        ]
        
        for pattern in high_risk_patterns:
            if pattern in text_lower:
                # Check for affiliate exception
                has_affiliate_exception = "affiliate" in text_lower or "subsidiary" in text_lower
                if has_affiliate_exception:
                    return RiskLevel.MEDIUM, "Assignment restricted except to affiliates"
                else:
                    return RiskLevel.HIGH, f"Strict assignment restriction: '{pattern}'"
        
        # MEDIUM RISK indicators
        medium_risk_patterns = [
            "with consent",
            "prior written consent",
            "reasonable consent",
            "not unreasonably withheld"
        ]
        
        for pattern in medium_risk_patterns:
            if pattern in text_lower:
                return RiskLevel.MEDIUM, "Assignment requires consent"
        
        return RiskLevel.MEDIUM, "Assignment restrictions unclear"
    
    @staticmethod
    def evaluate_audit_rights(clause_text: str) -> tuple[RiskLevel, str]:
        """
        Evaluate audit rights clause for compliance oversight
        
        HIGH RISK:
        - Unlimited audit rights
        - No notice requirement
        - Customer bears all costs
        
        MEDIUM RISK:
        - Reasonable audit rights with notice
        - Limited frequency
        
        LOW RISK:
        - Audit for cause only
        - Shared costs
        - Reasonable frequency limits
        """
        if not clause_text:
            return RiskLevel.LOW, "No audit rights granted"
        
        text_lower = clause_text.lower()
        
        # HIGH RISK indicators
        high_risk_patterns = [
            "at any time",
            "without notice",
            "unlimited access",
            "immediate access",
            "at customer expense"
        ]
        
        for pattern in high_risk_patterns:
            if pattern in text_lower:
                return RiskLevel.HIGH, f"Broad audit rights: '{pattern}'"
        
        # LOW RISK indicators
        low_risk_patterns = [
            "reasonable notice",
            "business hours",
            "once per year",
            "for cause",
            "shared cost",
            "expense borne by"
        ]
        
        for pattern in low_risk_patterns:
            if pattern in text_lower:
                return RiskLevel.LOW, "Reasonable audit rights with limitations"
        
        return RiskLevel.MEDIUM, "Standard audit rights present"
    
    @staticmethod
    def evaluate_post_termination(clause_text: str) -> tuple[RiskLevel, str]:
        """
        Evaluate post-termination services clause for exit obligations
        
        HIGH RISK:
        - Extensive post-termination obligations
        - No time limits
        - Unclear deliverables
        
        MEDIUM RISK:
        - Reasonable transition period
        - Clear scope and timeline
        
        LOW RISK:
        - No post-termination obligations
        - Minimal transition support
        """
        if not clause_text:
            return RiskLevel.LOW, "No post-termination obligations"
        
        text_lower = clause_text.lower()
        
        # HIGH RISK indicators
        high_risk_patterns = [
            "indefinite",
            "as long as",
            "until",
            "continue to provide",
            "ongoing obligation"
        ]
        
        for pattern in high_risk_patterns:
            if pattern in text_lower and not any(term in text_lower for term in ["30 day", "60 day", "90 day"]):
                return RiskLevel.HIGH, f"Open-ended post-termination obligations: '{pattern}'"
        
        # MEDIUM RISK indicators
        medium_risk_patterns = [
            "transition",
            "wind down",
            "90 day",
            "three month",
            "180 day"
        ]
        
        for pattern in medium_risk_patterns:
            if pattern in text_lower:
                return RiskLevel.MEDIUM, "Post-termination transition period required"
        
        # LOW RISK indicators
        low_risk_patterns = [
            "30 day",
            "minimal",
            "reasonable assistance",
            "at prevailing rates"
        ]
        
        for pattern in low_risk_patterns:
            if pattern in text_lower:
                return RiskLevel.LOW, "Limited post-termination obligations"
        
        return RiskLevel.MEDIUM, "Post-termination services clause present"


# ============================================================================
# CLAUSE IMPORTANCE WEIGHTS
# ============================================================================

CLAUSE_IMPORTANCE = {
    ClauseType.GOVERNING_LAW: "HIGH",          # Critical for dispute resolution
    ClauseType.LIABILITY: "HIGH",              # Financial risk protection
    ClauseType.CONFIDENTIALITY: "HIGH",        # IP and trade secret protection
    ClauseType.TERMINATION: "HIGH",            # Exit strategy
    ClauseType.INDEMNIFICATION: "MEDIUM",      # Risk allocation
    ClauseType.PAYMENT_TERMS: "MEDIUM",        # Financial clarity
    ClauseType.INTELLECTUAL_PROPERTY: "HIGH",  # IP ownership
    ClauseType.DATA_PROTECTION: "MEDIUM",      # Compliance requirement
    ClauseType.FORCE_MAJEURE: "LOW",           # Uncommon events
    # New clauses (v2.0)
    ClauseType.NON_COMPETE: "HIGH",            # Business flexibility
    ClauseType.EXCLUSIVITY: "HIGH",            # Revenue opportunity
    ClauseType.CHANGE_OF_CONTROL: "MEDIUM",    # M&A flexibility
    ClauseType.ANTI_ASSIGNMENT: "MEDIUM",      # Transfer rights
    ClauseType.AUDIT_RIGHTS: "MEDIUM",         # Operational access
    ClauseType.POST_TERMINATION_SERVICES: "MEDIUM",  # Exit obligations
}


# ============================================================================
# GAP DETECTION RULES
# ============================================================================

def get_critical_missing_clauses(analysis: ContractAnalysisSchema) -> List[str]:
    """
    Identify critical missing clauses based on CUAD best practices
    
    Returns list of missing critical clauses
    """
    missing = []
    
    critical_clauses = {
        "governing_law": "Critical: No governing law specified - disputes will be unclear",
        "liability": "Critical: No liability clause - unlimited exposure risk",
        "confidentiality": "Critical: No confidentiality clause - no IP protection",
        "termination": "Critical: No termination clause - unclear exit process",
        "non_compete": "Critical: No non-compete clause - post-relationship competition unclear",
        "exclusivity": "Critical: No exclusivity terms - business flexibility unclear",
    }
    
    for clause_name, description in critical_clauses.items():
        clause_obj = getattr(analysis, clause_name)
        if not clause_obj.present:
            missing.append(description)
    
    return missing


def get_recommended_missing_clauses(analysis: ContractAnalysisSchema) -> List[str]:
    """
    Identify recommended but non-critical missing clauses
    
    Returns list of recommended clauses to add
    """
    missing = []
    
    recommended_clauses = {
        "indemnification": "Recommended: Add indemnification clause for risk allocation",
        "intellectual_property": "Recommended: Add IP clause to protect ownership rights",
        "data_protection": "Recommended: Add data protection clause for compliance",
        "change_of_control": "Recommended: Add change of control provisions for M&A scenarios",
        "anti_assignment": "Recommended: Add assignment restrictions to control transfers",
        "audit_rights": "Recommended: Add audit rights for compliance verification",
        "post_termination_services": "Recommended: Add post-termination terms for smooth exit",
        "force_majeure": "Recommended: Add force majeure clause for unforeseen events",
        "payment_terms": "Recommended: Add clear payment terms to avoid disputes",
    }
    
    for clause_name, description in recommended_clauses.items():
        clause_obj = getattr(analysis, clause_name)
        if not clause_obj.present:
            missing.append(description)
    
    return missing
