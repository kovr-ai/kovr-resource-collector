from providers.service import BaseService, service_class
import random
from datetime import datetime, timedelta


@service_class
class StorageService(BaseService):
    def __init__(self, credential, subscription_id):
        super().__init__(credential)
        self.subscription_id = subscription_id
        # No real clients needed for mock data

    def process(self):
        data = {
            "storage_accounts": {},
            "blob_containers": {},
            "file_shares": {},
            "queues": {},
            "tables": {},
        }

        # Generate mock Storage Accounts
        print("Generating mock Storage Accounts...")
        account_count = random.randint(2, 6)
        for i in range(account_count):
            account_id = f"/subscriptions/{self.subscription_id}/resourceGroups/mock-rg-{i%3}/providers/Microsoft.Storage/storageAccounts/mockstorageacc{i}"
            account_dict = self._generate_mock_storage_account(i)
            data["storage_accounts"][account_id] = account_dict
            print(f"Generated Storage Account: mockstorageacc{i}")

            # Generate blob containers for this storage account
            container_count = random.randint(1, 5)
            for j in range(container_count):
                container_id = f"{account_id}/blobServices/default/containers/container-{j}"
                container_dict = self._generate_mock_container(j, account_id)
                data["blob_containers"][container_id] = container_dict

            # Generate file shares for this storage account
            share_count = random.randint(0, 3)
            for j in range(share_count):
                share_id = f"{account_id}/fileServices/default/shares/share-{j}"
                share_dict = self._generate_mock_file_share(j, account_id)
                data["file_shares"][share_id] = share_dict

        return data

    def _generate_mock_storage_account(self, index):
        """Generate mock Storage Account data"""
        kinds = ["StorageV2", "Storage", "BlobStorage", "BlockBlobStorage", "FileStorage"]
        sku_names = ["Standard_LRS", "Standard_GRS", "Standard_RAGRS", "Premium_LRS"]
        access_tiers = ["Hot", "Cool"]
        locations = ["eastus", "westus2", "centralus", "northeurope"]
        
        creation_time = datetime.now() - timedelta(days=random.randint(30, 365))
        
        return {
            "id": f"/subscriptions/{self.subscription_id}/resourceGroups/mock-rg-{index%3}/providers/Microsoft.Storage/storageAccounts/mockstorageacc{index}",
            "name": f"mockstorageacc{index}",
            "location": random.choice(locations),
            "resource_group": f"mock-rg-{index%3}",
            "kind": random.choice(kinds),
            "sku": {
                "name": random.choice(sku_names),
                "tier": "Standard" if "Standard" in random.choice(sku_names) else "Premium",
            },
            "access_tier": random.choice(access_tiers),
            "provisioning_state": "Succeeded",
            "creation_time": creation_time.isoformat(),
            "primary_location": random.choice(locations),
            "secondary_location": random.choice(locations) if random.choice([True, False]) else None,
            "enable_https_traffic_only": random.choice([True, False]),
            "allow_blob_public_access": random.choice([True, False]),
            "allow_shared_key_access": random.choice([True, False]),
            "minimum_tls_version": random.choice(["TLS1_0", "TLS1_1", "TLS1_2"]),
            "tags": {
                "Environment": random.choice(["Dev", "Test", "Prod"]),
                "CostCenter": f"CC{index%5}",
                "Owner": f"Team{index%3}"
            },
        }

    def _generate_mock_container(self, index, storage_account_id):
        """Generate mock Blob Container data"""
        public_access_types = [None, "Blob", "Container"]
        lease_statuses = ["Available", "Leased", "Expired", "Breaking", "Broken"]
        lease_states = ["Available", "Leased", "Expired", "Breaking", "Broken"]
        
        last_modified = datetime.now() - timedelta(days=random.randint(1, 90))
        
        return {
            "id": f"{storage_account_id}/blobServices/default/containers/container-{index}",
            "name": f"container-{index}",
            "storage_account_id": storage_account_id,
            "public_access": random.choice(public_access_types),
            "last_modified_time": last_modified.isoformat(),
            "lease_status": random.choice(lease_statuses),
            "lease_state": random.choice(lease_states),
            "metadata": {
                "purpose": random.choice(["backup", "logs", "media", "documents"]),
                "created_by": f"user{index%5}",
            },
        }

    def _generate_mock_file_share(self, index, storage_account_id):
        """Generate mock File Share data"""
        protocols = ["SMB", "NFS"]
        access_tiers = ["TransactionOptimized", "Hot", "Cool", "Premium"]
        
        last_modified = datetime.now() - timedelta(days=random.randint(1, 60))
        
        return {
            "id": f"{storage_account_id}/fileServices/default/shares/share-{index}",
            "name": f"share-{index}",
            "storage_account_id": storage_account_id,
            "share_quota": random.choice([100, 500, 1000, 5120]),
            "share_usage_bytes": random.randint(1000000, 100000000),  # 1MB to 100MB
            "enabled_protocols": random.choice(protocols),
            "access_tier": random.choice(access_tiers),
            "last_modified_time": last_modified.isoformat(),
            "metadata": {
                "department": random.choice(["IT", "HR", "Finance", "Marketing"]),
                "backup_enabled": str(random.choice([True, False])).lower(),
            },
        } 