"""
AI Clause Generator Service

Generates legally relevant contract clauses based on:
- Detected risks or missing clauses
- Selected jurisdiction
- CUAD dataset clause patterns

Uses CUAD templates as guidance for LLM-based clause generation.
"""
import logging
from typing import Dict, Any, Optional
from app.services.ollama_service import ollama_service
from app.models.clause_schema import ClauseType

logger = logging.getLogger(__name__)


# ============================================================================
# CUAD-based clause templates with placeholders
# Each template is aligned with a ClauseType and structured for adaptation
# ============================================================================

CUAD_CLAUSE_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "governing_law": {
        "title": "Governing Law",
        "clause_type": ClauseType.GOVERNING_LAW,
        "template": (
            "GOVERNING LAW AND JURISDICTION\n\n"
            "This Agreement and any dispute or claim arising out of or in connection with it "
            "or its subject matter or formation (including non-contractual disputes or claims) "
            "shall be governed by and construed in accordance with the laws of [JURISDICTION].\n\n"
            "The parties irrevocably agree that the courts of [JURISDICTION] shall have "
            "exclusive jurisdiction to settle any dispute or claim arising out of or in "
            "connection with this Agreement."
        ),
        "placeholders": ["JURISDICTION"],
        "cuad_category": "Governing Law",
        "guidance": "Specifies which jurisdiction's laws govern the contract and where disputes are resolved.",
    },
    "confidentiality": {
        "title": "Confidentiality and Non-Disclosure",
        "clause_type": ClauseType.CONFIDENTIALITY,
        "template": (
            "CONFIDENTIALITY\n\n"
            "1. Each party (the \"Receiving Party\") agrees to keep confidential all Confidential "
            "Information disclosed by the other party (the \"Disclosing Party\") and shall not "
            "disclose such information to any third party without prior written consent.\n\n"
            "2. \"Confidential Information\" means all non-public information disclosed by either "
            "party, whether orally, in writing, or by inspection, that is designated as confidential "
            "or that reasonably should be understood to be confidential.\n\n"
            "3. Exceptions: The obligations above shall not apply to information that: "
            "(a) is or becomes publicly available through no fault of the Receiving Party; "
            "(b) was known to the Receiving Party prior to disclosure; "
            "(c) is independently developed by the Receiving Party; or "
            "(d) is required to be disclosed by law or court order.\n\n"
            "4. This obligation shall survive for a period of [DURATION] years after termination "
            "of this Agreement.\n\n"
            "5. Upon termination, the Receiving Party shall return or destroy all Confidential "
            "Information and certify in writing that it has done so."
        ),
        "placeholders": ["DURATION"],
        "cuad_category": "Confidentiality/Non-Disclosure",
        "guidance": "Protects proprietary and sensitive information exchanged between parties.",
    },
    "termination": {
        "title": "Termination",
        "clause_type": ClauseType.TERMINATION,
        "template": (
            "TERMINATION\n\n"
            "1. Termination for Convenience: Either party may terminate this Agreement upon "
            "[NOTICE_PERIOD] days' prior written notice to the other party.\n\n"
            "2. Termination for Cause: Either party may terminate this Agreement immediately "
            "upon written notice if the other party:\n"
            "   (a) materially breaches this Agreement and fails to cure such breach within "
            "[CURE_PERIOD] days of receiving written notice of the breach;\n"
            "   (b) becomes insolvent, files for bankruptcy, or has a receiver appointed for "
            "its assets.\n\n"
            "3. Effect of Termination: Upon termination:\n"
            "   (a) all outstanding payment obligations shall become immediately due;\n"
            "   (b) each party shall return the other party's Confidential Information;\n"
            "   (c) any licenses granted hereunder shall terminate;\n"
            "   (d) the provisions of Sections [SURVIVING_SECTIONS] shall survive termination."
        ),
        "placeholders": ["NOTICE_PERIOD", "CURE_PERIOD", "SURVIVING_SECTIONS"],
        "cuad_category": "Termination",
        "guidance": "Defines how and when the contract can be terminated by either party.",
    },
    "liability": {
        "title": "Limitation of Liability",
        "clause_type": ClauseType.LIABILITY,
        "template": (
            "LIMITATION OF LIABILITY\n\n"
            "1. To the maximum extent permitted by applicable law, neither party shall be "
            "liable to the other for any indirect, incidental, special, consequential, or "
            "punitive damages, including but not limited to loss of profits, data, business "
            "opportunities, or goodwill, regardless of the cause of action or theory of liability.\n\n"
            "2. The total aggregate liability of either party under this Agreement shall not "
            "exceed [LIABILITY_CAP].\n\n"
            "3. The limitations set forth in this section shall not apply to:\n"
            "   (a) death or personal injury caused by negligence;\n"
            "   (b) fraud or fraudulent misrepresentation;\n"
            "   (c) willful misconduct;\n"
            "   (d) breach of confidentiality obligations;\n"
            "   (e) indemnification obligations under this Agreement."
        ),
        "placeholders": ["LIABILITY_CAP"],
        "cuad_category": "Liability/Limitation of Liability",
        "guidance": "Caps financial exposure and excludes certain types of damages.",
    },
    "indemnification": {
        "title": "Indemnification",
        "clause_type": ClauseType.INDEMNIFICATION,
        "template": (
            "INDEMNIFICATION\n\n"
            "1. [PARTY_A] shall indemnify, defend, and hold harmless [PARTY_B], its officers, "
            "directors, employees, and agents from and against any and all claims, damages, "
            "losses, liabilities, costs, and expenses (including reasonable attorneys' fees) "
            "arising out of or relating to:\n"
            "   (a) [PARTY_A]'s breach of this Agreement;\n"
            "   (b) [PARTY_A]'s negligence or willful misconduct;\n"
            "   (c) any third-party claim arising from [PARTY_A]'s performance under this Agreement.\n\n"
            "2. The indemnifying party's obligations are conditioned upon:\n"
            "   (a) prompt written notice of the claim;\n"
            "   (b) sole control of the defense and settlement;\n"
            "   (c) reasonable cooperation from the indemnified party.\n\n"
            "3. The indemnifying party shall not settle any claim that imposes obligations on "
            "the indemnified party without prior written consent."
        ),
        "placeholders": ["PARTY_A", "PARTY_B"],
        "cuad_category": "Indemnification",
        "guidance": "Allocates responsibility for third-party claims between the parties.",
    },
    "payment_terms": {
        "title": "Payment Terms",
        "clause_type": ClauseType.PAYMENT_TERMS,
        "template": (
            "PAYMENT TERMS\n\n"
            "1. Fees: [PARTY_B] shall pay [PARTY_A] the fees set forth in [SCHEDULE/EXHIBIT], "
            "totaling [CONTRACT_VALUE] ([CURRENCY]).\n\n"
            "2. Payment Schedule: Payments shall be made [PAYMENT_FREQUENCY] within "
            "[PAYMENT_DAYS] days of receipt of a valid invoice.\n\n"
            "3. Late Payment: Any payment not received by the due date shall bear interest at "
            "the rate of [INTEREST_RATE]% per annum, or the maximum rate permitted by law, "
            "whichever is lower.\n\n"
            "4. Taxes: All fees are exclusive of applicable taxes. [PARTY_B] shall be responsible "
            "for all taxes, duties, and levies arising from this Agreement, excluding taxes on "
            "[PARTY_A]'s income.\n\n"
            "5. Disputes: If [PARTY_B] disputes any invoice, it shall notify [PARTY_A] in writing "
            "within [DISPUTE_PERIOD] days of receipt and pay the undisputed portion by the due date."
        ),
        "placeholders": [
            "PARTY_A", "PARTY_B", "SCHEDULE/EXHIBIT", "CONTRACT_VALUE",
            "CURRENCY", "PAYMENT_FREQUENCY", "PAYMENT_DAYS", "INTEREST_RATE", "DISPUTE_PERIOD",
        ],
        "cuad_category": "Payment Terms",
        "guidance": "Defines financial obligations, payment schedule, and late payment consequences.",
    },
    "intellectual_property": {
        "title": "Intellectual Property Rights",
        "clause_type": ClauseType.INTELLECTUAL_PROPERTY,
        "template": (
            "INTELLECTUAL PROPERTY\n\n"
            "1. Pre-Existing IP: Each party retains all rights, title, and interest in its "
            "pre-existing intellectual property (\"Background IP\"). Nothing in this Agreement "
            "transfers ownership of Background IP.\n\n"
            "2. Developed IP: All intellectual property developed by [PARTY_A] specifically for "
            "[PARTY_B] under this Agreement (\"Foreground IP\") shall be owned by [IP_OWNER].\n\n"
            "3. License Grant: [LICENSOR] hereby grants [LICENSEE] a non-exclusive, royalty-free, "
            "perpetual license to use the Foreground IP solely for the purposes contemplated by "
            "this Agreement.\n\n"
            "4. No Infringement: Each party represents and warrants that its performance under "
            "this Agreement does not infringe any third party's intellectual property rights."
        ),
        "placeholders": ["PARTY_A", "PARTY_B", "IP_OWNER", "LICENSOR", "LICENSEE"],
        "cuad_category": "IP Ownership/Assignment",
        "guidance": "Establishes ownership of pre-existing and newly created intellectual property.",
    },
    "data_protection": {
        "title": "Data Protection and Privacy",
        "clause_type": ClauseType.DATA_PROTECTION,
        "template": (
            "DATA PROTECTION\n\n"
            "1. Compliance: Each party shall comply with all applicable data protection laws "
            "and regulations, including but not limited to [APPLICABLE_REGULATIONS].\n\n"
            "2. Data Processing: Where [PARTY_A] processes personal data on behalf of [PARTY_B], "
            "[PARTY_A] shall:\n"
            "   (a) process such data only in accordance with [PARTY_B]'s documented instructions;\n"
            "   (b) implement appropriate technical and organizational security measures;\n"
            "   (c) not transfer personal data outside [JURISDICTION] without prior written consent;\n"
            "   (d) promptly notify [PARTY_B] of any data breach.\n\n"
            "3. Data Subject Rights: [PARTY_A] shall assist [PARTY_B] in fulfilling its "
            "obligations to respond to data subject access requests.\n\n"
            "4. Sub-processors: [PARTY_A] shall not engage sub-processors without [PARTY_B]'s "
            "prior written consent.\n\n"
            "5. Data Retention: Upon termination, [PARTY_A] shall delete or return all personal "
            "data within [RETENTION_PERIOD] days, unless retention is required by law."
        ),
        "placeholders": [
            "APPLICABLE_REGULATIONS", "PARTY_A", "PARTY_B", "JURISDICTION", "RETENTION_PERIOD",
        ],
        "cuad_category": "Data Protection/Privacy",
        "guidance": "Ensures compliance with data protection laws and defines data handling obligations.",
    },
    "force_majeure": {
        "title": "Force Majeure",
        "clause_type": ClauseType.FORCE_MAJEURE,
        "template": (
            "FORCE MAJEURE\n\n"
            "1. Neither party shall be liable for any delay or failure to perform its obligations "
            "under this Agreement if such delay or failure results from a Force Majeure Event.\n\n"
            "2. \"Force Majeure Event\" means any event beyond the reasonable control of a party, "
            "including but not limited to: acts of God, natural disasters, epidemics, pandemics, "
            "war, terrorism, riot, embargo, acts of government, fire, flood, earthquake, labor "
            "disputes not involving employees of the affected party, or failure of public utilities.\n\n"
            "3. Notice: The affected party shall promptly notify the other party in writing of "
            "the Force Majeure Event and its expected duration.\n\n"
            "4. Mitigation: The affected party shall use reasonable efforts to mitigate the "
            "impact of the Force Majeure Event.\n\n"
            "5. Termination: If the Force Majeure Event continues for more than [FM_DURATION] "
            "consecutive days, either party may terminate this Agreement upon written notice."
        ),
        "placeholders": ["FM_DURATION"],
        "cuad_category": "Force Majeure",
        "guidance": "Addresses performance obligations during extraordinary, unforeseeable events.",
    },
    "non_compete": {
        "title": "Non-Compete",
        "clause_type": ClauseType.NON_COMPETE,
        "template": (
            "NON-COMPETE\n\n"
            "1. During the term of this Agreement and for a period of [NON_COMPETE_DURATION] "
            "following its termination, [RESTRICTED_PARTY] shall not, directly or indirectly, "
            "engage in, own, manage, operate, or participate in any business that competes with "
            "the business of [PROTECTED_PARTY] within [GEOGRAPHIC_SCOPE].\n\n"
            "2. This restriction shall not apply to:\n"
            "   (a) ownership of less than [OWNERSHIP_THRESHOLD]% of publicly traded securities;\n"
            "   (b) activities expressly authorized in writing by [PROTECTED_PARTY].\n\n"
            "3. The parties acknowledge that the scope and duration of this restriction are "
            "reasonable and necessary to protect [PROTECTED_PARTY]'s legitimate business interests.\n\n"
            "4. Remedies: Any breach of this provision shall entitle [PROTECTED_PARTY] to "
            "injunctive relief in addition to any other remedies available at law or in equity."
        ),
        "placeholders": [
            "NON_COMPETE_DURATION", "RESTRICTED_PARTY", "PROTECTED_PARTY",
            "GEOGRAPHIC_SCOPE", "OWNERSHIP_THRESHOLD",
        ],
        "cuad_category": "Non-Compete",
        "guidance": "Restricts competitive activities during and after the contract term.",
    },
    "exclusivity": {
        "title": "Exclusivity",
        "clause_type": ClauseType.EXCLUSIVITY,
        "template": (
            "EXCLUSIVITY\n\n"
            "1. During the term of this Agreement, [EXCLUSIVE_PARTY] shall be the exclusive "
            "provider of [SERVICES/PRODUCTS] to [OTHER_PARTY] within [TERRITORY].\n\n"
            "2. [OTHER_PARTY] agrees not to engage, contract with, or procure similar "
            "[SERVICES/PRODUCTS] from any third party during the term.\n\n"
            "3. Minimum Performance: The exclusivity arrangement is contingent upon [EXCLUSIVE_PARTY] "
            "meeting the following minimum performance standards: [PERFORMANCE_METRICS].\n\n"
            "4. Failure to meet minimum performance standards for [CONSECUTIVE_PERIODS] consecutive "
            "periods shall entitle [OTHER_PARTY] to terminate the exclusivity arrangement upon "
            "[NOTICE_DAYS] days' written notice.\n\n"
            "5. This exclusivity shall not prevent [OTHER_PARTY] from performing such activities "
            "internally using its own resources."
        ),
        "placeholders": [
            "EXCLUSIVE_PARTY", "OTHER_PARTY", "SERVICES/PRODUCTS", "TERRITORY",
            "PERFORMANCE_METRICS", "CONSECUTIVE_PERIODS", "NOTICE_DAYS",
        ],
        "cuad_category": "Exclusivity",
        "guidance": "Establishes sole-provider arrangements with protective performance conditions.",
    },
    "change_of_control": {
        "title": "Change of Control",
        "clause_type": ClauseType.CHANGE_OF_CONTROL,
        "template": (
            "CHANGE OF CONTROL\n\n"
            "1. \"Change of Control\" means: (a) a merger, consolidation, or similar transaction; "
            "(b) a sale of all or substantially all assets; or (c) any transaction resulting in "
            "a person or entity acquiring more than [CONTROL_THRESHOLD]% of the voting securities.\n\n"
            "2. Notice: The party undergoing a Change of Control shall provide written notice to "
            "the other party within [NOTICE_DAYS] days of the Change of Control.\n\n"
            "3. Rights: Upon a Change of Control, the non-affected party may, at its sole "
            "discretion:\n"
            "   (a) continue this Agreement with the successor entity; or\n"
            "   (b) terminate this Agreement upon [TERMINATION_DAYS] days' written notice.\n\n"
            "4. Obligations: The party undergoing the Change of Control shall ensure that the "
            "successor entity assumes all obligations under this Agreement."
        ),
        "placeholders": ["CONTROL_THRESHOLD", "NOTICE_DAYS", "TERMINATION_DAYS"],
        "cuad_category": "Change of Control",
        "guidance": "Addresses rights and obligations when corporate ownership changes.",
    },
    "anti_assignment": {
        "title": "Anti-Assignment",
        "clause_type": ClauseType.ANTI_ASSIGNMENT,
        "template": (
            "ASSIGNMENT\n\n"
            "1. Neither party may assign, transfer, or delegate any of its rights or obligations "
            "under this Agreement without the prior written consent of the other party, which "
            "consent shall not be unreasonably withheld.\n\n"
            "2. Notwithstanding the foregoing, either party may assign this Agreement without "
            "consent to:\n"
            "   (a) an affiliate that is controlled by, controls, or is under common control with "
            "the assigning party;\n"
            "   (b) a successor entity pursuant to a merger, acquisition, or sale of all or "
            "substantially all of its assets.\n\n"
            "3. Any purported assignment in violation of this section shall be void and of no effect.\n\n"
            "4. This Agreement shall be binding upon and inure to the benefit of the parties "
            "and their respective successors and permitted assigns."
        ),
        "placeholders": [],
        "cuad_category": "Anti-Assignment",
        "guidance": "Controls who can take over contract rights and obligations.",
    },
    "audit_rights": {
        "title": "Audit Rights",
        "clause_type": ClauseType.AUDIT_RIGHTS,
        "template": (
            "AUDIT RIGHTS\n\n"
            "1. [AUDITING_PARTY] shall have the right, at its own expense, to audit "
            "[AUDITED_PARTY]'s records and facilities to verify compliance with this Agreement.\n\n"
            "2. Audits shall be conducted:\n"
            "   (a) no more than [AUDIT_FREQUENCY] per calendar year;\n"
            "   (b) upon [NOTICE_DAYS] days' prior written notice;\n"
            "   (c) during normal business hours;\n"
            "   (d) in a manner that minimizes disruption to [AUDITED_PARTY]'s operations.\n\n"
            "3. [AUDITED_PARTY] shall maintain accurate and complete records related to this "
            "Agreement for a period of [RECORD_RETENTION] years after termination.\n\n"
            "4. If an audit reveals a material non-compliance or an overcharge exceeding "
            "[THRESHOLD]%, [AUDITED_PARTY] shall promptly remedy the non-compliance and "
            "reimburse [AUDITING_PARTY] for reasonable audit costs."
        ),
        "placeholders": [
            "AUDITING_PARTY", "AUDITED_PARTY", "AUDIT_FREQUENCY",
            "NOTICE_DAYS", "RECORD_RETENTION", "THRESHOLD",
        ],
        "cuad_category": "Audit Rights",
        "guidance": "Establishes the right to verify compliance through record and facility audits.",
    },
    "post_termination_services": {
        "title": "Post-Termination Services",
        "clause_type": ClauseType.POST_TERMINATION_SERVICES,
        "template": (
            "POST-TERMINATION SERVICES\n\n"
            "1. Transition Period: Upon termination or expiration of this Agreement, "
            "[PARTY_A] shall provide transition assistance to [PARTY_B] for a period of "
            "[TRANSITION_PERIOD] (the \"Transition Period\").\n\n"
            "2. Transition Services: During the Transition Period, [PARTY_A] shall:\n"
            "   (a) continue to provide services at the then-current service levels;\n"
            "   (b) cooperate with [PARTY_B] and any successor service provider;\n"
            "   (c) transfer all [PARTY_B] data in a mutually agreed format;\n"
            "   (d) provide reasonable knowledge transfer and documentation.\n\n"
            "3. Fees: Transition services shall be provided at [FEE_ARRANGEMENT].\n\n"
            "4. Data Return: Within [DATA_RETURN_DAYS] days after the Transition Period, "
            "[PARTY_A] shall securely delete all [PARTY_B] data and certify deletion in writing."
        ),
        "placeholders": [
            "PARTY_A", "PARTY_B", "TRANSITION_PERIOD", "FEE_ARRANGEMENT", "DATA_RETURN_DAYS",
        ],
        "cuad_category": "Post-Termination Services/Obligations",
        "guidance": "Ensures smooth transition and data return after contract ends.",
    },
}

