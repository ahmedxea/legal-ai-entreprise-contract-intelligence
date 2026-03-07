"""
Risk Evaluation Engine

Deterministic rule-based risk evaluation for contract clauses.
Uses CUAD-derived rules to assess risk levels in a transparent, explainable manner.

This engine:
1. Applies structured risk rules to extracted clauses
2. Evaluates each clause independently
3. Generates an overall risk assessment
4. Provides clear explanations for risk ratings

NO LLM HALLUCINATIONS - purely rule-based evaluation.
"""

import logging
from typing import Dict, List, Tuple, Optional
from app.models.clause_schema import (
    ContractAnalysisSchema,
    ClauseAnalysis,
    RiskLevel,
    RiskSummary,
    RiskRule,
    ClauseType,
    CLAUSE_IMPORTANCE,
    get_critical_missing_clauses,
    get_recommended_missing_clauses
)

logger = logging.getLogger(__name__)


class RiskEvaluationEngine:
    """
    Deterministic risk evaluation engine
    
    Applies rule-based risk analysis to contract clauses
    following CUAD methodology and legal best practices.
    """
    
    def __init__(self):
        """Initialize the risk evaluation engine"""
        self.rule_engine = RiskRule()
    
    def evaluate_contract_risk(self, analysis: ContractAnalysisSchema) -> ContractAnalysisSchema:
        """
        Evaluate risk for all clauses in the contract
        
        Args:
            analysis: Contract analysis with extracted clauses
            
        Returns:
            Updated analysis with risk levels assigned
        """
        logger.info(f"Starting risk evaluation for contract {analysis.contract_id}")
        
        # Evaluate each clause type
        analysis.liability = self._evaluate_clause(
            analysis.liability,
            ClauseType.LIABILITY,
            self.rule_engine.evaluate_liability_clause
        )
        
        analysis.confidentiality = self._evaluate_clause(
            analysis.confidentiality,
            ClauseType.CONFIDENTIALITY,
            self.rule_engine.evaluate_confidentiality_clause
        )
        
        analysis.termination = self._evaluate_clause(
            analysis.termination,
            ClauseType.TERMINATION,
            self.rule_engine.evaluate_termination_clause
        )
        
        analysis.payment_terms = self._evaluate_clause(
            analysis.payment_terms,
            ClauseType.PAYMENT_TERMS,
            self.rule_engine.evaluate_payment_terms
        )
        
        analysis.intellectual_property = self._evaluate_clause(
            analysis.intellectual_property,
            ClauseType.INTELLECTUAL_PROPERTY,
            self.rule_engine.evaluate_ip_clause
        )
        
        analysis.data_protection = self._evaluate_clause(
            analysis.data_protection,
            ClauseType.DATA_PROTECTION,
            self.rule_engine.evaluate_data_protection
        )
        
        # Governing Law: dedicated evaluation
        analysis.governing_law = self._evaluate_clause(
            analysis.governing_law,
            ClauseType.GOVERNING_LAW,
            self.rule_engine.evaluate_governing_law
        )
        
        analysis.indemnification = self._evaluate_generic_clause(
            analysis.indemnification,
            ClauseType.INDEMNIFICATION,
            importance="MEDIUM"
        )
        
        analysis.force_majeure = self._evaluate_generic_clause(
            analysis.force_majeure,
            ClauseType.FORCE_MAJEURE,
            importance="LOW"
        )
        
        # Evaluate NEW clause types (v2.0)
        analysis.non_compete = self._evaluate_clause(
            analysis.non_compete,
            ClauseType.NON_COMPETE,
            self.rule_engine.evaluate_non_compete
        )
        
        analysis.exclusivity = self._evaluate_clause(
            analysis.exclusivity,
            ClauseType.EXCLUSIVITY,
            self.rule_engine.evaluate_exclusivity
        )
        
        analysis.change_of_control = self._evaluate_clause(
            analysis.change_of_control,
            ClauseType.CHANGE_OF_CONTROL,
            self.rule_engine.evaluate_change_of_control
        )
        
        analysis.anti_assignment = self._evaluate_clause(
            analysis.anti_assignment,
            ClauseType.ANTI_ASSIGNMENT,
            self.rule_engine.evaluate_anti_assignment
        )
        
        analysis.audit_rights = self._evaluate_clause(
            analysis.audit_rights,
            ClauseType.AUDIT_RIGHTS,
            self.rule_engine.evaluate_audit_rights
        )
        
        analysis.post_termination_services = self._evaluate_clause(
            analysis.post_termination_services,
            ClauseType.POST_TERMINATION_SERVICES,
            self.rule_engine.evaluate_post_termination
        )
        
        logger.info(f"Risk evaluation completed for contract {analysis.contract_id}")
        return analysis
    
    def _evaluate_clause(
        self,
        clause: ClauseAnalysis,
        clause_type: ClauseType,
        evaluation_func
    ) -> ClauseAnalysis:
        """
        Apply specific evaluation rule to a clause
        
        Args:
            clause: Clause analysis object
            clause_type: Type of clause
            evaluation_func: Function to evaluate risk
            
        Returns:
            Updated clause with risk assessment
        """
        if clause.present and clause.text:
            risk_level, reason = evaluation_func(clause.text)
            clause.risk_level = risk_level
            clause.risk_reason = reason
        else:
            # Missing clause risk based on importance
            importance = CLAUSE_IMPORTANCE.get(clause_type, "MEDIUM")
            if importance == "HIGH":
                clause.risk_level = RiskLevel.HIGH
                clause.risk_reason = f"Critical clause missing: {clause_type.value}"
            elif importance == "MEDIUM":
                clause.risk_level = RiskLevel.MEDIUM
                clause.risk_reason = f"Important clause missing: {clause_type.value}"
            else:
                clause.risk_level = RiskLevel.LOW
                clause.risk_reason = f"Optional clause missing: {clause_type.value}"
        
        return clause
    
    def _evaluate_generic_clause(
        self,
        clause: ClauseAnalysis,
        clause_type: ClauseType,
        importance: str
    ) -> ClauseAnalysis:
        """
        Apply generic evaluation for clauses without specific rules
        
        Args:
            clause: Clause analysis object
            clause_type: Type of clause
            importance: HIGH | MEDIUM | LOW
            
        Returns:
            Updated clause with risk assessment
        """
        if clause.present and clause.text:
            # Clause exists - generally low risk if present
            clause.risk_level = RiskLevel.LOW
            clause.risk_reason = f"{clause_type.value.replace('_', ' ').title()} clause present"
        else:
            # Missing clause - risk based on importance
            if importance == "HIGH":
                clause.risk_level = RiskLevel.HIGH
                clause.risk_reason = f"Critical clause missing: {clause_type.value}"
            elif importance == "MEDIUM":
                clause.risk_level = RiskLevel.MEDIUM
                clause.risk_reason = f"Important clause missing: {clause_type.value}"
            else:
                clause.risk_level = RiskLevel.LOW
                clause.risk_reason = f"Optional clause missing: {clause_type.value}"
        
        return clause
    
    def generate_risk_summary(
        self, 
        analysis: ContractAnalysisSchema, 
        extracted_data: Optional[Dict] = None
    ) -> RiskSummary:
        """
        Generate overall risk summary for the contract
        
        Aggregates clause-level risks into contract-level assessment
        
        Args:
            analysis: Complete contract analysis with risk evaluations
            extracted_data: Optional extracted metadata and entities for enhanced risk flags
            
        Returns:
            RiskSummary with overall risk, key findings, and risk flags
        """
        logger.info(f"Generating risk summary for contract {analysis.contract_id}")
        
        # Collect risk items by severity
        high_risk_items = []
        medium_risk_items = []
        missing_clauses = []
        key_findings = []
        
        # Analyze each clause
        clause_fields = [
            ("governing_law", "Governing Law"),
            ("confidentiality", "Confidentiality"),
            ("termination", "Termination"),
            ("liability", "Liability"),
            ("indemnification", "Indemnification"),
            ("payment_terms", "Payment Terms"),
            ("intellectual_property", "Intellectual Property"),
            ("data_protection", "Data Protection"),
            ("force_majeure", "Force Majeure"),
        ]
        
        for field_name, display_name in clause_fields:
            clause = getattr(analysis, field_name)
            
            if not clause.present:
                missing_clauses.append(display_name)
            
            if clause.risk_level == RiskLevel.HIGH:
                high_risk_items.append({
                    "clause": display_name,
                    "reason": clause.risk_reason or "High risk identified"
                })
            elif clause.risk_level == RiskLevel.MEDIUM:
                medium_risk_items.append({
                    "clause": display_name,
                    "reason": clause.risk_reason or "Medium risk identified"
                })
        
        # Determine overall risk level
        overall_risk = self._calculate_overall_risk(
            len(high_risk_items),
            len(medium_risk_items),
            len(missing_clauses)
        )
        
        # Generate key findings
        key_findings = self._generate_key_findings(
            analysis,
            high_risk_items,
            medium_risk_items,
            missing_clauses
        )
        
        # Identify compliance gaps
        compliance_gaps = get_critical_missing_clauses(analysis)
        
        # Generate risk flags (production-ready indicators)
        risk_flags = []
        if extracted_data:
            risk_flags = self.generate_risk_flags(analysis, extracted_data)
        
        summary = RiskSummary(
            overall_risk=overall_risk,
            high_risk_items=high_risk_items,
            medium_risk_items=medium_risk_items,
            missing_clauses=missing_clauses,
            key_findings=key_findings,
            compliance_gaps=compliance_gaps,
            risk_flags=risk_flags
        )
        
        logger.info(f"Risk summary generated: Overall risk = {overall_risk}, {len(risk_flags)} risk flags")
        return summary
    
    def generate_risk_flags(self, analysis: ContractAnalysisSchema, extracted_data: Dict) -> List[str]:
        """
        Generate specific risk flags for enterprise contract intelligence
        
        Production-ready risk indicators used in major contract AI systems:
        - Unlimited liability
        - Missing termination clause
        - Unclear payment terms
        - No governing law
        - Automatic renewal
        - Missing confidentiality
        - Ambiguous IP ownership
        - No data protection
        - One-sided obligations
        - Missing audit rights
        
        Args:
            analysis: Complete contract analysis
            extracted_data: Extracted metadata and entities
            
        Returns:
            List of risk flag messages
        """
        risk_flags = []
        
        # 1. Unlimited liability detection
        if analysis.liability.present and analysis.liability.risk_level == RiskLevel.HIGH:
            if analysis.liability.risk_reason and "unlimited" in analysis.liability.risk_reason.lower():
                risk_flags.append("⚠️ Unlimited liability clause detected")
        elif not analysis.liability.present:
            risk_flags.append("⚠️ Missing limitation of liability clause")
        
        # 2. Termination clause issues
        if not analysis.termination.present:
            risk_flags.append("⚠️ Missing termination clause - no exit strategy defined")
        elif analysis.termination.risk_level == RiskLevel.HIGH:
            risk_flags.append("⚠️ Problematic termination terms detected")
        
        # 3. Payment terms clarity
        if not analysis.payment_terms.present:
            risk_flags.append("⚠️ Unclear or missing payment terms")
        elif analysis.payment_terms.risk_level == RiskLevel.HIGH:
            risk_flags.append("⚠️ High-risk payment terms identified")
        
        # 4. Governing law / jurisdiction
        if not analysis.governing_law.present:
            risk_flags.append("⚠️ No governing law specified - legal jurisdiction unclear")
        else:
            jurisdiction_conf = extracted_data.get("jurisdiction_confidence", 0)
            if not extracted_data.get("governing_law"):
                risk_flags.append("⚠️ Governing law clause present but jurisdiction not identified")
            elif jurisdiction_conf < 0.6:
                risk_flags.append("⚠️ Governing law jurisdiction detected with low confidence - manual review recommended")
        
        # 5. Automatic renewal risks
        if analysis.termination.present and analysis.termination.text:
            text_lower = analysis.termination.text.lower()
            if "automatic renewal" in text_lower or "auto-renew" in text_lower:
                if "notice" not in text_lower:
                    risk_flags.append("⚠️ Automatic renewal without clear notice requirements")
        
        # 6. Confidentiality issues
        if not analysis.confidentiality.present:
            risk_flags.append("⚠️ Missing confidentiality clause - sensitive data unprotected")
        elif analysis.confidentiality.risk_level == RiskLevel.HIGH:
            risk_flags.append("⚠️ Weak confidentiality protections")
        
        # 7. Intellectual property ambiguity
        if not analysis.intellectual_property.present:
            risk_flags.append("⚠️ No IP ownership clause - ownership rights unclear")
        elif analysis.intellectual_property.risk_level == RiskLevel.HIGH:
            risk_flags.append("⚠️ Problematic IP ownership terms")
        
        # 8. Data protection compliance
        if not analysis.data_protection.present:
            risk_flags.append("⚠️ Missing data protection clause - GDPR/privacy compliance risk")
        
        # 9. One-sided obligations (check parties balance)
        if extracted_data.get("obligations"):
            obligations = extracted_data["obligations"]
            if len(obligations) > 0:
                parties = set()
                for obl in obligations:
                    if isinstance(obl, dict) and obl.get("party"):
                        parties.add(obl["party"].lower())
                if len(parties) == 1:
                    risk_flags.append("⚠️ One-sided contract - obligations only on one party")
        
        # 10. Exclusivity without performance requirements
        if analysis.exclusivity.present and analysis.exclusivity.risk_level == RiskLevel.HIGH:
            risk_flags.append("⚠️ Exclusive arrangement without performance guarantees")
        
        # 11. Non-compete overly broad
        if analysis.non_compete.present and analysis.non_compete.risk_level == RiskLevel.HIGH:
            risk_flags.append("⚠️ Overly broad non-compete restrictions")
        
        # 12. Change of control issues
        if analysis.change_of_control.present and analysis.change_of_control.risk_level == RiskLevel.HIGH:
            risk_flags.append("⚠️ Automatic termination on change of control - M&A risk")
        
        # 13. Assignment restrictions
        if analysis.anti_assignment.present and analysis.anti_assignment.risk_level == RiskLevel.HIGH:
            risk_flags.append("⚠️ Strict assignment restrictions - may block business transfers")
        
        # 14. Missing critical dates
        if not extracted_data.get("effective_date") and not extracted_data.get("execution_date"):
            risk_flags.append("⚠️ No effective date specified - contract start unclear")
        
        if not extracted_data.get("expiration_date"):
            risk_flags.append("⚠️ No expiration date - perpetual obligation risk")
        
        # 15. Missing contract value (for commercial contracts)
        contract_type = extracted_data.get("contract_type", "").lower()
        commercial_types = ["saas", "service", "license", "procurement", "purchase"]
        if any(ct in contract_type for ct in commercial_types):
            if not extracted_data.get("contract_value") and not extracted_data.get("financial_terms"):
                risk_flags.append("⚠️ Commercial contract with unclear financial terms")
        
        logger.info(f"Generated {len(risk_flags)} risk flags")
        return risk_flags
    
    def _calculate_overall_risk(
        self,
        high_count: int,
        medium_count: int,
        missing_count: int
    ) -> RiskLevel:
        """
        Calculate overall contract risk based on clause-level risks
        
        Logic:
        - 3+ high risks OR 5+ missing critical clauses -> HIGH
        - 1-2 high risks OR 3-4 missing clauses OR 5+ medium risks -> MEDIUM
        - Otherwise -> LOW
        """
        if high_count >= 3 or missing_count >= 5:
            return RiskLevel.HIGH
        elif high_count >= 1 or missing_count >= 3 or medium_count >= 5:
            return RiskLevel.MEDIUM
        elif medium_count >= 2:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _generate_key_findings(
        self,
        analysis: ContractAnalysisSchema,
        high_risk_items: List[Dict],
        medium_risk_items: List[Dict],
        missing_clauses: List[str]
    ) -> List[str]:
        """
        Generate human-readable key findings
        
        Returns:
            List of key findings for the contract
        """
        findings = []
        
        # Critical findings
        if len(high_risk_items) > 0:
            findings.append(f"⚠️ {len(high_risk_items)} high-risk clause(s) identified requiring immediate attention")
        
        if len(missing_clauses) >= 4:
            findings.append(f"⚠️ {len(missing_clauses)} clauses missing - contract may be incomplete")
        
        # Specific high-priority findings
        if not analysis.governing_law.present:
            findings.append("❌ No governing law specified - dispute resolution will be unclear")
        
        if not analysis.liability.present:
            findings.append("❌ No liability clause - unlimited liability exposure")
        elif analysis.liability.risk_level == RiskLevel.HIGH:
            findings.append(f"❌ Liability clause contains high-risk terms: {analysis.liability.risk_reason}")
        
        if not analysis.confidentiality.present:
            findings.append("❌ No confidentiality clause - intellectual property at risk")
        
        if not analysis.termination.present:
            findings.append("⚠️ No termination clause - unclear exit process")
        
        # Positive findings
        if analysis.confidentiality.present and analysis.confidentiality.risk_level == RiskLevel.LOW:
            findings.append("✅ Strong confidentiality protection in place")
        
        if analysis.liability.present and analysis.liability.risk_level == RiskLevel.LOW:
            findings.append("✅ Liability clause includes appropriate protections")
        
        # General assessment
        if len(findings) == 0:
            findings.append("✅ No critical issues identified - contract appears well-structured")
        
        return findings


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def evaluate_contract_risk(analysis: ContractAnalysisSchema) -> tuple[ContractAnalysisSchema, RiskSummary]:
    """
    Evaluate contract risk and generate summary
    
    Convenience function that performs both risk evaluation and summary generation
    
    Args:
        analysis: Contract analysis with extracted clauses
        
    Returns:
        Tuple of (updated analysis, risk summary)
    """
    engine = RiskEvaluationEngine()
    
    # Apply risk evaluation rules
    analysis = engine.evaluate_contract_risk(analysis)
    
    # Generate risk summary
    summary = engine.generate_risk_summary(analysis)
    
    return analysis, summary
