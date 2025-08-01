"""Pydantic models for Azure Security resources."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

from .base_models import AzureResource, AzureSku


class AccessPolicyModel(BaseModel):
    """Azure Key Vault Access Policy model."""
    tenant_id: str
    object_id: str
    application_id: Optional[str] = None
    permissions: Dict[str, List[str]] = Field(default_factory=dict)


class KeyVaultModel(AzureResource):
    """Azure Key Vault model."""
    vault_uri: Optional[str] = None
    tenant_id: Optional[str] = None
    sku: Optional[AzureSku] = None
    
    # Access policies
    access_policies: List[AccessPolicyModel] = Field(default_factory=list)
    
    # Feature flags
    enabled_for_deployment: bool = False
    enabled_for_disk_encryption: bool = False
    enabled_for_template_deployment: bool = False
    
    # Soft delete and purge protection
    soft_delete_retention_in_days: Optional[int] = None
    purge_protection_enabled: bool = False
    
    # Network settings
    network_acl_default_action: Optional[str] = None  # Allow, Deny
    network_acl_bypass: Optional[str] = None  # AzureServices, None
    network_acl_virtual_network_rules: List[Dict[str, Any]] = Field(default_factory=list)
    network_acl_ip_rules: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Private endpoint connections
    private_endpoint_connections: List[Dict[str, Any]] = Field(default_factory=list)
    
    # RBAC authorization
    enable_rbac_authorization: bool = False
    
    # Create mode
    create_mode: Optional[str] = None  # default, recover


class KeyVaultKeyModel(BaseModel):
    """Azure Key Vault Key model."""
    id: str
    name: str
    key_vault_id: str
    key_type: Optional[str] = None  # EC, EC-HSM, RSA, RSA-HSM, oct, oct-HSM
    key_size: Optional[int] = None
    curve_name: Optional[str] = None
    
    # Properties
    enabled: bool = True
    expires_on: Optional[datetime] = None
    not_before: Optional[datetime] = None
    created_on: Optional[datetime] = None
    updated_on: Optional[datetime] = None
    recoverable_days: Optional[int] = None
    
    # Operations
    key_operations: List[str] = Field(default_factory=list)
    
    # Tags
    tags: Dict[str, str] = Field(default_factory=dict)


class KeyVaultSecretModel(BaseModel):
    """Azure Key Vault Secret model."""
    id: str
    name: str
    key_vault_id: str
    content_type: Optional[str] = None
    
    # Properties
    enabled: bool = True
    expires_on: Optional[datetime] = None
    not_before: Optional[datetime] = None
    created_on: Optional[datetime] = None
    updated_on: Optional[datetime] = None
    recoverable_days: Optional[int] = None
    
    # Tags
    tags: Dict[str, str] = Field(default_factory=dict)


class KeyVaultCertificateModel(BaseModel):
    """Azure Key Vault Certificate model."""
    id: str
    name: str
    key_vault_id: str
    
    # Certificate properties
    enabled: bool = True
    expires_on: Optional[datetime] = None
    not_before: Optional[datetime] = None
    created_on: Optional[datetime] = None
    updated_on: Optional[datetime] = None
    recoverable_days: Optional[int] = None
    
    # Certificate policy
    certificate_policy: Dict[str, Any] = Field(default_factory=dict)
    
    # Tags
    tags: Dict[str, str] = Field(default_factory=dict)


class SecurityContactModel(BaseModel):
    """Azure Security Center Contact model."""
    name: str
    id: str
    type: str
    email: Optional[str] = None
    phone: Optional[str] = None
    alert_notifications: Optional[str] = None  # On, Off
    alerts_to_admins: Optional[str] = None  # On, Off


class SecurityAlertModel(BaseModel):
    """Azure Security Center Alert model."""
    name: str
    id: str
    type: str
    state: Optional[str] = None  # Active, Dismissed, InProgress, Resolved
    report_time: Optional[datetime] = None
    vendor_name: Optional[str] = None
    alert_name: Optional[str] = None
    alert_display_name: Optional[str] = None
    detected_time: Optional[datetime] = None
    description: Optional[str] = None
    remediation_steps: Optional[str] = None
    action_taken: Optional[str] = None
    confidence_score: Optional[float] = None
    severity: Optional[str] = None  # High, Medium, Low, Informational
    
    # Entities involved in the alert
    entities: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Extended properties
    extended_properties: Dict[str, str] = Field(default_factory=dict)
    
    # Compromise intent
    intent: Optional[str] = None
    
    # Kill chain intent
    kill_chain_intent: Optional[str] = None
    
    # Associated resource
    compromised_entity: Optional[str] = None


class SecurityTaskModel(BaseModel):
    """Azure Security Center Task model."""
    name: str
    id: str
    type: str
    state: Optional[str] = None  # Active, Completed, Dismissed
    sub_state: Optional[str] = None
    creation_time: Optional[datetime] = None
    last_state_change_time: Optional[datetime] = None
    
    # Task details
    security_task_parameters: Dict[str, Any] = Field(default_factory=dict)


class SecurityAssessmentModel(BaseModel):
    """Azure Security Center Assessment model."""
    name: str
    id: str
    type: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    remediation_description: Optional[str] = None
    
    # Assessment status
    status: Dict[str, Any] = Field(default_factory=dict)
    
    # Resource details
    resource_details: Dict[str, Any] = Field(default_factory=dict)
    
    # Additional data
    additional_data: Dict[str, Any] = Field(default_factory=dict)
    
    # Links
    links: Dict[str, Any] = Field(default_factory=dict)


class SecurityData(BaseModel):
    """Container for all Azure Security service data."""
    key_vaults: Dict[str, KeyVaultModel] = Field(default_factory=dict)
    key_vault_keys: Dict[str, KeyVaultKeyModel] = Field(default_factory=dict)
    key_vault_secrets: Dict[str, KeyVaultSecretModel] = Field(default_factory=dict)
    key_vault_certificates: Dict[str, KeyVaultCertificateModel] = Field(default_factory=dict)
    security_contacts: Dict[str, SecurityContactModel] = Field(default_factory=dict)
    security_alerts: Dict[str, SecurityAlertModel] = Field(default_factory=dict)
    security_tasks: Dict[str, SecurityTaskModel] = Field(default_factory=dict)
    security_assessments: Dict[str, SecurityAssessmentModel] = Field(default_factory=dict)
    
    # Summary statistics
    total_key_vaults: int = 0
    total_keys: int = 0
    total_secrets: int = 0
    total_certificates: int = 0
    total_security_alerts: int = 0
    total_security_tasks: int = 0
    total_security_assessments: int = 0
    
    # Key Vault security statistics
    key_vaults_with_purge_protection: int = 0
    key_vaults_with_soft_delete: int = 0
    key_vaults_with_rbac_enabled: int = 0
    key_vaults_with_private_endpoints: int = 0
    key_vaults_with_network_restrictions: int = 0
    
    # Security alert statistics
    high_severity_alerts: int = 0
    medium_severity_alerts: int = 0
    low_severity_alerts: int = 0
    active_alerts: int = 0
    dismissed_alerts: int = 0
    
    def calculate_statistics(self):
        """Calculate summary statistics from the collected data."""
        self.total_key_vaults = len(self.key_vaults)
        self.total_keys = len(self.key_vault_keys)
        self.total_secrets = len(self.key_vault_secrets)
        self.total_certificates = len(self.key_vault_certificates)
        self.total_security_alerts = len(self.security_alerts)
        self.total_security_tasks = len(self.security_tasks)
        self.total_security_assessments = len(self.security_assessments)
        
        # Calculate Key Vault security statistics
        self.key_vaults_with_purge_protection = sum(
            1 for kv in self.key_vaults.values()
            if kv.purge_protection_enabled
        )
        
        self.key_vaults_with_soft_delete = sum(
            1 for kv in self.key_vaults.values()
            if kv.soft_delete_retention_in_days is not None and kv.soft_delete_retention_in_days > 0
        )
        
        self.key_vaults_with_rbac_enabled = sum(
            1 for kv in self.key_vaults.values()
            if kv.enable_rbac_authorization
        )
        
        self.key_vaults_with_private_endpoints = sum(
            1 for kv in self.key_vaults.values()
            if len(kv.private_endpoint_connections) > 0
        )
        
        self.key_vaults_with_network_restrictions = sum(
            1 for kv in self.key_vaults.values()
            if kv.network_acl_default_action == "Deny"
        )
        
        # Calculate security alert statistics
        self.high_severity_alerts = sum(
            1 for alert in self.security_alerts.values()
            if alert.severity == "High"
        )
        
        self.medium_severity_alerts = sum(
            1 for alert in self.security_alerts.values()
            if alert.severity == "Medium"
        )
        
        self.low_severity_alerts = sum(
            1 for alert in self.security_alerts.values()
            if alert.severity == "Low"
        )
        
        self.active_alerts = sum(
            1 for alert in self.security_alerts.values()
            if alert.state == "Active"
        )
        
        self.dismissed_alerts = sum(
            1 for alert in self.security_alerts.values()
            if alert.state == "Dismissed"
        ) 