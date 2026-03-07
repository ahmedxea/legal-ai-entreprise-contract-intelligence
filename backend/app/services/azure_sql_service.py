"""
Azure SQL Database Service using SQLAlchemy with async support
Supports Azure SQL Server, PostgreSQL, and SQLite as fallback
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import uuid
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, and_, or_, desc
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.models.database import (
    Base, User, Session, Contract, DocumentText, DocumentChunk,
    ContractEntity, ContractSummary, ContractRisk, ContractGap, AuditLog
)
from app.models.schemas import ContractStatus, Language

logger = logging.getLogger(__name__)


class AzureSQLService:
    """Database service for Azure SQL / PostgreSQL using SQLAlchemy async"""
    
    def __init__(self):
        """Initialize database engine and session factory"""
        self.engine = None
        self.async_session_factory = None
        self._initialize_engine()
    
    def _initialize_engine(self):
        """Create async database engine based on configuration"""
        
        # Determine connection string
        db_url = None
        
        if settings.SQL_CONNECTION_STRING:
            # Azure SQL Server connection
            # Format: mssql+pyodbc://user:pass@server/database?driver=ODBC+Driver+18+for+SQL+Server
            db_url = settings.SQL_CONNECTION_STRING
            logger.info("Using Azure SQL Server (SQL_CONNECTION_STRING)")
            
        elif settings.DATABASE_URL:
            # Generic database URL (PostgreSQL, SQLite, etc.)
            db_url = settings.DATABASE_URL
            logger.info(f"Using DATABASE_URL: {db_url.split('@')[0]}...")
            
        else:
            # Fallback to SQLite for local development
            db_url = "sqlite+aiosqlite:///./data/contracts.db"
            logger.info("Using SQLite fallback for local development")
        
        # Create async engine
        try:
            # Connection args for different databases
            connect_args = {}
            if db_url.startswith("sqlite"):
                connect_args = {"check_same_thread": False}
            elif "pyodbc" in db_url:
                # Azure SQL / SQL Server specific settings
                connect_args = {
                    "TrustServerCertificate": "yes",
                    "Encrypt": "yes",
                }
            
            self.engine = create_async_engine(
                db_url,
                echo=False,  # Set to True for SQL debugging
                future=True,
                pool_pre_ping=True,  # Verify connections before using
            )
            
            self.async_session_factory = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )
            
            logger.info("Database engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database engine: {e}", exc_info=True)
            raise
    
    @asynccontextmanager
    async def _get_db_session(self):
        """Get an async database session (internal context manager)"""
        async with self.async_session_factory() as session:
            try:
                yield session
            except Exception as e:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def create_tables(self):
        """Create all database tables (for initial setup)"""
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {e}", exc_info=True)
            raise
    
    # ─── User Management ──────────────────────────────────────────────────────
    
    async def create_user(
        self,
        email: str,
        password_hash: str,
        full_name: str,
        organization: str = ""
    ) -> Optional[Dict[str, Any]]:
        """Create a new user account"""
        async with self._get_db_session() as session:
            try:
                user = User(
                    id=str(uuid.uuid4()),
                    email=email.lower().strip(),
                    name=full_name.strip(),
                    full_name=full_name.strip(),
                    password_hash=password_hash,
                    organization=organization.strip(),
                    role="user",
                    is_active=True,
                )
                session.add(user)
                await session.commit()
                
                return {
                    "id": user.id,
                    "email": user.email,
                    "full_name": user.full_name,
                    "name": user.name,
                    "organization": user.organization,
                    "role": user.role,
                }
            except SQLAlchemyError as e:
                logger.error(f"Error creating user: {e}")
                return None
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email address"""
        async with self._get_db_session() as session:
            try:
                result = await session.execute(
                    select(User).where(
                        and_(
                            User.email == email.lower().strip(),
                            User.is_active == True
                        )
                    )
                )
                user = result.scalar_one_or_none()
                
                if user:
                    return {
                        "id": user.id,
                        "email": user.email,
                        "password_hash": user.password_hash,
                        "full_name": user.full_name,
                        "name": user.name,
                        "organization": user.organization,
                        "role": user.role,
                    }
                return None
            except Exception as e:
                logger.error(f"Error getting user by email: {e}")
                return None
    
    async def update_user_last_login(self, user_id: str):
        """Update user's last login timestamp"""
        async with self._get_db_session() as session:
            try:
                result = await session.execute(
                    select(User).where(User.id == user_id)
                )
                user = result.scalar_one_or_none()
                if user:
                    user.last_login = datetime.utcnow()
                    await session.commit()
            except Exception as e:
                logger.error(f"Error updating last login: {e}")
    
    # ─── Session Management ───────────────────────────────────────────────────
    
    async def create_session(self, user_id: str, token: str, expires_at: datetime):
        """Create a new session token"""
        async with self._get_db_session() as session:
            try:
                new_session = Session(
                    user_id=user_id,
                    token=token,
                    expires_at=expires_at,
                )
                session.add(new_session)
                await session.commit()
            except Exception as e:
                logger.error(f"Error creating session: {e}")
                raise
    
    async def get_session(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate session token and return user"""
        async with self._get_db_session() as session:
            try:
                result = await session.execute(
                    select(Session, User)
                    .join(User, Session.user_id == User.id)
                    .where(
                        and_(
                            Session.token == token,
                            User.is_active == True,
                            Session.expires_at > datetime.utcnow()
                        )
                    )
                )
                row = result.first()
                
                if row:
                    sess, user = row
                    return {
                        "id": user.id,
                        "email": user.email,
                        "full_name": user.full_name,
                        "name": user.name,
                        "organization": user.organization,
                        "role": user.role,
                    }
                return None
            except Exception as e:
                logger.error(f"Error validating session: {e}")
                return None
    
    async def delete_session(self, token: str):
        """Delete a session token (logout)"""
        async with self._get_db_session() as session:
            try:
                result = await session.execute(
                    select(Session).where(Session.token == token)
                )
                sess = result.scalar_one_or_none()
                if sess:
                    await session.delete(sess)
                    await session.commit()
            except Exception as e:
                logger.error(f"Error deleting session: {e}")
    
    # ─── Contract Management ──────────────────────────────────────────────────
    
    async def create_contract(
        self,
        user_id: str,
        filename: str,
        blob_url: str,
        language: Language,
        industry: Optional[str] = None,
        file_size: Optional[int] = None,
        file_type: Optional[str] = None,
    ) -> str:
        """Create a new contract record"""
        async with self._get_db_session() as session:
            try:
                contract_id = str(uuid.uuid4())
                contract = Contract(
                    id=contract_id,
                    user_id=user_id,
                    filename=filename,
                    blob_url=blob_url,
                    status=ContractStatus.UPLOADED.value,
                    language=language.value if hasattr(language, 'value') else str(language),
                    industry=industry,
                    file_size=file_size,
                    file_type=file_type,
                )
                session.add(contract)
                await session.commit()
                
                logger.info(f"Contract created: {contract_id}")
                return contract_id
            except Exception as e:
                logger.error(f"Error creating contract: {e}")
                raise
    
    async def get_contract(self, contract_id: str, user_id: str) -> Optional[Dict]:
        """Get contract by ID and user (enforce ownership)"""
        async with self._get_db_session() as session:
            try:
                result = await session.execute(
                    select(Contract).where(
                        and_(
                            Contract.id == contract_id,
                            Contract.user_id == user_id
                        )
                    )
                )
                contract = result.scalar_one_or_none()
                
                if contract:
                    return self._contract_to_dict(contract)
                return None
            except Exception as e:
                logger.error(f"Error getting contract: {e}")
                return None
    
    async def get_contract_by_id(self, contract_id: str) -> Optional[Dict]:
        """Get contract by ID only (internal use, no ownership check)"""
        async with self._get_db_session() as session:
            try:
                result = await session.execute(
                    select(Contract).where(Contract.id == contract_id)
                )
                contract = result.scalar_one_or_none()
                
                if contract:
                    return self._contract_to_dict(contract)
                return None
            except Exception as e:
                logger.error(f"Error getting contract by ID: {e}")
                return None
    
    async def list_contracts(
        self,
        user_id: str,
        status: Optional[ContractStatus] = None,
        limit: int = 50
    ) -> List[Dict]:
        """List contracts for a user"""
        async with self._get_db_session() as session:
            try:
                query = select(Contract).where(Contract.user_id == user_id)
                
                if status:
                    query = query.where(Contract.status == status.value)
                
                query = query.order_by(desc(Contract.upload_date)).limit(limit)
                
                result = await session.execute(query)
                contracts = result.scalars().all()
                
                return [self._contract_to_dict(c) for c in contracts]
            except Exception as e:
                logger.error(f"Error listing contracts: {e}")
                return []
    
    async def update_contract_status(self, contract_id: str, status: ContractStatus):
        """Update contract processing status"""
        async with self._get_db_session() as session:
            try:
                result = await session.execute(
                    select(Contract).where(Contract.id == contract_id)
                )
                contract = result.scalar_one_or_none()
                
                if contract:
                    contract.status = status.value if hasattr(status, 'value') else str(status)
                    await session.commit()
                    logger.info(f"Contract {contract_id} status updated to {status}")
            except Exception as e:
                logger.error(f"Error updating contract status: {e}")
                raise
    
    async def update_contract_analysis(self, contract_id: str, analysis_data: Dict):
        """Update contract with legacy analysis column"""
        async with self._get_db_session() as session:
            try:
                result = await session.execute(
                    select(Contract).where(Contract.id == contract_id)
                )
                contract = result.scalar_one_or_none()
                
                if contract:
                    contract.analysis = json.dumps(analysis_data)
                    if "extracted_data" in analysis_data:
                        contract.extracted_data = json.dumps(analysis_data["extracted_data"])
                    await session.commit()
            except Exception as e:
                logger.error(f"Error updating contract analysis: {e}")
                raise
    
    def _contract_to_dict(self, contract: Contract) -> Dict:
        """Convert SQLAlchemy Contract model to dictionary"""
        upload_date_iso = contract.upload_date.isoformat() if contract.upload_date else None
        
        data = {
            "id": contract.id,
            "user_id": contract.user_id,
            "filename": contract.filename,
            "blob_url": contract.blob_url,
            "upload_date": upload_date_iso,
            "uploaded_at": upload_date_iso,
            "status": contract.status,
            "language": contract.language,
            "industry": contract.industry,
            "file_size": contract.file_size,
            "file_type": contract.file_type,
        }
        
        # Parse JSON fields (check for None and non-empty strings)
        if contract.extracted_data and isinstance(contract.extracted_data, str):
            try:
                data["extracted_data"] = json.loads(contract.extracted_data)
            except:
                pass
        
        if contract.analysis and isinstance(contract.analysis, str):
            try:
                data["analysis"] = json.loads(contract.analysis)
            except:
                pass
        
        return data
    
    # ─── Phase 1: Document Text ───────────────────────────────────────────────
    
    async def save_document_text(
        self,
        document_id: str,
        raw_text: str,
        paragraphs: List[str],
        page_count: Optional[int] = None,
        file_type: Optional[str] = None,
    ):
        """Save extracted document text"""
        async with self._get_db_session() as session:
            try:
                doc_text = DocumentText(
                    document_id=document_id,
                    raw_text=raw_text,
                    paragraphs=json.dumps(paragraphs),
                    page_count=page_count,
                    file_type=file_type,
                )
                await session.merge(doc_text)
                await session.commit()
            except Exception as e:
                logger.error(f"Error saving document text: {e}")
                raise
    
    async def get_document_text(self, document_id: str) -> Optional[Dict]:
        """Get extracted document text"""
        async with self._get_db_session() as session:
            try:
                result = await session.execute(
                    select(DocumentText).where(DocumentText.document_id == document_id)
                )
                doc_text = result.scalar_one_or_none()
                
                if doc_text:
                    return {
                        "raw_text": doc_text.raw_text,
                        "paragraphs": json.loads(doc_text.paragraphs),
                        "page_count": doc_text.page_count,
                        "file_type": doc_text.file_type,
                    }
                return None
            except Exception as e:
                logger.error(f"Error getting document text: {e}")
                return None
    
    async def save_document_chunks(self, document_id: str, chunks: List[str]):
        """Save document chunks for retrieval"""
        async with self._get_db_session() as session:
            try:
                # Delete existing chunks first
                await session.execute(
                    select(DocumentChunk).where(DocumentChunk.document_id == document_id)
                )
                
                # Insert new chunks
                for idx, chunk_text in enumerate(chunks):
                    chunk = DocumentChunk(
                        chunk_id=str(uuid.uuid4()),
                        document_id=document_id,
                        chunk_index=idx,
                        chunk_text=chunk_text,
                    )
                    session.add(chunk)
                
                await session.commit()
            except Exception as e:
                logger.error(f"Error saving document chunks: {e}")
                raise
    
    async def get_document_chunks(self, document_id: str) -> List[Dict]:
        """Get document chunks"""
        async with self._get_db_session() as session:
            try:
                result = await session.execute(
                    select(DocumentChunk)
                    .where(DocumentChunk.document_id == document_id)
                    .order_by(DocumentChunk.chunk_index)
                )
                chunks = result.scalars().all()
                
                return [
                    {
                        "chunk_index": c.chunk_index,
                        "chunk_text": c.chunk_text,
                    }
                    for c in chunks
                ]
            except Exception as e:
                logger.error(f"Error getting document chunks: {e}")
                return []
    
    # ─── Phase 2: Analysis Results ────────────────────────────────────────────
    
    async def save_contract_entities(self, contract_id: str, entities: Dict):
        """Save structured entity extraction results"""
        async with self._get_db_session() as session:
            try:
                entity_record = ContractEntity(
                    document_id=contract_id,
                    extraction_json=json.dumps(entities),
                )
                await session.merge(entity_record)
                await session.commit()
            except Exception as e:
                logger.error(f"Error saving contract entities: {e}")
                raise
    
    async def get_contract_entities(self, contract_id: str) -> Optional[Dict]:
        """Get contract entities"""
        async with self._get_db_session() as session:
            try:
                result = await session.execute(
                    select(ContractEntity).where(ContractEntity.document_id == contract_id)
                )
                entity = result.scalar_one_or_none()
                
                if entity:
                    return json.loads(entity.extraction_json)
                return None
            except Exception as e:
                logger.error(f"Error getting contract entities: {e}")
                return None
    
    async def save_contract_summary(self, contract_id: str, summary: str):
        """Save executive summary"""
        async with self._get_db_session() as session:
            try:
                summary_record = ContractSummary(
                    document_id=contract_id,
                    summary_text=summary,
                )
                await session.merge(summary_record)
                await session.commit()
            except Exception as e:
                logger.error(f"Error saving contract summary: {e}")
                raise
    
    async def get_contract_summary(self, contract_id: str) -> Optional[str]:
        """Get contract summary"""
        async with self._get_db_session() as session:
            try:
                result = await session.execute(
                    select(ContractSummary).where(ContractSummary.document_id == contract_id)
                )
                summary = result.scalar_one_or_none()
                
                if summary:
                    return summary.summary_text
                return None
            except Exception as e:
                logger.error(f"Error getting contract summary: {e}")
                return None
    
    async def save_contract_risks(self, contract_id: str, risks: List[Dict]):
        """Save risk findings"""
        async with self._get_db_session() as session:
            try:
                # Delete existing risks
                result = await session.execute(
                    select(ContractRisk).where(ContractRisk.document_id == contract_id)
                )
                for risk in result.scalars().all():
                    await session.delete(risk)
                
                # Insert new risks
                for risk_data in risks:
                    risk = ContractRisk(
                        risk_id=str(uuid.uuid4()),
                        document_id=contract_id,
                        risk_type=risk_data.get("risk_type", ""),
                        severity=risk_data.get("severity", "low"),
                        description=risk_data.get("description", ""),
                        source_text=risk_data.get("source_text", ""),
                    )
                    session.add(risk)
                
                await session.commit()
            except Exception as e:
                logger.error(f"Error saving contract risks: {e}")
                raise
    
    async def get_contract_risks(self, contract_id: str) -> List[Dict]:
        """Get contract risks"""
        async with self._get_db_session() as session:
            try:
                result = await session.execute(
                    select(ContractRisk).where(ContractRisk.document_id == contract_id)
                )
                risks = result.scalars().all()
                
                return [
                    {
                        "risk_type": r.risk_type,
                        "severity": r.severity,
                        "description": r.description,
                        "source_text": r.source_text,
                    }
                    for r in risks
                ]
            except Exception as e:
                logger.error(f"Error getting contract risks: {e}")
                return []
    
    async def save_contract_gaps(self, contract_id: str, missing_clauses: List[str]):
        """Save missing clause gaps"""
        async with self._get_db_session() as session:
            try:
                gap_record = ContractGap(
                    document_id=contract_id,
                    missing_clauses_json=json.dumps(missing_clauses),
                )
                await session.merge(gap_record)
                await session.commit()
            except Exception as e:
                logger.error(f"Error saving contract gaps: {e}")
                raise
    
    async def get_contract_gaps(self, contract_id: str) -> Optional[List[str]]:
        """Get missing clauses"""
        async with self._get_db_session() as session:
            try:
                result = await session.execute(
                    select(ContractGap).where(ContractGap.document_id == contract_id)
                )
                gap = result.scalar_one_or_none()
                
                if gap:
                    return json.loads(gap.missing_clauses_json)
                return None
            except Exception as e:
                logger.error(f"Error getting contract gaps: {e}")
                return None
    
    # ─── Audit Logging ────────────────────────────────────────────────────────
    
    async def create_audit_log(
        self,
        user_id: str,
        action: str,
        contract_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """Create audit log entry"""
        async with self._get_db_session() as session:
            try:
                audit = AuditLog(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    action=action,
                    contract_id=contract_id,
                    metadata=json.dumps(metadata) if metadata else None,
                )
                session.add(audit)
                await session.commit()
            except Exception as e:
                logger.error(f"Error creating audit log: {e}")


# Create singleton instance
azure_sql_service = AzureSQLService()