# Map risk types to CUAD clause categories
RISK_TO_CLAUSE_MAP: Dict[str, str] = {
    # Direct mappings
    "governing_law": "governing_law",
    "liability": "liability",
    "confidentiality": "confidentiality",
    "termination": "termination",
    "indemnification": "indemnification",
    "payment_terms": "payment_terms",
    "intellectual_property": "intellectual_property",
    "data_protection": "data_protection",
    "force_majeure": "force_majeure",
    "non_compete": "non_compete",
    "exclusivity": "exclusivity",
    "change_of_control": "change_of_control",
    "anti_assignment": "anti_assignment",
    "audit_rights": "audit_rights",
    "post_termination_services": "post_termination_services",
    # Common risk type aliases
    "unlimited_liability": "liability",
    "missing_liability_cap": "liability",
    "no_liability_cap": "liability",
    "ip_ownership": "intellectual_property",
    "ip_rights": "intellectual_property",
    "data_privacy": "data_protection",
    "gdpr": "data_protection",
    "nda": "confidentiality",
    "non_disclosure": "confidentiality",
    "payment": "payment_terms",
    "dispute_resolution": "governing_law",
    "automatic_renewal": "termination",
    "auto_renewal": "termination",
    "assignment": "anti_assignment",
}

# Jurisdiction-specific guidance
JURISDICTION_GUIDANCE: Dict[str, str] = {
    "qatar": (
        "Ensure compliance with Qatar Civil Code (Law No. 22 of 2004) and Qatar Commercial "
        "Companies Law. Consider Qatar International Court and Dispute Resolution Centre (QICDRC) "
        "for arbitration. Arabic may be required as the official language."
    ),
    "uae": (
        "Comply with UAE Civil Transactions Law (Federal Law No. 5 of 1985). Consider DIFC or "
        "ADGM courts for commercial disputes. Sharia principles may apply to certain matters."
    ),
    "uk": (
        "Follow English common law principles. Consider the Unfair Contract Terms Act 1977 and "
        "Consumer Rights Act 2015. The Sale of Goods Act may apply."
    ),
    "usa": (
        "Consider both federal and state laws. The Uniform Commercial Code (UCC) may apply. "
        "Specify the governing state (e.g., Delaware, New York, California)."
    ),
    "eu": (
        "Ensure compliance with EU Directives and Regulations, especially GDPR for data protection. "
        "Consider Brussels I Regulation for jurisdiction and Rome I Regulation for applicable law."
    ),
}


