"""
Database service using SQLite (free alternative to Cosmos DB)
"""
import sqlite3
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import json
import os
from pathlib import Path

from app.models.schemas import ContractStatus, RiskLevel, Language

logger = logging.getLogger(__name__)


class DatabaseService:
    """Service for managing data in SQLite"""
    
    def __init__(self, db_path: str = "data/contracts.db"):
        """
        Initialize SQLite database
        
        Args:
            db_path: Path to SQLite database file
        """
        # Ensure data directory exists
        db_file = Path(db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.db_path = db_path
        self._initialize_database()
        logger.info(f"SQLite database initialized at: {db_path}")
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        return conn
    
    def _initialize_database(self):
        """Initialize database tables"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Create contracts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS contracts (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    blob_url TEXT NOT NULL,
                    upload_date TEXT NOT NULL,
                    status TEXT NOT NULL,
                    language TEXT NOT NULL,
                    industry TEXT,
                    extracted_data TEXT,
                    analysis TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            # Create indexes for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_contracts_user_id 
                ON contracts(user_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_contracts_status 
                ON contracts(status)
            """)
            
            # Create users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    name TEXT,
                    created_date TEXT NOT NULL
                )
            """)
            
            # Create audit_logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    contract_id TEXT,
                    timestamp TEXT NOT NULL,
                    metadata TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (contract_id) REFERENCES contracts (id)
                )
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id 
                ON audit_logs(user_id)
            """)

            # Phase 1: document text storage
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS document_text (
                    document_id TEXT PRIMARY KEY,
                    raw_text TEXT NOT NULL,
                    paragraphs TEXT NOT NULL DEFAULT '[]',
                    page_count INTEGER,
                    file_type TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (document_id) REFERENCES contracts (id)
                )
            """)

            # Phase 1: document chunks storage
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS document_chunks (
                    chunk_id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    chunk_text TEXT NOT NULL,
                    FOREIGN KEY (document_id) REFERENCES contracts (id)
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_chunks_document_id
                ON document_chunks(document_id)
            """)

            # Phase 2: structured entity extraction
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS contract_entities (
                    document_id TEXT PRIMARY KEY,
                    extraction_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (document_id) REFERENCES contracts (id)
                )
            """)

            # Phase 2: executive summaries
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS contract_summaries (
                    document_id TEXT PRIMARY KEY,
                    summary_text TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (document_id) REFERENCES contracts (id)
                )
            """)

            # Phase 2: risk findings
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS contract_risks (
                    risk_id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    risk_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    description TEXT NOT NULL,
                    source_text TEXT,
                    FOREIGN KEY (document_id) REFERENCES contracts (id)
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_risks_document_id
                ON contract_risks(document_id)
            """)

            # Phase 2: missing clause gaps
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS contract_gaps (
                    document_id TEXT PRIMARY KEY,
                    missing_clauses_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (document_id) REFERENCES contracts (id)
                )
            """)

            conn.commit()
            logger.info("Database tables initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()

        # Migrate existing contracts table to add Phase 1 columns
        self._migrate_contracts_table()

    def _migrate_contracts_table(self):
        """
        Add Phase 1 columns to contracts table if they do not already exist.
        SQLite does not support IF NOT EXISTS on ALTER TABLE, so each column
        migration is attempted individually and duplicate-column errors are
        silently ignored.
        """
        migrations = [
            "ALTER TABLE contracts ADD COLUMN file_size INTEGER",
            "ALTER TABLE contracts ADD COLUMN file_type TEXT",
            "ALTER TABLE contracts ADD COLUMN page_count INTEGER",
        ]
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            for sql in migrations:
                try:
                    cursor.execute(sql)
                    conn.commit()
                except sqlite3.OperationalError as e:
                    if "duplicate column" in str(e).lower():
                        pass  # column already exists – safe to ignore
                    else:
                        raise
        finally:
            conn.close()
    
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
        contract_id = str(uuid.uuid4())
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO contracts 
                (id, user_id, filename, blob_url, upload_date, status, language, industry,
                 extracted_data, analysis, file_size, file_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                contract_id,
                user_id,
                filename,
                blob_url,
                datetime.utcnow().isoformat(),
                ContractStatus.UPLOADED.value,
                language.value,
                industry,
                None,
                None,
                file_size,
                file_type,
            ))
            
            conn.commit()
            logger.info(f"Created contract: {contract_id}")
            return contract_id
            
        except Exception as e:
            logger.error(f"Error creating contract: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    async def get_contract(self, contract_id: str, user_id: str) -> Optional[Dict]:
        """Get a contract by ID"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT * FROM contracts 
                WHERE id = ? AND user_id = ?
            """, (contract_id, user_id))
            
            row = cursor.fetchone()
            if row:
                contract = dict(row)
                # Parse JSON fields
                if contract.get("extracted_data"):
                    contract["extracted_data"] = json.loads(contract["extracted_data"])
                if contract.get("analysis"):
                    contract["analysis"] = json.loads(contract["analysis"])
                return contract
            return None
            
        except Exception as e:
            logger.error(f"Error reading contract: {e}")
            return None
        finally:
            conn.close()
    
    async def get_contract_by_id(self, contract_id: str) -> Optional[Dict]:
        """Get a contract by ID only (no user_id check) - for internal use"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT * FROM contracts 
                WHERE id = ?
            """, (contract_id,))
            
            row = cursor.fetchone()
            if row:
                contract = dict(row)
                # Parse JSON fields
                if contract.get("extracted_data"):
                    contract["extracted_data"] = json.loads(contract["extracted_data"])
                if contract.get("analysis"):
                    contract["analysis"] = json.loads(contract["analysis"])
                return contract
            return None
            
        except Exception as e:
            logger.error(f"Error reading contract: {e}")
            return None
        finally:
            conn.close()
    
    async def update_contract_status(self, contract_id: str, status: ContractStatus):
        """Update contract status"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE contracts 
                SET status = ?
                WHERE id = ?
            """, (status.value, contract_id))
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"Error updating contract status: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    async def update_contract_analysis(self, contract_id: str, analysis_result: Dict):
        """Update contract with analysis results"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Convert dicts to JSON strings
            extracted_data_json = json.dumps(analysis_result.get("extracted_data")) if analysis_result.get("extracted_data") else None
            analysis_json = json.dumps(analysis_result.get("analysis")) if analysis_result.get("analysis") else None
            
            cursor.execute("""
                UPDATE contracts 
                SET extracted_data = ?, analysis = ?
                WHERE id = ?
            """, (extracted_data_json, analysis_json, contract_id))
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"Error updating contract analysis: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    async def list_contracts(
        self,
        user_id: str,
        status: Optional[ContractStatus] = None,
        limit: int = 50
    ) -> List[Dict]:
        """List contracts for a user"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            query = "SELECT * FROM contracts WHERE user_id = ?"
            params: List[Any] = [user_id]
            
            if status:
                query += " AND status = ?"
                params.append(status.value)
            
            query += " ORDER BY upload_date DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            contracts = []
            for row in rows:
                contract = dict(row)
                # Parse JSON fields
                if contract.get("extracted_data"):
                    contract["extracted_data"] = json.loads(contract["extracted_data"])
                if contract.get("analysis"):
                    contract["analysis"] = json.loads(contract["analysis"])
                contracts.append(contract)
            
            return contracts
            
        except Exception as e:
            logger.error(f"Error listing contracts: {e}")
            return []
        finally:
            conn.close()
    
    async def delete_contract(self, contract_id: str):
        """Delete a contract"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM contracts WHERE id = ?", (contract_id,))
            conn.commit()
            
        except Exception as e:
            logger.error(f"Error deleting contract: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    async def create_audit_log(
        self,
        user_id: str,
        action: str,
        contract_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """Create an audit log entry"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            log_id = str(uuid.uuid4())
            metadata_json = json.dumps(metadata) if metadata else None
            
            cursor.execute("""
                INSERT INTO audit_logs 
                (id, user_id, action, contract_id, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                log_id,
                user_id,
                action,
                contract_id,
                datetime.utcnow().isoformat(),
                metadata_json
            ))
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"Error creating audit log: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    async def get_audit_logs(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Get audit logs for a user"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT * FROM audit_logs 
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (user_id, limit))
            
            rows = cursor.fetchall()
            logs = []
            for row in rows:
                log = dict(row)
                if log.get("metadata"):
                    log["metadata"] = json.loads(log["metadata"])
                logs.append(log)
            
            return logs
            
        except Exception as e:
            logger.error(f"Error retrieving audit logs: {e}")
            return []
        finally:
            conn.close()
    
    async def get_user_risks(
        self,
        user_id: str,
        severity: Optional[RiskLevel] = None,
        limit: int = 50
    ) -> List[Dict]:
        """Get all risks across user's contracts"""
        contracts = await self.list_contracts(user_id, limit=limit)
        
        all_risks = []
        for contract in contracts:
            if contract.get("analysis") and contract["analysis"].get("risks"):
                for risk in contract["analysis"]["risks"]:
                    if not severity or risk.get("severity") == severity.value:
                        risk_item = {
                            **risk,
                            "contract_id": contract["id"],
                            "contract_filename": contract["filename"]
                        }
                        all_risks.append(risk_item)
        
        return all_risks[:limit]
    
    async def get_user_dashboard_stats(self, user_id: str) -> Dict:
        """Get dashboard statistics for a user"""
        contracts = await self.list_contracts(user_id, limit=1000)
        
        total_contracts = len(contracts)
        analyzed_contracts = sum(1 for c in contracts if c["status"] == "analyzed")
        
        # Calculate risks
        all_risks = []
        for contract in contracts:
            if contract.get("analysis") and contract["analysis"].get("risks"):
                all_risks.extend(contract["analysis"]["risks"])
        
        high_risks = sum(1 for r in all_risks if r.get("severity") == "high")
        medium_risks = sum(1 for r in all_risks if r.get("severity") == "medium")
        
        # Calculate average risk score
        risk_scores = [
            contract["analysis"]["overall_risk_score"]
            for contract in contracts
            if contract.get("analysis") and contract["analysis"].get("overall_risk_score")
        ]
        avg_risk_score = sum(risk_scores) / len(risk_scores) if risk_scores else 0
        
        # Calculate average compliance score
        compliance_scores = [
            contract["analysis"]["compliance_score"]
            for contract in contracts
            if contract.get("analysis") and contract["analysis"].get("compliance_score")
        ]
        avg_compliance = sum(compliance_scores) / len(compliance_scores) if compliance_scores else 0
        
        return {
            "total_contracts": total_contracts,
            "analyzed_contracts": analyzed_contracts,
            "high_risks": high_risks,
            "medium_risks": medium_risks,
            "average_risk_score": round(avg_risk_score, 2),
            "average_compliance_score": round(avg_compliance, 2),
            "recent_uploads": contracts[:5] if contracts else []
        }


    async def update_contract_page_count(self, contract_id: str, page_count: int) -> None:
        """Persist page_count extracted during document processing"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE contracts SET page_count = ? WHERE id = ?",
                (page_count, contract_id),
            )
            conn.commit()
        except Exception as e:
            logger.error(f"Error updating page_count for {contract_id}: {e}")
            conn.rollback()
        finally:
            conn.close()

    # ── Phase 1: document text ────────────────────────────────────────────────

    async def save_document_text(
        self,
        document_id: str,
        raw_text: str,
        paragraphs: List[str],
        page_count: Optional[int] = None,
        file_type: Optional[str] = None,
    ) -> None:
        """
        Persist extracted text for a document.
        Uses INSERT OR REPLACE so re-processing is idempotent.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT OR REPLACE INTO document_text
                    (document_id, raw_text, paragraphs, page_count, file_type, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    document_id,
                    raw_text,
                    json.dumps(paragraphs),
                    page_count,
                    file_type,
                    datetime.utcnow().isoformat(),
                ),
            )
            conn.commit()
            logger.debug(f"Saved document text for {document_id}: {len(raw_text)} chars")
        except Exception as e:
            logger.error(f"Error saving document text for {document_id}: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()

    async def get_document_text(self, document_id: str) -> Optional[Dict]:
        """
        Retrieve extracted text for a document.
        Returns None if text has not been extracted yet.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT * FROM document_text WHERE document_id = ?",
                (document_id,),
            )
            row = cursor.fetchone()
            if row is None:
                return None
            result = dict(row)
            result["paragraphs"] = json.loads(result.get("paragraphs") or "[]")
            return result
        except Exception as e:
            logger.error(f"Error retrieving document text for {document_id}: {e}")
            return None
        finally:
            conn.close()

    # ── Phase 1: document chunks ──────────────────────────────────────────────

    async def save_chunks(self, document_id: str, chunks: List[Dict]) -> None:
        """
        Persist text chunks for a document.
        Deletes existing chunks first to keep the operation idempotent.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "DELETE FROM document_chunks WHERE document_id = ?",
                (document_id,),
            )
            cursor.executemany(
                """
                INSERT INTO document_chunks (chunk_id, document_id, chunk_index, chunk_text)
                VALUES (?, ?, ?, ?)
                """,
                [
                    (
                        str(uuid.uuid4()),
                        document_id,
                        chunk["chunk_index"],
                        chunk["chunk_text"],
                    )
                    for chunk in chunks
                ],
            )
            conn.commit()
            logger.debug(f"Saved {len(chunks)} chunks for {document_id}")
        except Exception as e:
            logger.error(f"Error saving chunks for {document_id}: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()

    async def get_chunks(self, document_id: str) -> List[Dict]:
        """
        Retrieve all chunks for a document, ordered by chunk_index.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT chunk_id, document_id, chunk_index, chunk_text
                FROM document_chunks
                WHERE document_id = ?
                ORDER BY chunk_index
                """,
                (document_id,),
            )
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error retrieving chunks for {document_id}: {e}")
            return []
        finally:
            conn.close()

    # ── Phase 2: entity extraction ────────────────────────────────────────────

    async def save_contract_entities(self, document_id: str, extraction: Dict) -> None:
        """Persist structured entity extraction result. Overwrites on re-analysis."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT OR REPLACE INTO contract_entities
                    (document_id, extraction_json, created_at)
                VALUES (?, ?, ?)
                """,
                (document_id, json.dumps(extraction), datetime.utcnow().isoformat()),
            )
            conn.commit()
        except Exception as e:
            logger.error(f"Error saving entities for {document_id}: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()

    async def get_contract_entities(self, document_id: str) -> Optional[Dict]:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT extraction_json FROM contract_entities WHERE document_id = ?",
                (document_id,),
            )
            row = cursor.fetchone()
            return json.loads(row["extraction_json"]) if row else None
        except Exception as e:
            logger.error(f"Error retrieving entities for {document_id}: {e}")
            return None
        finally:
            conn.close()

    # ── Phase 2: summaries ────────────────────────────────────────────────────

    async def save_contract_summary(self, document_id: str, summary_text: str) -> None:
        """Persist executive summary. Overwrites on re-analysis."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT OR REPLACE INTO contract_summaries
                    (document_id, summary_text, created_at)
                VALUES (?, ?, ?)
                """,
                (document_id, summary_text, datetime.utcnow().isoformat()),
            )
            conn.commit()
        except Exception as e:
            logger.error(f"Error saving summary for {document_id}: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()

    async def get_contract_summary(self, document_id: str) -> Optional[str]:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT summary_text FROM contract_summaries WHERE document_id = ?",
                (document_id,),
            )
            row = cursor.fetchone()
            return row["summary_text"] if row else None
        except Exception as e:
            logger.error(f"Error retrieving summary for {document_id}: {e}")
            return None
        finally:
            conn.close()

    # ── Phase 2: risks ────────────────────────────────────────────────────────

    async def save_contract_risks(self, document_id: str, risks: List[Dict]) -> None:
        """
        Persist risk findings. Deletes existing risks for the document first
        to keep the operation idempotent.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "DELETE FROM contract_risks WHERE document_id = ?", (document_id,)
            )
            cursor.executemany(
                """
                INSERT INTO contract_risks
                    (risk_id, document_id, risk_type, severity, description, source_text)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        str(uuid.uuid4()),
                        document_id,
                        r.get("risk_type", "unknown"),
                        r.get("severity", "medium"),
                        r.get("description", ""),
                        r.get("source_text"),
                    )
                    for r in risks
                ],
            )
            conn.commit()
        except Exception as e:
            logger.error(f"Error saving risks for {document_id}: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()

    async def get_contract_risks(self, document_id: str) -> List[Dict]:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT risk_id, document_id, risk_type, severity, description, source_text
                FROM contract_risks
                WHERE document_id = ?
                """,
                (document_id,),
            )
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error retrieving risks for {document_id}: {e}")
            return []
        finally:
            conn.close()

    # ── Phase 2: gap analysis ─────────────────────────────────────────────────

    async def save_contract_gaps(self, document_id: str, missing_clauses: List[str]) -> None:
        """Persist missing clause detection result. Overwrites on re-analysis."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT OR REPLACE INTO contract_gaps
                    (document_id, missing_clauses_json, created_at)
                VALUES (?, ?, ?)
                """,
                (document_id, json.dumps(missing_clauses), datetime.utcnow().isoformat()),
            )
            conn.commit()
        except Exception as e:
            logger.error(f"Error saving gaps for {document_id}: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()

    async def get_contract_gaps(self, document_id: str) -> Optional[List[str]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT missing_clauses_json FROM contract_gaps WHERE document_id = ?",
                (document_id,),
            )
            row = cursor.fetchone()
            return json.loads(row["missing_clauses_json"]) if row else None
        except Exception as e:
            logger.error(f"Error retrieving gaps for {document_id}: {e}")
            return None
        finally:
            conn.close()


    # ── Quota helpers ──────────────────────────────────────────────────────

    async def get_user_document_count(self, user_id: str) -> int:
        """Return the number of documents owned by a user."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT COUNT(*) as cnt FROM contracts WHERE user_id = ?",
                (user_id,),
            )
            row = cursor.fetchone()
            return row["cnt"] if row else 0
        except Exception as e:
            logger.error(f"Error counting documents for {user_id}: {e}")
            return 0
        finally:
            conn.close()

    async def get_user_storage_usage(self, user_id: str) -> int:
        """Return total bytes used by a user (sum of file_size across contracts)."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT COALESCE(SUM(file_size), 0) as total FROM contracts WHERE user_id = ?",
                (user_id,),
            )
            row = cursor.fetchone()
            return row["total"] if row else 0
        except Exception as e:
            logger.error(f"Error computing storage usage for {user_id}: {e}")
            return 0
        finally:
            conn.close()

    async def delete_contract_cascade(self, contract_id: str) -> None:
        """Delete a contract and all related data from every table."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM contract_gaps WHERE document_id = ?", (contract_id,))
            cursor.execute("DELETE FROM contract_risks WHERE document_id = ?", (contract_id,))
            cursor.execute("DELETE FROM contract_summaries WHERE document_id = ?", (contract_id,))
            cursor.execute("DELETE FROM contract_entities WHERE document_id = ?", (contract_id,))
            cursor.execute("DELETE FROM document_chunks WHERE document_id = ?", (contract_id,))
            cursor.execute("DELETE FROM document_text WHERE document_id = ?", (contract_id,))
            cursor.execute("DELETE FROM contracts WHERE id = ?", (contract_id,))
            conn.commit()
            logger.info(f"Cascade-deleted contract {contract_id} and all related data")
        except Exception as e:
            logger.error(f"Error cascade-deleting contract {contract_id}: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()


# Global instance
database_service = DatabaseService()
