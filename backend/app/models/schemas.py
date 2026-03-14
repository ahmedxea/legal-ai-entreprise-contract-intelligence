"""
Pydantic schemas for request/response models
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class RiskLevel(str, Enum):
    """Risk level enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ContractStatus(str, Enum):
    """Contract processing status"""
    UPLOADED = "uploaded"
    EXTRACTING = "extracting"
    EXTRACTED = "extracted"
    PROCESSING = "processing"
    ANALYZED = "analyzed"
    FAILED = "failed"


class Language(str, Enum):
    """Supported languages"""
    ENGLISH = "en"
    ARABIC = "ar"


class Industry(str, Enum):
    """Industry sectors"""
    CONSTRUCTION = "construction"
    FINANCE = "finance"
    TECHNOLOGY = "technology"
    HEALTHCARE = "healthcare"
    MANUFACTURING = "manufacturing"
    SERVICES = "services"
    GOVERNMENT = "government"
    OTHER = "other"


class GoverningLaw(str, Enum):
    """Jurisdictions"""
    QATAR = "qatar"
    UK = "uk"
    UAE = "uae"
    USA = "usa"
    OTHER = "other"


# Contract Models
class ContractParty(BaseModel):
    """Contract party information"""
    name: str
    role: str  # e.g., "Contractor", "Client", "Vendor"
    contact: Optional[str] = None


class KeyDate(BaseModel):
    """Important contract dates"""
    date_type: str  # e.g., "Effective Date", "Expiration Date"
    date: str
    description: Optional[str] = None


class FinancialTerm(BaseModel):
    """Financial terms and conditions"""
    description: str
    amount: Optional[float] = None
    currency: str = "QAR"
    payment_schedule: Optional[str] = None


class Obligation(BaseModel):
    """Contract obligations"""
    party: str
    description: str
    deadline: Optional[str] = None


class ExtractedData(BaseModel):
    """Extracted contract data"""
    parties: List[ContractParty] = []
    key_dates: List[KeyDate] = []
    financial_terms: List[FinancialTerm] = []
    governing_law: Optional[str] = None
    jurisdiction: Optional[str] = None
    obligations: List[Obligation] = []
    contract_type: Optional[str] = None
    contract_value: Optional[float] = None


class RiskItem(BaseModel):
    """Identified risk item"""
    risk_type: str
    severity: RiskLevel
    description: str
    source_text: Optional[str] = None        # Phase 2: verbatim clause text
    clause_reference: Optional[str] = None
    page_number: Optional[int] = None
    recommendation: Optional[str] = None


class ComplianceItem(BaseModel):
    """Compliance check item"""
    clause_type: str
    status: str  # "present", "missing", "incomplete"
    description: str
    recommendation: Optional[str] = None


class LegalOpinion(BaseModel):
    """Legal advisory opinion"""
    topic: str
    opinion: str
    legal_basis: Optional[str] = None
    recommendation: Optional[str] = None
    severity: Optional[RiskLevel] = None


class ContractAnalysis(BaseModel):
    """Complete contract analysis results"""
    summary: str
    risks: List[RiskItem] = []
    compliance: List[ComplianceItem] = []
    legal_opinions: List[LegalOpinion] = []
    overall_risk_score: float = Field(ge=0, le=10)
    compliance_score: float = Field(ge=0, le=100)
    # Phase 2 additions
    entities: Optional[Dict[str, Any]] = None       # structured extraction output
    missing_clauses: Optional[List[str]] = None     # gap analysis output


# ── Phase 2: dedicated analysis response ─────────────────────────────────────

class ContractAnalysisResponse(BaseModel):
    """
    Full Phase 2 analysis result for GET /api/contracts/{id}/analysis.
    All four analysis types are presented as flat, nullable fields so the
    client can display partial results when analysis is still in progress.
    """
    contract_id: str
    status: str                                     # processing | analyzed | failed
    summary: Optional[str] = None
    entities: Optional[Dict[str, Any]] = None
    risks: Optional[List[RiskItem]] = None
    missing_clauses: Optional[List[str]] = None
    overall_risk_score: Optional[float] = None


# Request/Response Models
class ContractUploadResponse(BaseModel):
    """Response for contract upload"""
    contract_id: str
    filename: str
    status: ContractStatus
    message: str


class ContractDetail(BaseModel):
    """Detailed contract information"""
    id: str
    user_id: str
    filename: str
    upload_date: datetime
    status: ContractStatus
    language: Language
    industry: Optional[str] = None
    governing_law: Optional[str] = None
    file_size: Optional[int] = None
    file_type: Optional[str] = None
    page_count: Optional[int] = None
    extracted_data: Optional[Dict[str, Any]] = None
    analysis: Optional[Dict[str, Any]] = None
    blob_url: Optional[str] = None


class ContractListItem(BaseModel):
    """Contract list item for dashboard"""
    id: str
    filename: str
    upload_date: datetime
    status: ContractStatus
    risk_level: Optional[RiskLevel] = None
    contract_value: Optional[float] = None
    expiry_date: Optional[str] = None
    analysis: Optional[Dict[str, Any]] = None
    extracted_data: Optional[Dict[str, Any]] = None
    blob_url: Optional[str] = None


class ClauseTemplate(BaseModel):
    """Clause template model"""
    id: str
    type: str
    industry: List[Industry]
    jurisdiction: GoverningLaw
    language: Language
    template: str
    legal_basis: Optional[str] = None
    risk_level: RiskLevel = RiskLevel.LOW


class GenerateContractRequest(BaseModel):
    """Request to generate contract clauses"""
    industry: Industry
    governing_law: GoverningLaw
    language: Language
    clause_types: List[str]
    custom_parameters: Optional[Dict[str, Any]] = {}


class AuditLogEntry(BaseModel):
    """Audit log entry"""
    id: str
    user_id: str
    action: str
    contract_id: Optional[str] = None
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None


# ── Phase 1: Document processing models ──────────────────────────────────────

class ChunkItem(BaseModel):
    """A single text chunk produced from a document"""
    chunk_id: str
    chunk_index: int
    chunk_text: str


class DocumentTextResponse(BaseModel):
    """Extracted text and paragraph structure for a document"""
    document_id: str
    raw_text: str
    paragraphs: List[str]
    page_count: Optional[int] = None
    file_type: Optional[str] = None


class DocumentChunksResponse(BaseModel):
    """All chunks produced from a document"""
    document_id: str
    total_chunks: int
    chunks: List[ChunkItem]
