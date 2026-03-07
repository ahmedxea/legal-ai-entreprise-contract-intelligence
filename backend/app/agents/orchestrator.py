"""
Contract Orchestrator - Coordinates all agents for complete analysis
"""
import logging
from typing import Dict, Any
import asyncio

from app.agents.document_parser import DocumentParserAgent
from app.agents.extraction_agent import ExtractionAgent
from app.agents.risk_agent import RiskAnalysisAgent
from app.agents.legal_advisory_agent import LegalAdvisoryAgent
from app.agents.compliance_agent import ComplianceAgent
from app.models.schemas import Language
from app.services.sqlite_service import DatabaseService

logger = logging.getLogger(__name__)


class ContractOrchestrator:
    """Orchestrates the multi-agent pipeline for contract analysis"""
    
    def __init__(self):
        self.parser_agent = DocumentParserAgent()
        self.extraction_agent = ExtractionAgent()
        self.risk_agent = RiskAnalysisAgent()
        self.legal_agent = LegalAdvisoryAgent()
        self.compliance_agent = ComplianceAgent()
        self._db = DatabaseService()
    
    async def analyze_contract(
        self,
        contract_id: str,
        blob_url: str,
        language: Language,
        industry: str = None
    ) -> Dict[str, Any]:
        """
        Run complete contract analysis pipeline
        
        Args:
            contract_id: Contract identifier
            blob_url: Blob storage URL
            language: Contract language
            industry: Industry sector
            
        Returns:
            Complete analysis results
        """
        logger.info(f"Starting orchestrated analysis for contract: {contract_id}")
        
        try:
            # Step 1: Parse document — or use cached text if extraction already ran
            logger.info("Step 1/5: Resolving document text...")
            cached = await self._db.get_document_text(contract_id)
            if cached is not None:
                contract_text = cached["raw_text"]
                logger.info(
                    f"Using cached extracted text for {contract_id} "
                    f"({len(contract_text)} chars)"
                )
            else:
                logger.info("No cached text found; parsing document from storage...")
                parsed_doc = await self.parser_agent.parse_document(blob_url)
                contract_text = parsed_doc["full_text"]
            
            # Step 2: Extract structured data
            logger.info("Step 2/5: Extracting structured data...")
            extracted_data = await self.extraction_agent.extract_data(
                contract_text=contract_text,
                language=language
            )
            
            # Determine governing law from extracted data
            governing_law = extracted_data.get("governing_law")
            
            # Steps 3-5: Run analysis agents in parallel for efficiency
            logger.info("Steps 3-5: Running parallel analysis (Risk, Legal, Compliance)...")
            
            risk_task = self.risk_agent.analyze_risks(
                contract_text=contract_text,
                extracted_data=extracted_data,
                language=language,
                industry=industry
            )
            
            legal_task = self.legal_agent.provide_legal_opinion(
                contract_text=contract_text,
                extracted_data=extracted_data,
                language=language,
                governing_law=governing_law
            )
            
            compliance_task = self.compliance_agent.check_compliance(
                contract_text=contract_text,
                extracted_data=extracted_data,
                language=language,
                industry=industry
            )
            
            # Wait for all analyses to complete
            risk_analysis, legal_opinion, compliance_check = await asyncio.gather(
                risk_task,
                legal_task,
                compliance_task
            )
            
            # Step 6: Generate summary
            logger.info("Step 6/6: Generating summary...")
            summary = await self._generate_summary(
                extracted_data=extracted_data,
                risk_analysis=risk_analysis,
                legal_opinion=legal_opinion,
                compliance_check=compliance_check
            )
            
            # Compile complete analysis
            result = {
                "extracted_data": extracted_data,
                "analysis": {
                    "summary": summary,
                    "risks": risk_analysis.get("risks", []),
                    "legal_opinions": legal_opinion.get("legal_opinions", []),
                    "compliance": compliance_check.get("compliance_items", []),
                    "overall_risk_score": risk_analysis.get("overall_risk_score", 0),
                    "compliance_score": compliance_check.get("compliance_score", 0),
                    "regulatory_compliance": legal_opinion.get("regulatory_compliance", {}),
                    "recommendations": self._consolidate_recommendations(
                        risk_analysis, legal_opinion, compliance_check
                    )
                },
                "metadata": {
                    "page_count": parsed_doc.get("page_count"),
                    "file_type": parsed_doc.get("file_type"),
                    "language": language.value,
                    "industry": industry
                }
            }
            
            logger.info(f"Analysis complete for contract: {contract_id}")
            logger.info(f"Results: Risk Score={result['analysis']['overall_risk_score']}, "
                       f"Compliance={result['analysis']['compliance_score']}, "
                       f"Risks={len(result['analysis']['risks'])}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in orchestrated analysis: {e}", exc_info=True)
            raise
    
    async def _generate_summary(
        self,
        extracted_data: Dict,
        risk_analysis: Dict,
        legal_opinion: Dict,
        compliance_check: Dict
    ) -> str:
        """Generate executive summary of the contract"""
        
        # Extract parties with safe handling
        parties_list = extracted_data.get('parties', [])
        if parties_list:
            if isinstance(parties_list[0], dict):
                parties = ', '.join([p.get('name', p.get('party', 'Unknown')) for p in parties_list])
            else:
                parties = ', '.join([str(p) for p in parties_list])
        else:
            parties = 'Not specified'
            
        contract_type = extracted_data.get('contract_type', 'Contract')
        value = extracted_data.get('contract_value') or 'Unspecified'
        
        risk_count = len(risk_analysis.get('risks', []))
        high_risks = sum(1 for r in risk_analysis.get('risks', []) if r.get('severity') in ['high', 'critical'])
        
        missing_clauses = len([
            c for c in compliance_check.get('compliance_items', [])
            if c.get('status') == 'missing'
        ])
        
        summary = f"""**Executive Summary**

**Contract Overview:**
- Type: {contract_type}
- Parties: {parties}
- Value: {value}
- Governing Law: {extracted_data.get('governing_law', 'Not specified')}

**Analysis Results:**
- Overall Risk Score: {risk_analysis.get('overall_risk_score', 0)}/10
- Compliance Score: {compliance_check.get('compliance_score', 0)}/100
- Total Risks Identified: {risk_count} ({high_risks} high/critical)
- Missing Standard Clauses: {missing_clauses}

**Key Findings:**
"""
        
        # Add top risks
        if high_risks > 0:
            summary += "\n**Critical Risks:**\n"
            for risk in risk_analysis.get('risks', [])[:3]:
                if risk.get('severity') in ['high', 'critical']:
                    summary += f"- {risk.get('description', '')}\n"
        
        # Add critical missing clauses
        critical_missing = compliance_check.get('critical_missing', [])
        if critical_missing:
            # Handle both string lists and dict lists
            if isinstance(critical_missing[0], dict):
                clause_names = [c.get('clause', c.get('name', str(c))) for c in critical_missing]
            else:
                clause_names = critical_missing
            summary += f"\n**Missing Critical Clauses:** {', '.join(clause_names)}\n"
        
        return summary
    
    def _consolidate_recommendations(
        self,
        risk_analysis: Dict,
        legal_opinion: Dict,
        compliance_check: Dict
    ) -> list:
        """Consolidate recommendations from all agents"""
        recommendations = []
        
        # From risk analysis
        for risk in risk_analysis.get('risks', []):
            if risk.get('recommendation') and risk.get('severity') in ['high', 'critical']:
                recommendations.append({
                    "source": "risk_analysis",
                    "priority": "high",
                    "recommendation": risk['recommendation']
                })
        
        # From legal opinion
        for rec in legal_opinion.get('recommendations', [])[:5]:
            recommendations.append({
                "source": "legal_advisory",
                "priority": "medium",
                "recommendation": rec
            })
        
        # From compliance
        for rec in compliance_check.get('recommendations', [])[:5]:
            recommendations.append({
                "source": "compliance",
                "priority": "medium",
                "recommendation": rec
            })
        
        return recommendations[:10]  # Limit to top 10
