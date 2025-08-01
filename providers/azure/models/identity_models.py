"""Pydantic models for Azure Identity and Access Management resources."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

from .base_models import AzureResource


class RoleAssignmentModel(BaseModel):
    """Azure Role Assignment model."""
    id: str
    name: str
    type: str
    scope: str
    role_definition_id: str
    principal_id: str
    principal_type: Optional[str] = None  # User, Group, ServicePrincipal, etc.
    
    # Timestamps
    created_on: Optional[datetime] = None
    updated_on: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    
    # Conditions
    condition: Optional[str] = None
    condition_version: Optional[str] = None
    
    # Description
    description: Optional[str] = None
    
    # Delegation
    delegated_managed_identity_resource_id: Optional[str] = None


class PermissionModel(BaseModel):
    """Azure Role Permission model."""
    actions: List[str] = Field(default_factory=list)
    not_actions: List[str] = Field(default_factory=list)
    data_actions: List[str] = Field(default_factory=list)
    not_data_actions: List[str] = Field(default_factory=list)


class RoleDefinitionModel(BaseModel):
    """Azure Role Definition model."""
    id: str
    name: str
    type: str
    role_name: str
    description: Optional[str] = None
    role_type: Optional[str] = None  # BuiltInRole, CustomRole
    
    # Permissions
    permissions: List[PermissionModel] = Field(default_factory=list)
    
    # Assignable scopes
    assignable_scopes: List[str] = Field(default_factory=list)
    
    # Timestamps
    created_on: Optional[datetime] = None
    updated_on: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None


class ManagedIdentityModel(AzureResource):
    """Azure Managed Identity model."""
    principal_id: Optional[str] = None
    client_id: Optional[str] = None
    tenant_id: Optional[str] = None
    
    # Identity type (SystemAssigned, UserAssigned)
    identity_type: Optional[str] = None
    
    # Associated resource (for system-assigned identities)
    associated_resource_id: Optional[str] = None


class ServicePrincipalModel(BaseModel):
    """Azure Service Principal model."""
    id: str
    app_id: str
    display_name: str
    service_principal_type: Optional[str] = None
    
    # Authentication
    password_credentials: List[Dict[str, Any]] = Field(default_factory=list)
    key_credentials: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Properties
    account_enabled: bool = True
    app_display_name: Optional[str] = None
    app_owner_organization_id: Optional[str] = None
    
    # Tags
    tags: List[str] = Field(default_factory=list)
    
    # Alternative names
    alternative_names: List[str] = Field(default_factory=list)
    
    # App roles
    app_roles: List[Dict[str, Any]] = Field(default_factory=list)
    
    # OAuth2 permissions
    oauth2_permissions: List[Dict[str, Any]] = Field(default_factory=list)


class GroupModel(BaseModel):
    """Azure AD Group model."""
    id: str
    display_name: str
    description: Optional[str] = None
    group_types: List[str] = Field(default_factory=list)
    mail: Optional[str] = None
    mail_enabled: bool = False
    mail_nickname: Optional[str] = None
    security_enabled: bool = True
    
    # Membership
    members: List[str] = Field(default_factory=list)
    owners: List[str] = Field(default_factory=list)


class UserModel(BaseModel):
    """Azure AD User model."""
    id: str
    user_principal_name: str
    display_name: str
    given_name: Optional[str] = None
    surname: Optional[str] = None
    mail: Optional[str] = None
    
    # Account properties
    account_enabled: bool = True
    user_type: Optional[str] = None  # Member, Guest
    
    # Authentication
    password_profile: Optional[Dict[str, Any]] = None
    
    # License and usage
    assigned_licenses: List[Dict[str, Any]] = Field(default_factory=list)
    usage_location: Optional[str] = None
    
    # Department and job info
    department: Optional[str] = None
    job_title: Optional[str] = None
    office_location: Optional[str] = None


class IdentityData(BaseModel):
    """Container for all Azure Identity service data."""
    role_assignments: Dict[str, RoleAssignmentModel] = Field(default_factory=dict)
    role_definitions: Dict[str, RoleDefinitionModel] = Field(default_factory=dict)
    managed_identities: Dict[str, ManagedIdentityModel] = Field(default_factory=dict)
    service_principals: Dict[str, ServicePrincipalModel] = Field(default_factory=dict)
    groups: Dict[str, GroupModel] = Field(default_factory=dict)
    users: Dict[str, UserModel] = Field(default_factory=dict)
    
    # Summary statistics
    total_role_assignments: int = 0
    total_custom_roles: int = 0
    total_builtin_roles: int = 0
    total_managed_identities: int = 0
    total_service_principals: int = 0
    total_groups: int = 0
    total_users: int = 0
    
    # Identity statistics
    system_assigned_identities: int = 0
    user_assigned_identities: int = 0
    
    # Role assignment statistics by principal type
    user_role_assignments: int = 0
    group_role_assignments: int = 0
    service_principal_role_assignments: int = 0
    
    def calculate_statistics(self):
        """Calculate summary statistics from the collected data."""
        self.total_role_assignments = len(self.role_assignments)
        self.total_managed_identities = len(self.managed_identities)
        self.total_service_principals = len(self.service_principals)
        self.total_groups = len(self.groups)
        self.total_users = len(self.users)
        
        # Calculate role definition statistics
        self.total_custom_roles = sum(
            1 for role in self.role_definitions.values()
            if role.role_type == "CustomRole"
        )
        self.total_builtin_roles = sum(
            1 for role in self.role_definitions.values()
            if role.role_type == "BuiltInRole"
        )
        
        # Calculate managed identity statistics
        self.system_assigned_identities = sum(
            1 for identity in self.managed_identities.values()
            if identity.identity_type == "SystemAssigned"
        )
        self.user_assigned_identities = sum(
            1 for identity in self.managed_identities.values()
            if identity.identity_type == "UserAssigned"
        )
        
        # Calculate role assignment statistics by principal type
        self.user_role_assignments = sum(
            1 for assignment in self.role_assignments.values()
            if assignment.principal_type == "User"
        )
        self.group_role_assignments = sum(
            1 for assignment in self.role_assignments.values()
            if assignment.principal_type == "Group"
        )
        self.service_principal_role_assignments = sum(
            1 for assignment in self.role_assignments.values()
            if assignment.principal_type == "ServicePrincipal"
        ) 