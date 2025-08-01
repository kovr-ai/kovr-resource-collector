"""Pydantic models for Azure Storage resources."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

from .base_models import AzureResource, AzureSku


class StorageAccountModel(AzureResource):
    """Azure Storage Account model."""
    kind: Optional[str] = None  # Storage, StorageV2, BlobStorage, etc.
    sku: Optional[AzureSku] = None
    access_tier: Optional[str] = None  # Hot, Cool, Archive
    creation_time: Optional[datetime] = None
    primary_location: Optional[str] = None
    secondary_location: Optional[str] = None
    status_of_primary: Optional[str] = None
    status_of_secondary: Optional[str] = None
    last_geo_failure_time: Optional[datetime] = None
    
    # Security and access settings
    enable_https_traffic_only: bool = True
    allow_blob_public_access: bool = False
    allow_shared_key_access: bool = True
    allow_cross_tenant_replication: bool = True
    minimum_tls_version: Optional[str] = None
    
    # Network settings
    network_rule_set: Dict[str, Any] = Field(default_factory=dict)
    
    # Encryption settings
    encryption: Dict[str, Any] = Field(default_factory=dict)
    
    # Blob properties
    blob_restore_status: Optional[Dict[str, Any]] = None
    is_nfs_v3_enabled: bool = False
    is_sftp_enabled: bool = False
    
    # Identity
    identity: Optional[Dict[str, Any]] = None
    
    # Key policy
    key_policy: Optional[Dict[str, Any]] = None
    
    # Primary and secondary endpoints
    primary_endpoints: Dict[str, str] = Field(default_factory=dict)
    secondary_endpoints: Dict[str, str] = Field(default_factory=dict)


class BlobContainerModel(BaseModel):
    """Azure Blob Container model."""
    id: str
    name: str
    storage_account_id: str
    public_access: Optional[str] = None  # None, Blob, Container
    last_modified_time: Optional[datetime] = None
    lease_status: Optional[str] = None
    lease_state: Optional[str] = None
    lease_duration: Optional[str] = None
    metadata: Dict[str, str] = Field(default_factory=dict)
    deleted: bool = False
    deleted_time: Optional[datetime] = None
    remaining_retention_days: Optional[int] = None
    default_encryption_scope: Optional[str] = None
    prevent_encryption_scope_override: bool = False
    
    # Container properties
    has_immutability_policy: bool = False
    has_legal_hold: bool = False
    immutable_storage_with_versioning_enabled: bool = False


class FileShareModel(BaseModel):
    """Azure File Share model."""
    id: str
    name: str
    storage_account_id: str
    share_quota: Optional[int] = None  # In GB
    share_usage_bytes: Optional[int] = None
    enabled_protocols: Optional[str] = None  # SMB, NFS
    root_squash: Optional[str] = None
    access_tier: Optional[str] = None  # TransactionOptimized, Hot, Cool, Premium
    
    # Timestamps
    last_modified_time: Optional[datetime] = None
    
    # Metadata
    metadata: Dict[str, str] = Field(default_factory=dict)
    
    # Snapshot info
    snapshot_time: Optional[datetime] = None
    share_usage_bytes: Optional[int] = None
    
    # Backup and versioning
    deleted: bool = False
    deleted_time: Optional[datetime] = None
    remaining_retention_days: Optional[int] = None


class QueueModel(BaseModel):
    """Azure Storage Queue model."""
    id: str
    name: str
    storage_account_id: str
    metadata: Dict[str, str] = Field(default_factory=dict)
    approximate_message_count: int = 0


class TableModel(BaseModel):
    """Azure Storage Table model."""
    id: str
    name: str
    storage_account_id: str
    table_name: str
    
    
class StorageData(BaseModel):
    """Container for all Azure Storage service data."""
    storage_accounts: Dict[str, StorageAccountModel] = Field(default_factory=dict)
    blob_containers: Dict[str, BlobContainerModel] = Field(default_factory=dict)
    file_shares: Dict[str, FileShareModel] = Field(default_factory=dict) 
    queues: Dict[str, QueueModel] = Field(default_factory=dict)
    tables: Dict[str, TableModel] = Field(default_factory=dict)
    
    # Summary statistics
    total_storage_accounts: int = 0
    total_blob_containers: int = 0
    total_file_shares: int = 0
    total_queues: int = 0
    total_tables: int = 0
    
    # Storage account statistics by type
    storage_v2_accounts: int = 0
    blob_storage_accounts: int = 0
    file_storage_accounts: int = 0
    
    # Security statistics
    accounts_with_https_only: int = 0
    accounts_with_public_blob_access_disabled: int = 0
    accounts_with_minimum_tls_v12: int = 0
    
    def calculate_statistics(self):
        """Calculate summary statistics from the collected data."""
        self.total_storage_accounts = len(self.storage_accounts)
        self.total_blob_containers = len(self.blob_containers)
        self.total_file_shares = len(self.file_shares)
        self.total_queues = len(self.queues)
        self.total_tables = len(self.tables)
        
        # Calculate storage account types
        self.storage_v2_accounts = sum(
            1 for acc in self.storage_accounts.values()
            if acc.kind == "StorageV2"
        )
        self.blob_storage_accounts = sum(
            1 for acc in self.storage_accounts.values()
            if acc.kind == "BlobStorage"
        )
        self.file_storage_accounts = sum(
            1 for acc in self.storage_accounts.values()
            if acc.kind == "FileStorage"
        )
        
        # Calculate security statistics
        self.accounts_with_https_only = sum(
            1 for acc in self.storage_accounts.values()
            if acc.enable_https_traffic_only
        )
        self.accounts_with_public_blob_access_disabled = sum(
            1 for acc in self.storage_accounts.values()
            if not acc.allow_blob_public_access
        )
        self.accounts_with_minimum_tls_v12 = sum(
            1 for acc in self.storage_accounts.values()
            if acc.minimum_tls_version in ["TLS1_2", "TLS1_3"]
        ) 