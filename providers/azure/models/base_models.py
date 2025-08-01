"""Base Pydantic models for Azure provider data structures."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class AzureTag(BaseModel):
    """Azure resource tag."""
    key: str
    value: str


class AzureLocation(BaseModel):
    """Azure location/region information."""
    name: str
    display_name: Optional[str] = None


class AzureSku(BaseModel):
    """Azure SKU information."""
    name: str
    tier: Optional[str] = None
    size: Optional[str] = None
    family: Optional[str] = None
    capacity: Optional[int] = None


class AzureResourceReference(BaseModel):
    """Reference to another Azure resource."""
    id: str
    name: Optional[str] = None
    resource_type: Optional[str] = None


class ResourceGroup(BaseModel):
    """Azure Resource Group information."""
    id: str
    name: str
    location: str
    managed_by: Optional[str] = None
    provisioning_state: Optional[str] = None
    tags: Dict[str, str] = Field(default_factory=dict)


class AzureResource(BaseModel):
    """Base Azure resource model."""
    id: str
    name: str
    type: str
    location: str
    resource_group: Optional[str] = None
    provisioning_state: Optional[str] = None
    tags: Dict[str, str] = Field(default_factory=dict)
    created_time: Optional[datetime] = None
    changed_time: Optional[datetime] = None
    zones: Optional[List[str]] = None


class AzureNetworkProfile(BaseModel):
    """Azure network profile for resources."""
    network_interfaces: List[str] = Field(default_factory=list)
    
    
class AzureHardwareProfile(BaseModel):
    """Azure hardware profile for compute resources."""
    vm_size: Optional[str] = None


class AzureStorageProfile(BaseModel):
    """Azure storage profile for compute resources."""
    os_disk: Optional[Dict[str, Any]] = None
    data_disks: List[Dict[str, Any]] = Field(default_factory=list)
    image_reference: Optional[Dict[str, Any]] = None 