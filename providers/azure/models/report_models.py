"""Main Azure report Pydantic model."""

from datetime import datetime, timezone
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from .compute_models import ComputeData
from .storage_models import StorageData
from .networking_models import NetworkingData
from .identity_models import IdentityData
from .security_models import SecurityData
from .base_models import ResourceGroup


class AzureReport(BaseModel):
    """Complete Azure data collection report."""
    
    # Metadata
    collection_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    subscription_id: Optional[str] = None
    tenant_id: Optional[str] = None
    
    # Azure service data
    compute_data: ComputeData = Field(default_factory=ComputeData)
    storage_data: StorageData = Field(default_factory=StorageData)
    networking_data: NetworkingData = Field(default_factory=NetworkingData)
    identity_data: IdentityData = Field(default_factory=IdentityData)
    security_data: SecurityData = Field(default_factory=SecurityData)
    
    # Resource Groups
    resource_groups: Dict[str, ResourceGroup] = Field(default_factory=dict)
    
    # Overall statistics
    total_resources: int = 0
    total_resource_groups: int = 0
    
    # Collection metadata
    collection_duration_seconds: Optional[float] = None
    collection_errors: List[str] = Field(default_factory=list)
    api_call_count: int = 0
    
    def calculate_totals(self):
        """Calculate overall totals and statistics."""
        self.compute_data.calculate_statistics()
        self.storage_data.calculate_statistics()
        self.networking_data.calculate_statistics()
        self.identity_data.calculate_statistics()
        self.security_data.calculate_statistics()
        
        self.total_resource_groups = len(self.resource_groups)
        
        self.total_resources = (
            self.compute_data.total_vms +
            self.compute_data.total_disks +
            self.storage_data.total_storage_accounts +
            self.networking_data.total_vnets +
            self.identity_data.total_managed_identities +
            self.security_data.total_key_vaults
        )
    
    def get_summary(self) -> Dict:
        """Get a summary of the Azure environment."""
        return {
            "subscription_id": self.subscription_id,
            "collection_time": self.collection_time.isoformat(),
            "total_resources": self.total_resources,
            "total_resource_groups": self.total_resource_groups,
            "compute": {
                "virtual_machines": self.compute_data.total_vms,
                "storage_accounts": self.storage_data.total_storage_accounts,
                "virtual_networks": self.networking_data.total_vnets,
                "key_vaults": self.security_data.total_key_vaults,
            }
        } 