"""Pydantic models for Azure Compute resources."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

from .base_models import AzureResource, AzureSku


class VirtualMachineModel(AzureResource):
    """Azure Virtual Machine model."""
    vm_id: Optional[str] = None
    vm_size: Optional[str] = None
    os_type: Optional[str] = None
    os_disk: Dict[str, Any] = Field(default_factory=dict)
    data_disks: List[Dict[str, Any]] = Field(default_factory=list)
    network_interfaces: List[str] = Field(default_factory=list)
    availability_set_id: Optional[str] = None
    vm_scale_set_id: Optional[str] = None
    boot_diagnostics_enabled: bool = False
    admin_username: Optional[str] = None
    computer_name: Optional[str] = None
    platform_fault_domain: Optional[int] = None
    platform_update_domain: Optional[int] = None


class AvailabilitySetModel(AzureResource):
    """Azure Availability Set model."""
    platform_fault_domain_count: Optional[int] = None
    platform_update_domain_count: Optional[int] = None
    virtual_machines: List[str] = Field(default_factory=list)
    proximity_placement_group_id: Optional[str] = None
    managed: bool = True


class VMScaleSetModel(AzureResource):
    """Azure VM Scale Set model."""
    sku: Optional[AzureSku] = None
    capacity: Optional[int] = None
    upgrade_policy: Optional[str] = None
    overprovision: bool = True
    single_placement_group: bool = True
    platform_fault_domain_count: Optional[int] = None
    zone_balance: bool = False
    virtual_machine_profile: Dict[str, Any] = Field(default_factory=dict)
    identity: Optional[Dict[str, Any]] = None
    orchestration_mode: Optional[str] = None


class DiskModel(AzureResource):
    """Azure Managed Disk model."""
    disk_size_gb: Optional[int] = None
    disk_size_bytes: Optional[int] = None
    disk_state: Optional[str] = None
    os_type: Optional[str] = None
    creation_data: Dict[str, Any] = Field(default_factory=dict)
    disk_iops_read_write: Optional[int] = None
    disk_mbps_read_write: Optional[int] = None
    disk_iops_read_only: Optional[int] = None
    disk_mbps_read_only: Optional[int] = None
    encryption_settings_collection: Optional[Dict[str, Any]] = None
    network_access_policy: Optional[str] = None
    public_network_access: Optional[str] = None
    tier: Optional[str] = None
    max_shares: Optional[int] = None
    share_info: List[Dict[str, Any]] = Field(default_factory=list)


class ImageModel(AzureResource):
    """Azure Custom Image model."""
    source_virtual_machine_id: Optional[str] = None
    storage_profile: Dict[str, Any] = Field(default_factory=dict)
    hyper_v_generation: Optional[str] = None


class SnapshotModel(AzureResource):
    """Azure Disk Snapshot model."""
    disk_size_gb: Optional[int] = None
    disk_size_bytes: Optional[int] = None
    os_type: Optional[str] = None
    creation_data: Dict[str, Any] = Field(default_factory=dict)
    time_created: Optional[datetime] = None
    hyper_v_generation: Optional[str] = None
    incremental: bool = False
    encryption_settings_collection: Optional[Dict[str, Any]] = None
    network_access_policy: Optional[str] = None
    public_network_access: Optional[str] = None


class ComputeData(BaseModel):
    """Container for all Azure Compute service data."""
    virtual_machines: Dict[str, VirtualMachineModel] = Field(default_factory=dict)
    availability_sets: Dict[str, AvailabilitySetModel] = Field(default_factory=dict)
    vm_scale_sets: Dict[str, VMScaleSetModel] = Field(default_factory=dict)
    disks: Dict[str, DiskModel] = Field(default_factory=dict)
    images: Dict[str, ImageModel] = Field(default_factory=dict)
    snapshots: Dict[str, SnapshotModel] = Field(default_factory=dict)
    
    # Summary statistics
    total_vms: int = 0
    total_running_vms: int = 0
    total_stopped_vms: int = 0
    total_disks: int = 0
    total_disk_size_gb: int = 0
    total_snapshots: int = 0
    
    # Relationships
    vm_disk_relationships: Dict[str, List[str]] = Field(default_factory=dict)
    vm_availability_set_relationships: Dict[str, str] = Field(default_factory=dict)
    
    def calculate_statistics(self):
        """Calculate summary statistics from the collected data."""
        self.total_vms = len(self.virtual_machines)
        self.total_disks = len(self.disks)
        self.total_snapshots = len(self.snapshots)
        
        # Calculate running/stopped VMs
        self.total_running_vms = sum(
            1 for vm in self.virtual_machines.values() 
            if vm.provisioning_state == "Succeeded"
        )
        self.total_stopped_vms = self.total_vms - self.total_running_vms
        
        # Calculate total disk size
        self.total_disk_size_gb = sum(
            disk.disk_size_gb or 0 for disk in self.disks.values()
        ) 