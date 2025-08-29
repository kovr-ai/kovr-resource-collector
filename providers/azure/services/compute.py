from providers.service import BaseService, service_class
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.resource import ResourceManagementClient


@service_class
class ComputeService(BaseService):
    def __init__(self, credential, subscription_id):
        super().__init__(credential)
        self.subscription_id = subscription_id
        self.compute_client = ComputeManagementClient(credential, subscription_id)
        self.resource_client = ResourceManagementClient(credential, subscription_id)

    def process(self):
        data = {
            "virtual_machines": {},
            "availability_sets": {},
            "vm_scale_sets": {},
            "disks": {},
            "images": {},
            "snapshots": {},
            "quotas": {},
            "relationships": {
                "vm_disks": {},
                "vm_availability_sets": {},
                "vm_resource_groups": {}
            }
        }

        try:
            # Get Virtual Machines
            print("Collecting Virtual Machines...")
            vms = self.compute_client.virtual_machines.list_all()
            for vm in vms:
                vm_dict = self._vm_to_dict(vm)
                data["virtual_machines"][vm.id] = vm_dict
                print(f"Found VM: {vm.name}")

        except Exception as e:
            print(f"Error collecting Virtual Machines: {str(e)}")
            data["virtual_machines"] = {}

        try:
            # Get Availability Sets
            print("Collecting Availability Sets...")
            availability_sets = self.compute_client.availability_sets.list_all()
            for av_set in availability_sets:
                av_set_dict = self._availability_set_to_dict(av_set)
                data["availability_sets"][av_set.id] = av_set_dict
                print(f"Found Availability Set: {av_set.name}")

        except Exception as e:
            print(f"Error collecting Availability Sets: {str(e)}")
            data["availability_sets"] = {}

        try:
            # Get VM Scale Sets
            print("Collecting VM Scale Sets...")
            scale_sets = self.compute_client.virtual_machine_scale_sets.list_all()
            for scale_set in scale_sets:
                scale_set_dict = self._scale_set_to_dict(scale_set)
                data["vm_scale_sets"][scale_set.id] = scale_set_dict
                print(f"Found VM Scale Set: {scale_set.name}")

        except Exception as e:
            print(f"Error collecting VM Scale Sets: {str(e)}")
            data["vm_scale_sets"] = {}

        try:
            # Get Managed Disks
            print("Collecting Managed Disks...")
            disks = self.compute_client.disks.list()
            for disk in disks:
                disk_dict = self._disk_to_dict(disk)
                data["disks"][disk.id] = disk_dict
                print(f"Found Disk: {disk.name}")

        except Exception as e:
            print(f"Error collecting Managed Disks: {str(e)}")
            data["disks"] = {}

        try:
            # Get Images
            print("Collecting Images...")
            images = self.compute_client.images.list()
            for image in images:
                image_dict = self._image_to_dict(image)
                data["images"][image.id] = image_dict
                print(f"Found Image: {image.name}")

        except Exception as e:
            print(f"Error collecting Images: {str(e)}")
            data["images"] = {}

        try:
            # Get Snapshots
            print("Collecting Snapshots...")
            snapshots = self.compute_client.snapshots.list()
            for snapshot in snapshots:
                snapshot_dict = self._snapshot_to_dict(snapshot)
                data["snapshots"][snapshot.id] = snapshot_dict
                print(f"Found Snapshot: {snapshot.name}")

        except Exception as e:
            print(f"Error collecting Snapshots: {str(e)}")
            data["snapshots"] = {}

        return data

    def _vm_to_dict(self, vm):
        """Convert VM object to dictionary"""
        return {
            "id": vm.id,
            "name": vm.name,
            "location": vm.location,
            "resource_group": vm.id.split('/')[4] if len(vm.id.split('/')) > 4 else None,
            "vm_size": vm.hardware_profile.vm_size if vm.hardware_profile else None,
            "provisioning_state": vm.provisioning_state,
            "vm_id": vm.vm_id,
            "os_type": vm.storage_profile.os_disk.os_type if vm.storage_profile and vm.storage_profile.os_disk else None,
            "os_disk": {
                "name": vm.storage_profile.os_disk.name if vm.storage_profile and vm.storage_profile.os_disk else None,
                "disk_size_gb": vm.storage_profile.os_disk.disk_size_gb if vm.storage_profile and vm.storage_profile.os_disk else None,
                "managed_disk_id": vm.storage_profile.os_disk.managed_disk.id if vm.storage_profile and vm.storage_profile.os_disk and vm.storage_profile.os_disk.managed_disk else None,
            },
            "data_disks": [
                {
                    "name": disk.name,
                    "disk_size_gb": disk.disk_size_gb,
                    "lun": disk.lun,
                    "managed_disk_id": disk.managed_disk.id if disk.managed_disk else None,
                }
                for disk in (vm.storage_profile.data_disks or []) if vm.storage_profile
            ],
            "network_interfaces": [ni.id for ni in (vm.network_profile.network_interfaces or [])] if vm.network_profile else [],
            "tags": dict(vm.tags) if vm.tags else {},
            "zones": vm.zones,
        }

    def _availability_set_to_dict(self, av_set):
        """Convert Availability Set object to dictionary"""
        return {
            "id": av_set.id,
            "name": av_set.name,
            "location": av_set.location,
            "resource_group": av_set.id.split('/')[4] if len(av_set.id.split('/')) > 4 else None,
            "platform_fault_domain_count": av_set.platform_fault_domain_count,
            "platform_update_domain_count": av_set.platform_update_domain_count,
            "virtual_machines": [vm.id for vm in (av_set.virtual_machines or [])],
            "tags": dict(av_set.tags) if av_set.tags else {},
        }

    def _scale_set_to_dict(self, scale_set):
        """Convert VM Scale Set object to dictionary"""
        return {
            "id": scale_set.id,
            "name": scale_set.name,
            "location": scale_set.location,
            "resource_group": scale_set.id.split('/')[4] if len(scale_set.id.split('/')) > 4 else None,
            "sku": {
                "name": scale_set.sku.name if scale_set.sku else None,
                "capacity": scale_set.sku.capacity if scale_set.sku else None,
            },
            "provisioning_state": scale_set.provisioning_state,
            "upgrade_policy": scale_set.upgrade_policy.mode if scale_set.upgrade_policy else None,
            "tags": dict(scale_set.tags) if scale_set.tags else {},
            "zones": scale_set.zones,
        }

    def _disk_to_dict(self, disk):
        """Convert Disk object to dictionary"""
        return {
            "id": disk.id,
            "name": disk.name,
            "location": disk.location,
            "resource_group": disk.id.split('/')[4] if len(disk.id.split('/')) > 4 else None,
            "disk_size_gb": disk.disk_size_gb,
            "disk_state": disk.disk_state,
            "os_type": disk.os_type,
            "provisioning_state": disk.provisioning_state,
            "disk_iops_read_write": disk.disk_iops_read_write,
            "disk_mbps_read_write": disk.disk_mbps_read_write,
            "tags": dict(disk.tags) if disk.tags else {},
            "zones": disk.zones,
        }

    def _image_to_dict(self, image):
        """Convert Image object to dictionary"""
        return {
            "id": image.id,
            "name": image.name,
            "location": image.location,
            "resource_group": image.id.split('/')[4] if len(image.id.split('/')) > 4 else None,
            "provisioning_state": image.provisioning_state,
            "tags": dict(image.tags) if image.tags else {},
        }

    def _snapshot_to_dict(self, snapshot):
        """Convert Snapshot object to dictionary"""
        return {
            "id": snapshot.id,
            "name": snapshot.name,
            "location": snapshot.location,
            "resource_group": snapshot.id.split('/')[4] if len(snapshot.id.split('/')) > 4 else None,
            "disk_size_gb": snapshot.disk_size_gb,
            "os_type": snapshot.os_type,
            "provisioning_state": snapshot.provisioning_state,
            "time_created": snapshot.time_created.isoformat() if snapshot.time_created else None,
            "tags": dict(snapshot.tags) if snapshot.tags else {},
        } 