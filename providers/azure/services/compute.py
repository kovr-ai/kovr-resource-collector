from providers.service import BaseService, service_class
import uuid
from datetime import datetime, timedelta
import random


@service_class
class ComputeService(BaseService):
    def __init__(self, credential, subscription_id):
        super().__init__(credential)
        self.subscription_id = subscription_id
        # No real clients needed for mock data

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

        # Generate mock Virtual Machines
        print("Generating mock Virtual Machines...")
        vm_count = random.randint(2, 8)
        for i in range(vm_count):
            vm_id = f"/subscriptions/{self.subscription_id}/resourceGroups/mock-rg-{i%3}/providers/Microsoft.Compute/virtualMachines/mock-vm-{i}"
            vm_dict = self._generate_mock_vm(i)
            data["virtual_machines"][vm_id] = vm_dict
            print(f"Generated VM: mock-vm-{i}")

        # Generate mock Availability Sets
        print("Generating mock Availability Sets...")
        for i in range(2):
            av_set_id = f"/subscriptions/{self.subscription_id}/resourceGroups/mock-rg-{i}/providers/Microsoft.Compute/availabilitySets/mock-avset-{i}"
            av_set_dict = self._generate_mock_availability_set(i)
            data["availability_sets"][av_set_id] = av_set_dict
            print(f"Generated Availability Set: mock-avset-{i}")

        # Generate mock VM Scale Sets
        print("Generating mock VM Scale Sets...")
        for i in range(1):
            scale_set_id = f"/subscriptions/{self.subscription_id}/resourceGroups/mock-rg-{i}/providers/Microsoft.Compute/virtualMachineScaleSets/mock-vmss-{i}"
            scale_set_dict = self._generate_mock_scale_set(i)
            data["vm_scale_sets"][scale_set_id] = scale_set_dict
            print(f"Generated VM Scale Set: mock-vmss-{i}")

        # Generate mock Managed Disks
        print("Generating mock Managed Disks...")
        disk_count = random.randint(5, 15)
        for i in range(disk_count):
            disk_id = f"/subscriptions/{self.subscription_id}/resourceGroups/mock-rg-{i%3}/providers/Microsoft.Compute/disks/mock-disk-{i}"
            disk_dict = self._generate_mock_disk(i)
            data["disks"][disk_id] = disk_dict
            print(f"Generated Disk: mock-disk-{i}")

        # Generate mock Images
        print("Generating mock Images...")
        for i in range(2):
            image_id = f"/subscriptions/{self.subscription_id}/resourceGroups/mock-rg-{i}/providers/Microsoft.Compute/images/mock-image-{i}"
            image_dict = self._generate_mock_image(i)
            data["images"][image_id] = image_dict
            print(f"Generated Image: mock-image-{i}")

        # Generate mock Snapshots
        print("Generating mock Snapshots...")
        for i in range(3):
            snapshot_id = f"/subscriptions/{self.subscription_id}/resourceGroups/mock-rg-{i}/providers/Microsoft.Compute/snapshots/mock-snapshot-{i}"
            snapshot_dict = self._generate_mock_snapshot(i)
            data["snapshots"][snapshot_id] = snapshot_dict
            print(f"Generated Snapshot: mock-snapshot-{i}")

        return data

    def _generate_mock_vm(self, index):
        """Generate mock VM data"""
        vm_sizes = ["Standard_B2s", "Standard_D2s_v3", "Standard_F2s_v2", "Standard_E2s_v3"]
        os_types = ["Linux", "Windows"]
        states = ["Succeeded", "Running", "Stopped", "Deallocated"]
        
        return {
            "id": f"/subscriptions/{self.subscription_id}/resourceGroups/mock-rg-{index%3}/providers/Microsoft.Compute/virtualMachines/mock-vm-{index}",
            "name": f"mock-vm-{index}",
            "location": random.choice(["eastus", "westus2", "centralus"]),
            "resource_group": f"mock-rg-{index%3}",
            "vm_size": random.choice(vm_sizes),
            "provisioning_state": random.choice(states),
            "vm_id": str(uuid.uuid4()),
            "os_type": random.choice(os_types),
            "os_disk": {
                "name": f"mock-vm-{index}_OsDisk",
                "disk_size_gb": random.choice([30, 64, 128]),
                "managed_disk_id": f"/subscriptions/{self.subscription_id}/resourceGroups/mock-rg-{index%3}/providers/Microsoft.Compute/disks/mock-vm-{index}_OsDisk",
            },
            "data_disks": [
                {
                    "name": f"mock-vm-{index}_DataDisk_{j}",
                    "disk_size_gb": random.choice([100, 500, 1000]),
                    "lun": j,
                    "managed_disk_id": f"/subscriptions/{self.subscription_id}/resourceGroups/mock-rg-{index%3}/providers/Microsoft.Compute/disks/mock-vm-{index}_DataDisk_{j}",
                }
                for j in range(random.randint(0, 3))
            ],
            "network_interfaces": [f"/subscriptions/{self.subscription_id}/resourceGroups/mock-rg-{index%3}/providers/Microsoft.Network/networkInterfaces/mock-vm-{index}-nic"],
            "tags": {"Environment": random.choice(["Dev", "Test", "Prod"]), "Owner": f"Team{index%3}"},
            "zones": [str(random.randint(1, 3))] if random.choice([True, False]) else None,
        }

    def _generate_mock_availability_set(self, index):
        """Generate mock Availability Set data"""
        return {
            "id": f"/subscriptions/{self.subscription_id}/resourceGroups/mock-rg-{index}/providers/Microsoft.Compute/availabilitySets/mock-avset-{index}",
            "name": f"mock-avset-{index}",
            "location": random.choice(["eastus", "westus2"]),
            "resource_group": f"mock-rg-{index}",
            "platform_fault_domain_count": random.choice([2, 3]),
            "platform_update_domain_count": random.choice([5, 10, 20]),
            "virtual_machines": [f"/subscriptions/{self.subscription_id}/resourceGroups/mock-rg-{index}/providers/Microsoft.Compute/virtualMachines/mock-vm-{i}" for i in range(2)],
            "tags": {"Purpose": "HighAvailability"},
        }

    def _generate_mock_scale_set(self, index):
        """Generate mock VM Scale Set data"""
        return {
            "id": f"/subscriptions/{self.subscription_id}/resourceGroups/mock-rg-{index}/providers/Microsoft.Compute/virtualMachineScaleSets/mock-vmss-{index}",
            "name": f"mock-vmss-{index}",
            "location": "eastus",
            "resource_group": f"mock-rg-{index}",
            "sku": {
                "name": "Standard_B2s",
                "capacity": random.randint(2, 10),
            },
            "provisioning_state": "Succeeded",
            "upgrade_policy": random.choice(["Automatic", "Manual", "Rolling"]),
            "tags": {"Environment": "Production", "Application": "WebServer"},
            "zones": [str(i) for i in range(1, random.randint(2, 4))],
        }

    def _generate_mock_disk(self, index):
        """Generate mock Disk data"""
        disk_types = ["Premium_LRS", "Standard_LRS", "StandardSSD_LRS"]
        disk_states = ["Unattached", "Attached", "Reserved"]
        
        return {
            "id": f"/subscriptions/{self.subscription_id}/resourceGroups/mock-rg-{index%3}/providers/Microsoft.Compute/disks/mock-disk-{index}",
            "name": f"mock-disk-{index}",
            "location": random.choice(["eastus", "westus2"]),
            "resource_group": f"mock-rg-{index%3}",
            "disk_size_gb": random.choice([32, 64, 128, 256, 512, 1024]),
            "disk_state": random.choice(disk_states),
            "os_type": random.choice(["Linux", "Windows", None]),
            "provisioning_state": "Succeeded",
            "disk_iops_read_write": random.randint(120, 20000),
            "disk_mbps_read_write": random.randint(25, 900),
            "tags": {"BackupPolicy": "Daily", "CostCenter": f"CC{index%5}"},
            "zones": [str(random.randint(1, 3))] if random.choice([True, False]) else None,
        }

    def _generate_mock_image(self, index):
        """Generate mock Image data"""
        return {
            "id": f"/subscriptions/{self.subscription_id}/resourceGroups/mock-rg-{index}/providers/Microsoft.Compute/images/mock-image-{index}",
            "name": f"mock-image-{index}",
            "location": "eastus",
            "resource_group": f"mock-rg-{index}",
            "provisioning_state": "Succeeded",
            "tags": {"ImageType": "Golden", "OS": random.choice(["Ubuntu", "Windows"])},
        }

    def _generate_mock_snapshot(self, index):
        """Generate mock Snapshot data"""
        return {
            "id": f"/subscriptions/{self.subscription_id}/resourceGroups/mock-rg-{index}/providers/Microsoft.Compute/snapshots/mock-snapshot-{index}",
            "name": f"mock-snapshot-{index}",
            "location": "eastus",
            "resource_group": f"mock-rg-{index}",
            "disk_size_gb": random.choice([32, 64, 128]),
            "os_type": random.choice(["Linux", "Windows", None]),
            "provisioning_state": "Succeeded",
            "time_created": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat(),
            "tags": {"Purpose": "Backup", "RetentionDays": "30"},
        } 