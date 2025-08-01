"""Azure provider Pydantic models for data structures."""

from .base_models import (
    AzureResource,
    ResourceGroup,
    AzureLocation,
    AzureSku,
    AzureTag,
    AzureResourceReference
)

from .compute_models import (
    ComputeData,
    VirtualMachineModel,
    AvailabilitySetModel,
    VMScaleSetModel,
    DiskModel,
    ImageModel,
    SnapshotModel
)

from .storage_models import (
    StorageData,
    StorageAccountModel,
    BlobContainerModel,
    FileShareModel
)

from .networking_models import (
    NetworkingData,
    VirtualNetworkModel,
    SubnetModel,
    NetworkSecurityGroupModel,
    NetworkInterfaceModel,
    PublicIPModel,
    LoadBalancerModel
)

from .identity_models import (
    IdentityData,
    RoleAssignmentModel,
    RoleDefinitionModel,
    ManagedIdentityModel
)

from .security_models import (
    SecurityData,
    KeyVaultModel,
    SecurityContactModel,
    SecurityAlertModel
)

from .report_models import (
    AzureReport
)

__all__ = [
    # Base models
    "AzureResource",
    "ResourceGroup", 
    "AzureLocation",
    "AzureSku",
    "AzureTag",
    "AzureResourceReference",
    
    # Service data models
    "ComputeData",
    "StorageData", 
    "NetworkingData",
    "IdentityData",
    "SecurityData",
    
    # Resource models
    "VirtualMachineModel",
    "AvailabilitySetModel",
    "VMScaleSetModel",
    "DiskModel",
    "ImageModel",
    "SnapshotModel",
    "StorageAccountModel",
    "BlobContainerModel",
    "FileShareModel",
    "VirtualNetworkModel",
    "SubnetModel",
    "NetworkSecurityGroupModel",
    "NetworkInterfaceModel",
    "PublicIPModel",
    "LoadBalancerModel",
    "RoleAssignmentModel",
    "RoleDefinitionModel",
    "ManagedIdentityModel",
    "KeyVaultModel",
    "SecurityContactModel",
    "SecurityAlertModel",
    
    # Main report
    "AzureReport"
] 