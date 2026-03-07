"""
Database service for Azure Cosmos DB
"""
from azure.cosmos import CosmosClient, exceptions
from azure.cosmos.partition_key import PartitionKey
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from app.core.config import settings
from app.models.schemas import ContractStatus, RiskLevel, Language

logger = logging.getLogger(__name__)


class DatabaseService:
    """Service for managing data in Azure Cosmos DB"""
    
    def __init__(self):
        self.endpoint = settings.COSMOS_ENDPOINT
        self.key = settings.COSMOS_KEY
        self.database_name = settings.COSMOS_DATABASE_NAME
        self.client = None
        self.database = None
        self.contracts_container = None
        self.users_container = None
        self.audit_container = None
        
        # In-memory storage for development (fallback)
        self.mock_contracts = {}
        self.mock_audit_logs = []
        
        if self.endpoint and self.key:
            try:
                self.client = CosmosClient(self.endpoint, self.key)
                self._initialize_database()
            except Exception as e:
                logger.warning(f"Failed to initialize Cosmos DB: {e}")
                logger.warning("Using in-memory storage")
    
    def _initialize_database(self):
        """Initialize database and containers"""
        try:
            # Create database if not exists
            self.database = self.client.create_database_if_not_exists(
                id=self.database_name
            )
            
            # Create containers
            self.contracts_container = self.database.create_container_if_not_exists(
                id="contracts",
                partition_key=PartitionKey(path="/user_id"),
                offer_throughput=400
            )
            
            self.users_container = self.database.create_container_if_not_exists(
                id="users",
                partition_key=PartitionKey(path="/id"),
                offer_throughput=400
            )
            
            self.audit_container = self.database.create_container_if_not_exists(
                id="audit_logs",
                partition_key=PartitionKey(path="/user_id"),
                offer_throughput=400
            )
            
            logger.info("Cosmos DB initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    async def create_contract(
        self,
        user_id: str,
        filename: str,
        blob_url: str,
        language: Language,
        industry: Optional[str] = None
    ) -> str:
        """Create a new contract record"""
        contract_id = str(uuid.uuid4())
        
        contract = {
            "id": contract_id,
            "user_id": user_id,
            "filename": filename,
            "blob_url": blob_url,
            "upload_date": datetime.utcnow().isoformat(),
            "status": ContractStatus.UPLOADED.value,
            "language": language.value,
            "industry": industry,
            "extracted_data": None,
            "analysis": None
        }
        
        if self.contracts_container:
            try:
                self.contracts_container.create_item(body=contract)
            except exceptions.CosmosHttpResponseError as e:
                logger.error(f"Error creating contract in Cosmos DB: {e}")
                raise
        else:
            # In-memory fallback
            self.mock_contracts[contract_id] = contract
        
        logger.info(f"Created contract: {contract_id}")
        return contract_id
    
    async def get_contract(self, contract_id: str, user_id: str) -> Optional[Dict]:
        """Get a contract by ID"""
        if self.contracts_container:
            try:
                contract = self.contracts_container.read_item(
                    item=contract_id,
                    partition_key=user_id
                )
                return contract
            except exceptions.CosmosResourceNotFoundError:
                return None
            except exceptions.CosmosHttpResponseError as e:
                logger.error(f"Error reading contract: {e}")
                return None
        else:
            # In-memory fallback
            contract = self.mock_contracts.get(contract_id)
            if contract and contract["user_id"] == user_id:
                return contract
            return None
    
    async def update_contract_status(self, contract_id: str, status: ContractStatus):
        """Update contract status"""
        if self.contracts_container:
            try:
                # Read the contract first
                contracts = list(self.contracts_container.query_items(
                    query="SELECT * FROM c WHERE c.id = @id",
                    parameters=[{"name": "@id", "value": contract_id}],
                    enable_cross_partition_query=True
                ))
                
                if contracts:
                    contract = contracts[0]
                    contract["status"] = status.value
                    self.contracts_container.upsert_item(contract)
            except Exception as e:
                logger.error(f"Error updating contract status: {e}")
        else:
            if contract_id in self.mock_contracts:
                self.mock_contracts[contract_id]["status"] = status.value
    
    async def update_contract_analysis(self, contract_id: str, analysis_result: Dict):
        """Update contract with analysis results"""
        if self.contracts_container:
            try:
                contracts = list(self.contracts_container.query_items(
                    query="SELECT * FROM c WHERE c.id = @id",
                    parameters=[{"name": "@id", "value": contract_id}],
                    enable_cross_partition_query=True
                ))
                
                if contracts:
                    contract = contracts[0]
                    contract["extracted_data"] = analysis_result.get("extracted_data")
                    contract["analysis"] = analysis_result.get("analysis")
                    self.contracts_container.upsert_item(contract)
            except Exception as e:
                logger.error(f"Error updating contract analysis: {e}")
        else:
            if contract_id in self.mock_contracts:
                self.mock_contracts[contract_id].update(analysis_result)
    
    async def list_contracts(
        self,
        user_id: str,
        status: Optional[ContractStatus] = None,
        limit: int = 50
    ) -> List[Dict]:
        """List contracts for a user"""
        if self.contracts_container:
            try:
                query = "SELECT * FROM c WHERE c.user_id = @user_id"
                parameters = [{"name": "@user_id", "value": user_id}]
                
                if status:
                    query += " AND c.status = @status"
                    parameters.append({"name": "@status", "value": status.value})
                
                query += " ORDER BY c.upload_date DESC"
                
                contracts = list(self.contracts_container.query_items(
                    query=query,
                    parameters=parameters,
                    max_item_count=limit
                ))
                
                return contracts
            except Exception as e:
                logger.error(f"Error listing contracts: {e}")
                return []
        else:
            # In-memory fallback
            contracts = [
                c for c in self.mock_contracts.values()
                if c["user_id"] == user_id and (not status or c["status"] == status.value)
            ]
            return sorted(contracts, key=lambda x: x["upload_date"], reverse=True)[:limit]
    
    async def delete_contract(self, contract_id: str):
        """Delete a contract"""
        if self.contracts_container:
            try:
                contracts = list(self.contracts_container.query_items(
                    query="SELECT * FROM c WHERE c.id = @id",
                    parameters=[{"name": "@id", "value": contract_id}],
                    enable_cross_partition_query=True
                ))
                
                if contracts:
                    contract = contracts[0]
                    self.contracts_container.delete_item(
                        item=contract_id,
                        partition_key=contract["user_id"]
                    )
            except Exception as e:
                logger.error(f"Error deleting contract: {e}")
        else:
            if contract_id in self.mock_contracts:
                del self.mock_contracts[contract_id]
    
    async def create_audit_log(
        self,
        user_id: str,
        action: str,
        contract_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """Create an audit log entry"""
        log_entry = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "action": action,
            "contract_id": contract_id,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        
        if self.audit_container:
            try:
                self.audit_container.create_item(body=log_entry)
            except Exception as e:
                logger.error(f"Error creating audit log: {e}")
        else:
            self.mock_audit_logs.append(log_entry)
    
    async def get_audit_logs(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Get audit logs for a user"""
        if self.audit_container:
            try:
                logs = list(self.audit_container.query_items(
                    query="SELECT * FROM c WHERE c.user_id = @user_id ORDER BY c.timestamp DESC",
                    parameters=[{"name": "@user_id", "value": user_id}],
                    max_item_count=limit
                ))
                return logs
            except Exception as e:
                logger.error(f"Error retrieving audit logs: {e}")
                return []
        else:
            logs = [log for log in self.mock_audit_logs if log["user_id"] == user_id]
            return sorted(logs, key=lambda x: x["timestamp"], reverse=True)[:limit]
    
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