class ClauseGeneratorService:
    """
    Service for generating AI-powered contract clauses based on CUAD patterns.

    Workflow:
    1. Receive risk/gap context from contract analysis
    2. Look up matching CUAD clause template
    3. Generate a tailored clause using LLM + template as guidance
    4. Return structured response with title, text, and explanation
    """

    def __init__(self):
        self.llm = ollama_service
        self.templates = CUAD_CLAUSE_TEMPLATES
        self.risk_map = RISK_TO_CLAUSE_MAP
        self.jurisdiction_guidance = JURISDICTION_GUIDANCE

    def get_template(self, clause_type: str) -> Optional[Dict[str, Any]]:
        """Get a CUAD clause template by type, handling aliases."""
        normalized = self.risk_map.get(clause_type.lower(), clause_type.lower())
        return self.templates.get(normalized)

    async def generate_clause(
        self,
        clause_type: str,
        risk_description: str = "",
        jurisdiction: str = "",
        contract_context: str = "",
    ) -> Dict[str, Any]:
        """
        Generate a clause addressing a specific risk or gap.

        Returns:
            {
                "clause_title": str,
                "clause_text": str,
                "explanation": str,
                "clause_type": str,
                "jurisdiction": str,
                "template_used": bool,
                "cuad_category": str,
            }
        """
        # Resolve template
        normalized_type = self.risk_map.get(clause_type.lower(), clause_type.lower())
        template = self.templates.get(normalized_type)

        if not template:
            logger.warning(f"No CUAD template for clause type '{clause_type}', using generic generation")
            return await self._generate_generic_clause(clause_type, risk_description, jurisdiction, contract_context)

        cuad_category = template.get("cuad_category", normalized_type)
        jurisdiction_notes = self.jurisdiction_guidance.get(jurisdiction.lower(), "") if jurisdiction else ""

        system_prompt = (
            f"You are an expert legal drafter. Generate a professional, contract-ready "
            f"{template['title']} clause.\n\n"
            f"CUAD Category: {cuad_category}\n"
            f"Template guidance: {template['guidance']}\n\n"
            f"Reference template (use as structural guidance, adapt to context):\n"
            f"---\n{template['template']}\n---\n\n"
        )

        if jurisdiction_notes:
            system_prompt += f"Jurisdiction ({jurisdiction}):\n{jurisdiction_notes}\n\n"

        if jurisdiction:
            system_prompt += f"The clause must comply with {jurisdiction} law.\n"

        system_prompt += (
            "Instructions:\n"
            "- Replace all [PLACEHOLDER] values with reasonable, professional defaults\n"
            "- Address the specific risk or gap described below\n"
            "- Use clear, unambiguous legal language\n"
            "- Make the clause balanced and enforceable\n"
            "- Output ONLY the clause text (with title), no extra commentary"
        )

        user_message = f"Generate a {template['title']} clause"
        if risk_description:
            user_message += f" that addresses this risk: {risk_description}"
        if contract_context:
            user_message += f"\n\nContract context: {contract_context}"

        try:
            clause_text = await self.llm.chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.4,
                max_tokens=1500,
            )

            explanation = await self._generate_explanation(
                template["title"], risk_description, jurisdiction, normalized_type
            )

            return {
                "clause_title": template["title"],
                "clause_text": clause_text.strip(),
                "explanation": explanation.strip(),
                "clause_type": normalized_type,
                "jurisdiction": jurisdiction or "general",
                "template_used": True,
                "cuad_category": cuad_category,
            }

        except Exception as e:
            logger.error(f"LLM clause generation failed for '{clause_type}': {e}")
            # Fallback: return the raw template with placeholders
            return {
                "clause_title": template["title"],
                "clause_text": template["template"],
                "explanation": (
                    f"This is a standard {template['title']} clause template based on CUAD patterns. "
                    f"Replace [PLACEHOLDER] values with contract-specific details."
                ),
                "clause_type": normalized_type,
                "jurisdiction": jurisdiction or "general",
                "template_used": True,
                "cuad_category": cuad_category,
            }

    async def _generate_explanation(
        self, clause_title: str, risk_description: str, jurisdiction: str, clause_type: str
    ) -> str:
        """Generate a brief explanation of why this clause is recommended."""
        prompt = (
            f"In 2-3 sentences, explain why a {clause_title} clause is recommended"
        )
        if risk_description:
            prompt += f" given this risk: {risk_description}"
        if jurisdiction:
            prompt += f" under {jurisdiction} law"
        prompt += ". Be concise and professional."

        try:
            return await self.llm.chat_completion(
                messages=[
                    {"role": "system", "content": "You are a contract law expert. Provide brief, clear explanations."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=300,
            )
        except Exception:
            return f"This {clause_title} clause is recommended to address identified contract risks and ensure comprehensive legal protection."

    async def _generate_generic_clause(
        self, clause_type: str, risk_description: str, jurisdiction: str, contract_context: str
    ) -> Dict[str, Any]:
        """Fallback generation when no CUAD template exists."""
        system_prompt = (
            f"You are an expert legal drafter. Generate a professional {clause_type} clause "
            f"for a commercial contract."
        )
        if jurisdiction:
            system_prompt += f" The clause must comply with {jurisdiction} law."

        user_message = f"Generate a {clause_type} clause"
        if risk_description:
            user_message += f" that addresses: {risk_description}"
        if contract_context:
            user_message += f"\n\nContract context: {contract_context}"
        user_message += "\n\nProvide only the clause text with a title."

        try:
            clause_text = await self.llm.chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.4,
                max_tokens=1500,
            )

            return {
                "clause_title": clause_type.replace("_", " ").title(),
                "clause_text": clause_text.strip(),
                "explanation": f"This clause was generated to address the identified {clause_type.replace('_', ' ')} concerns in the contract.",
                "clause_type": clause_type,
                "jurisdiction": jurisdiction or "general",
                "template_used": False,
                "cuad_category": "Custom",
            }
        except Exception as e:
            logger.error(f"Generic clause generation failed: {e}")
            raise

    def list_available_templates(self) -> list:
        """Return all available CUAD clause templates."""
        return [
            {
                "clause_type": key,
                "title": val["title"],
                "cuad_category": val["cuad_category"],
                "placeholders": val["placeholders"],
            }
            for key, val in self.templates.items()
        ]


# Singleton
clause_generator_service = ClauseGeneratorService()
