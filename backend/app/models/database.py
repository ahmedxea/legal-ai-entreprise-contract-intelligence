"""
SQLAlchemy database models for Azure SQL Database
Compatible with PostgreSQL, Azure SQL Server, and SQLite
"""
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Index, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
import uuid

Base = declarative_base()


def generate_uuid():
    """Generate a UUID string for primary keys"""
    return str(uuid.uuid4())


class User(Base):
    """User accounts table"""
    __tablename__ = "users"
    
    id = Column(String(100), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), default="")
    password_hash = Column(Text, default="")
    full_name = Column(String(255), default="")
    organization = Column(String(255), default="")
    role = Column(String(50), default="user")
    last_login = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_date = Column(DateTime, default=func.now(), nullable=False)


class Session(Base):
    """User session tokens for authentication"""
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), ForeignKey("users.id"), nullable=False, index=True)
    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=func.now())


class Contract(Base):
    """Contract documents table"""
    __tablename__ = "contracts"
    
    id = Column(String(100), primary_key=True, default=generate_uuid)
    user_id = Column(String(100), ForeignKey("users.id"), nullable=False, index=True)
    filename = Column(String(500), nullable=False)
    blob_url = Column(Text, nullable=False)
    upload_date = Column(DateTime, default=func.now(), nullable=False)
    status = Column(String(50), nullable=False, index=True)
    language = Column(String(10), nullable=False, default="en")
    industry = Column(String(100), nullable=True)
    extracted_data = Column(Text, nullable=True)
    analysis = Column(Text, nullable=True)
    file_size = Column(Integer, nullable=True)
    file_type = Column(String(20), nullable=True)


class DocumentText(Base):
    """Extracted raw text from documents (Phase 1)"""
    __tablename__ = "document_text"
    
    document_id = Column(String(100), ForeignKey("contracts.id"), primary_key=True)
    raw_text = Column(Text, nullable=False)
    paragraphs = Column(Text, nullable=False, default="[]")
    page_count = Column(Integer, nullable=True)
    file_type = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)


class DocumentChunk(Base):
    """Text chunks for retrieval (Phase 1)"""
    __tablename__ = "document_chunks"
    
    chunk_id = Column(String(100), primary_key=True, default=generate_uuid)
    document_id = Column(String(100), ForeignKey("contracts.id"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)


class ContractEntity(Base):
    """Structured entity extraction results (Phase 2)"""
    __tablename__ = "contract_entities"
    
    document_id = Column(String(100), ForeignKey("contracts.id"), primary_key=True)
    extraction_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)


class ContractSummary(Base):
    """Executive summaries (Phase 2)"""
    __tablename__ = "contract_summaries"
    
    document_id = Column(String(100), ForeignKey("contracts.id"), primary_key=True)
    summary_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)


class ContractRisk(Base):
    """Risk findings (Phase 2)"""
    __tablename__ = "contract_risks"
    
    risk_id = Column(String(100), primary_key=True, default=generate_uuid)
    document_id = Column(String(100), ForeignKey("contracts.id"), nullable=False, index=True)
    risk_type = Column(String(100), nullable=False)
    severity = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    source_text = Column(Text, nullable=True)


class ContractGap(Base):
    """Missing clause detection (Phase 2)"""
    __tablename__ = "contract_gaps"
    
    document_id = Column(String(100), ForeignKey("contracts.id"), primary_key=True)
    missing_clauses_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)


class AuditLog(Base):
    """Audit trail for user actions"""
    __tablename__ = "audit_logs"
    
    id = Column(String(100), primary_key=True, default=generate_uuid)
    user_id = Column(String(100), ForeignKey("users.id"), nullable=False, index=True)
    action = Column(String(100), nullable=False)
    contract_id = Column(String(100), ForeignKey("contracts.id"), nullable=True)
    timestamp = Column(DateTime, default=func.now(), nullable=False)
    action_metadata = Column(Text, nullable=True)  # Renamed from 'metadata' (reserved in SQLAlchemy)


# Create indexes for performance
Index('idx_contracts_user_status', Contract.user_id, Contract.status)
Index('idx_sessions_token', Session.token)
Index('idx_sessions_user_id', Session.user_id)
Index('idx_audit_user_timestamp', AuditLog.user_id, AuditLog.timestamp)
