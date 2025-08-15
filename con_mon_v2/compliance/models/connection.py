"""
Connection model for con_mon_v2.

Represents external service connections (GitHub, AWS, Google Workspace, etc.)
that are used to collect resources for compliance checking.
"""
from enum import Enum
from typing import Optional, ClassVar, Dict, Any, Union
from datetime import datetime
from pydantic import Field, BaseModel as PydanticBaseModel, field_validator

from .base import TableModel


class ConnectionType(Enum):
    """Enumeration of supported connection types."""
    GITHUB = 1
    AWS = 2
    KUBERNETES = 3
    AZURE = 4
    VMWARE = 5
    GITLAB = 6
    TERRAFORM = 7
    MICROSOFT_365 = 8
    SLACK = 9
    GOOGLE = 10
    SPLUNK = 11
    CISCO = 12
    DATABASE = 13
    FILES = 14
    IDENTITY_SERVICES = 15
    FILE = 16


class SyncFrequencyType(Enum):
    """Enumeration of sync frequency types."""
    CRON = "cron"
    INTERVAL = "interval"
    MANUAL = "manual"


class SyncFrequency(PydanticBaseModel):
    """Sync frequency configuration."""
    type: SyncFrequencyType = Field(..., description="Sync frequency type")
    cron_expression: Optional[str] = Field(None, description="Cron expression for scheduled syncs")
    interval_minutes: Optional[int] = Field(None, description="Interval in minutes for regular syncs")
    
    @classmethod
    def from_dict(cls, data: Union[Dict[str, Any], None]) -> Optional['SyncFrequency']:
        """Create SyncFrequency from dictionary."""
        if not data:
            return None
            
        sync_type = SyncFrequencyType(data.get('type', 'manual'))
        return cls(
            type=sync_type,
            cron_expression=data.get('cron_expression'),
            interval_minutes=data.get('interval_minutes')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert SyncFrequency to dictionary."""
        result = {'type': self.type.value}
        if self.cron_expression:
            result['cron_expression'] = self.cron_expression
        if self.interval_minutes:
            result['interval_minutes'] = self.interval_minutes
        return result


class Connection(TableModel):
    """
    Connection model matching database schema exactly.
    
    Database table: connections
    Represents a connection to an external service for resource collection.
    """
    
    # Table configuration
    table_name: ClassVar[str] = "connections"
    
    # Database fields (exact 1:1 mapping)
    id: int = Field(..., description="Unique connection identifier")
    customer_id: str = Field(..., description="Customer/organization identifier")
    type: int = Field(..., description="Connection type ID (maps to ConnectionType enum)")
    credentials: Dict[str, Any] = Field(default_factory=dict, description="Service credentials (encrypted/secured)")
    
    # Audit fields
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    created_by: str = Field(..., description="User who created the connection")
    updated_by: str = Field(..., description="User who last updated the connection")
    
    # Sync fields
    synced_at: Optional[datetime] = Field(None, description="Last successful sync timestamp")
    sync_status: Optional[str] = Field(None, description="Current sync status")
    sync_error: Optional[str] = Field(None, description="Last sync error message")
    sync_frequency: Dict[str, Any] = Field(default_factory=dict, description="Sync frequency configuration JSONB")
    
    # Additional fields
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional connection metadata JSONB")
    is_deleted: bool = Field(False, description="Soft delete flag")
    info: Dict[str, Any] = Field(default_factory=dict, description="Additional connection information JSONB")
    alias: str = Field("", description="Human-readable connection name")
    
    @field_validator('alias', mode='before')
    @classmethod
    def validate_alias(cls, v):
        """Convert None alias to empty string."""
        return v if v is not None else ""
    
    @field_validator('sync_status', 'sync_error', mode='before')
    @classmethod
    def validate_optional_strings(cls, v):
        """Handle None values for optional string fields."""
        return v if v is not None else None
    
    @field_validator('credentials', 'metadata', 'info', 'sync_frequency', mode='before')
    @classmethod
    def validate_json_fields(cls, v):
        """Handle None values for JSON fields."""
        return v if v is not None else {}
    
    @property
    def connection_type(self) -> ConnectionType:
        """Get the ConnectionType enum from the type field."""
        return ConnectionType(self.type)

    @property
    def connector_type_str(self) -> str:
        """Get the ConnectionType enum from the type field."""
        return self.connection_type.name.lower()

    @property
    def type_name(self) -> str:
        """Get human-readable connection type name."""
        type_names = {
            ConnectionType.GITHUB: "GitHub",
            ConnectionType.AWS: "AWS",
            ConnectionType.KUBERNETES: "Kubernetes",
            ConnectionType.AZURE: "Azure",
            ConnectionType.VMWARE: "VMware",
            ConnectionType.GITLAB: "GitLab",
            ConnectionType.TERRAFORM: "Terraform",
            ConnectionType.MICROSOFT_365: "Microsoft 365",
            ConnectionType.SLACK: "Slack",
            ConnectionType.GOOGLE: "Google",
            ConnectionType.SPLUNK: "Splunk",
            ConnectionType.CISCO: "Cisco",
            ConnectionType.DATABASE: "Database",
            ConnectionType.FILES: "Files",
            ConnectionType.IDENTITY_SERVICES: "Identity Services",
            ConnectionType.FILE: "File"
        }
        return type_names.get(self.connection_type, f"Unknown ({self.type})")
    
    @property
    def display_name(self) -> str:
        """Get display name for the connection."""
        if self.alias:
            return f"{self.alias} ({self.type_name})"
        return f"{self.type_name} Connection #{self.id}"
    
    @property
    def is_active(self) -> bool:
        """Check if connection is active (not deleted)."""
        return not self.is_deleted
    
    @property
    def has_credentials(self) -> bool:
        """Check if connection has credentials configured."""
        return bool(self.credentials)
    
    @property
    def sync_frequency_obj(self) -> Optional[SyncFrequency]:
        """Get sync frequency as SyncFrequency object."""
        return SyncFrequency.from_dict(self.sync_frequency)
    
    def __str__(self) -> str:
        """String representation of the connection."""
        return f"Connection(id={self.id}, type={self.type_name}, customer={self.customer_id})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the connection."""
        return (f"Connection(id={self.id}, customer_id='{self.customer_id}', "
                f"type={self.type_name}, alias='{self.alias}', is_deleted={self.is_deleted})") 