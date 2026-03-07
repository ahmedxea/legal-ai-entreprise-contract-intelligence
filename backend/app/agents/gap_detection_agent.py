"""
Gap Detection Agent

Identifies missing clauses in contracts based on CUAD best practices
and industry standards for commercial contracts.

This agent:
1. Analyzes which critical clauses are present
2. Identifies missing clauses
3. Categorizes gaps by severity (critical vs recommended)
4. Provides actionable recommendations

Uses deterministic logic - no LLM hallucination risk.
"""

import logging
from typing import List, Dict, Any
from app.models.clause_schema import (
    ContractAnalysisSchema,
    ClauseType,
    CLAUSE_IMPORTANCE,
    get_critical_missing_clauses,
    get_recommended_missing_clauses
)

logger = logging.getLogger(__name__)


class GapDetectionAgent:
    """
    Detect missing clauses in contracts
    
    Based on CUAD dataset analysis showing 41 clause types
    commonly found in commercial contracts by legal experts.
    
    Focuses on 9 high-priority clauses for MVP.
    """
    
    def __init__(self):
        """Initialize the gap detection agent"""
        self.clause_definitions = self._load_clause_definitions()
    
    def _load_clause_definitions(self) -> Dict[str, Dict]:
        """
        Load clause definitions and importance levels
        
        Returns:
            Dictionary mapping clause types to their metadata
        """
        return {
            ClauseType.GOVERNING_LAW: {
                "name": "Governing Law",
                "importance": "CRITICAL",
                "description": "Specifies which jurisdiction's laws govern the contract",
                "why_needed": "Essential for dispute resolution and legal enforcement",
                "example": "This Agreement shall be governed by the laws of the State of Delaware"
            },
            ClauseType.LIABILITY: {
                "name": "Liability / Limitation of Liability",
                "importance": "CRITICAL",
                "description": "Defines liability limits and damage caps",
                "why_needed": "Protects from unlimited financial exposure",
                "example": "Total liability shall not exceed the fees paid in the 12 months preceding the claim"
            },
            ClauseType.CONFIDENTIALITY: {
                "name": "Confidentiality / Non-Disclosure",
                "importance": "CRITICAL",
                "description": "Protects confidential and proprietary information",
                "why_needed": "Prevents unauthorized disclosure of trade secrets and sensitive data",
                "example": "Recipient shall not disclose Confidential Information to third parties for 5 years"
            },
            ClauseType.TERMINATION: {
                "name": "Termination",
                "importance": "CRITICAL",
                "description": "Defines how and when the contract can be terminated",
                "why_needed": "Provides clear exit strategy and protects from endless commitment",
                "example": "Either party may terminate with 30 days written notice"
            },
            ClauseType.INDEMNIFICATION: {
                "name": "Indemnification",
                "importance": "HIGH",
                "description": "Allocates responsibility for third-party claims",
                "why_needed": "Protects from liability for other party's actions",
                "example": "Provider shall indemnify Customer from claims arising from Provider's negligence"
            },
            ClauseType.INTELLECTUAL_PROPERTY: {
                "name": "Intellectual Property Rights",
                "importance": "HIGH",
                "description": "Defines ownership of intellectual property",
                "why_needed": "Prevents disputes over IP ownership and usage rights",
                "example": "All IP developed under this Agreement shall belong to Customer"
            },
            ClauseType.PAYMENT_TERMS: {
                "name": "Payment Terms",
                "importance": "HIGH",
                "description": "Specifies payment amounts, schedule, and conditions",
                "why_needed": "Ensures clear financial obligations and prevents payment disputes",
                "example": "Customer shall pay $10,000 monthly within 30 days of invoice"
            },
            ClauseType.DATA_PROTECTION: {
                "name": "Data Protection / Privacy",
                "importance": "MEDIUM",
                "description": "Addresses data privacy and regulatory compliance",
                "why_needed": "Ensures compliance with GDPR, CCPA, and other regulations",
                "example": "Provider shall process personal data in compliance with GDPR"
            },
            ClauseType.FORCE_MAJEURE: {
                "name": "Force Majeure",
                "importance": "MEDIUM",
                "description": "Addresses performance during extraordinary events",
                "why_needed": "Protects from liability during unforeseeable circumstances",
                "example": "Neither party liable for delays due to acts of God, war, or pandemic"
            },
            ClauseType.NON_COMPETE: {
                "name": "Non-Compete",
                "importance": "MEDIUM",
                "description": "Restricts competing with counterparty",
                "why_needed": "Prevents conflicts of interest and protects business relationships",
                "example": "Provider shall not compete in same market for 2 years"
            },
            ClauseType.EXCLUSIVITY: {
                "name": "Exclusivity",
                "importance": "MEDIUM",
                "description": "Exclusive dealing or sole sourcing requirements",
                "why_needed": "Clarifies exclusive vs non-exclusive arrangements",
                "example": "Customer agrees to exclusively source products from Provider"
            },
            ClauseType.CHANGE_OF_CONTROL: {
                "name": "Change of Control",
                "importance": "MEDIUM",
                "description": "Rights and obligations upon M&A or ownership change",
                "why_needed": "Addresses implications of corporate restructuring",
                "example": "Agreement terminates upon change of control unless successor assumes obligations"
            },
            ClauseType.ANTI_ASSIGNMENT: {
                "name": "Anti-Assignment",
                "importance": "MEDIUM",
                "description": "Restrictions on assigning or transferring the contract",
                "why_needed": "Controls who can take over contract obligations",
                "example": "Neither party may assign without prior written consent"
            },
            ClauseType.AUDIT_RIGHTS: {
                "name": "Audit Rights",
                "importance": "LOW",
                "description": "Right to audit compliance or records",
                "why_needed": "Ensures transparency and compliance verification",
                "example": "Customer may audit Provider's records with 30 days notice"
            },
            ClauseType.POST_TERMINATION_SERVICES: {
                "name": "Post-Termination Services",
                "importance": "LOW",
                "description": "Obligations after contract ends",
                "why_needed": "Ensures smooth transition and data return",
                "example": "Provider shall assist with transition for 60 days post-termination"
            }
        }
    
    def detect_gaps(self, analysis: ContractAnalysisSchema) -> Dict[str, Any]:
        """
        Detect missing clauses in the contract
        
        Args:
            analysis: Contract analysis with clause detection results
            
        Returns:
            Dictionary containing gap analysis:
            - critical_gaps: Missing critical clauses
            - recommended_gaps: Missing recommended clauses
            - present_clauses: Clauses that exist
            - completeness_score: Percentage of clauses present
            - recommendations: Actionable recommendations
        """
        logger.info(f"Starting gap detection for contract {analysis.contract_id}")
        
        critical_gaps = []
        recommended_gaps = []
        present_clauses = []
        
        # Check each clause type
        for clause_type in ClauseType:
            clause_field = clause_type.value
            clause_obj = getattr(analysis, clause_field)
            clause_meta = self.clause_definitions[clause_type]
            
            if clause_obj.present:
                present_clauses.append(clause_meta["name"])
            else:
                gap_info = {
                    "clause_type": clause_meta["name"],
                    "importance": clause_meta["importance"],
                    "description": clause_meta["description"],
                    "why_needed": clause_meta["why_needed"],
                    "example": clause_meta["example"]
                }
                
                if clause_meta["importance"] in ["CRITICAL", "HIGH"]:
                    critical_gaps.append(gap_info)
                else:
                    recommended_gaps.append(gap_info)
        
        # Calculate completeness score
        total_clauses = len(ClauseType)
        present_count = len(present_clauses)
        completeness_score = (present_count / total_clauses) * 100
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            critical_gaps,
            recommended_gaps,
            completeness_score
        )
        
        gap_analysis = {
            "critical_gaps": critical_gaps,
            "recommended_gaps": recommended_gaps,
            "present_clauses": present_clauses,
            "completeness_score": round(completeness_score, 1),
            "recommendations": recommendations
        }
        
        logger.info(
            f"Gap detection completed: {present_count}/{total_clauses} clauses present "
            f"({completeness_score:.1f}%)"
        )
        
        return gap_analysis
    
    def _generate_recommendations(
        self,
        critical_gaps: List[Dict],
        recommended_gaps: List[Dict],
        completeness_score: float
    ) -> List[str]:
        """
        Generate actionable recommendations based on gaps
        
        Args:
            critical_gaps: List of critical missing clauses
            recommended_gaps: List of recommended missing clauses
            completeness_score: Percentage of clauses present
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Overall assessment
        if completeness_score < 50:
            recommendations.append(
                "⚠️ URGENT: Contract is significantly incomplete. "
                "Consider comprehensive legal review before signing."
            )
        elif completeness_score < 70:
            recommendations.append(
                "⚠️ Contract has notable gaps. Address critical missing clauses before execution."
            )
        elif completeness_score < 90:
            recommendations.append(
                "✓ Contract is reasonably complete but could be strengthened."
            )
        else:
            recommendations.append(
                "✓ Contract appears comprehensive with most standard clauses present."
            )
        
        # Critical gaps
        if len(critical_gaps) > 0:
            recommendations.append(
                f"\n🔴 CRITICAL: {len(critical_gaps)} essential clause(s) missing. "
                "These should be added before signing:"
            )
            for gap in critical_gaps[:3]:  # Top 3 critical gaps
                recommendations.append(
                    f"   • {gap['clause_type']}: {gap['why_needed']}"
                )
        
        # High-priority recommendations
        if len(recommended_gaps) > 0:
            recommendations.append(
                f"\n🟡 RECOMMENDED: Consider adding {len(recommended_gaps)} additional clause(s) "
                "to strengthen the contract:"
            )
            for gap in recommended_gaps[:2]:  # Top 2 recommended gaps
                recommendations.append(
                    f"   • {gap['clause_type']}: {gap['description']}"
                )
        
        # Action items
        recommendations.append("\n📋 Next Steps:")
        if len(critical_gaps) > 0:
            recommendations.append("   1. Request amendments to add critical missing clauses")
            recommendations.append("   2. Have legal counsel review the contract")
        else:
            recommendations.append("   1. Review medium-priority gaps with legal team")
        
        recommendations.append("   2. Verify all present clauses align with business requirements")
        recommendations.append("   3. Negotiate any unfavorable terms identified in risk analysis")
        
        return recommendations
    
    def generate_gap_report(self, analysis: ContractAnalysisSchema) -> Dict:
        """
        Generate comprehensive gap analysis report
        
        Args:
            analysis: Contract analysis with clause detection
            
        Returns:
            Complete gap report with categorized findings
        """
        gap_analysis = self.detect_gaps(analysis)
        
        # Add summary statistics
        gap_analysis["summary"] = {
            "total_clauses_evaluated": len(ClauseType),
            "clauses_present": len(gap_analysis["present_clauses"]),
            "clauses_missing": len(gap_analysis["critical_gaps"]) + len(gap_analysis["recommended_gaps"]),
            "critical_gaps_count": len(gap_analysis["critical_gaps"]),
            "recommended_gaps_count": len(gap_analysis["recommended_gaps"]),
            "completeness_score": gap_analysis["completeness_score"],
            "assessment": self._get_assessment(gap_analysis["completeness_score"])
        }
        
        return gap_analysis
    
    def _get_assessment(self, completeness_score: float) -> str:
        """
        Get qualitative assessment based on completeness score
        
        Args:
            completeness_score: Percentage of clauses present
            
        Returns:
            Assessment string
        """
        if completeness_score >= 90:
            return "EXCELLENT - Comprehensive contract"
        elif completeness_score >= 75:
            return "GOOD - Reasonably complete contract"
        elif completeness_score >= 60:
            return "FAIR - Several important clauses missing"
        elif completeness_score >= 40:
            return "POOR - Significantly incomplete contract"
        else:
            return "CRITICAL - Major gaps in contract structure"


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def detect_contract_gaps(analysis: ContractAnalysisSchema) -> Dict:
    """
    Detect gaps in a contract
    
    Convenience function for gap detection
    
    Args:
        analysis: Contract analysis
        
    Returns:
        Gap analysis report
    """
    agent = GapDetectionAgent()
    return agent.generate_gap_report(analysis)
