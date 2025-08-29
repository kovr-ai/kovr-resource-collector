from providers.service import BaseService, service_class
from azure.mgmt.storage import StorageManagementClient


@service_class
class StorageService(BaseService):
    def __init__(self, credential, subscription_id):
        super().__init__(credential)
        self.subscription_id = subscription_id
        self.storage_client = StorageManagementClient(credential, subscription_id)

    def process(self):
        data = {
            "storage_accounts": {},
            "blob_containers": {},
            "file_shares": {},
            "queues": {},
            "tables": {},
        }

        try:
            # Get Storage Accounts
            print("Collecting Storage Accounts...")
            storage_accounts = self.storage_client.storage_accounts.list()
            for account in storage_accounts:
                account_dict = self._storage_account_to_dict(account)
                data["storage_accounts"][account.id] = account_dict
                print(f"Found Storage Account: {account.name}")

                # Get blob containers for this storage account
                try:
                    containers = self.storage_client.blob_containers.list(
                        account.id.split('/')[4], account.name
                    )
                    for container in containers:
                        container_dict = self._container_to_dict(container, account.id)
                        data["blob_containers"][container.id] = container_dict
                except Exception as e:
                    print(f"Error collecting containers for {account.name}: {str(e)}")

                # Get file shares for this storage account
                try:
                    shares = self.storage_client.file_shares.list(
                        account.id.split('/')[4], account.name
                    )
                    for share in shares:
                        share_dict = self._file_share_to_dict(share, account.id)
                        data["file_shares"][share.id] = share_dict
                except Exception as e:
                    print(f"Error collecting file shares for {account.name}: {str(e)}")

        except Exception as e:
            print(f"Error collecting Storage Accounts: {str(e)}")
            data["storage_accounts"] = {}

        return data

    def _storage_account_to_dict(self, account):
        """Convert Storage Account object to dictionary"""
        return {
            "id": account.id,
            "name": account.name,
            "location": account.location,
            "resource_group": account.id.split('/')[4] if len(account.id.split('/')) > 4 else None,
            "kind": account.kind,
            "sku": {
                "name": account.sku.name if account.sku else None,
                "tier": account.sku.tier if account.sku else None,
            },
            "access_tier": account.access_tier,
            "provisioning_state": account.provisioning_state,
            "creation_time": account.creation_time.isoformat() if account.creation_time else None,
            "primary_location": account.primary_location,
            "secondary_location": account.secondary_location,
            "enable_https_traffic_only": account.enable_https_traffic_only,
            "allow_blob_public_access": account.allow_blob_public_access,
            "minimum_tls_version": account.minimum_tls_version,
            "tags": dict(account.tags) if account.tags else {},
        }

    def _container_to_dict(self, container, storage_account_id):
        """Convert Blob Container object to dictionary"""
        return {
            "id": container.id,
            "name": container.name,
            "storage_account_id": storage_account_id,
            "public_access": container.public_access,
            "last_modified_time": container.last_modified_time.isoformat() if container.last_modified_time else None,
            "lease_status": container.lease_status,
            "lease_state": container.lease_state,
            "metadata": container.metadata,
        }

    def _file_share_to_dict(self, share, storage_account_id):
        """Convert File Share object to dictionary"""
        return {
            "id": share.id,
            "name": share.name,
            "storage_account_id": storage_account_id,
            "share_quota": share.share_quota,
            "enabled_protocols": share.enabled_protocols,
            "last_modified_time": share.last_modified_time.isoformat() if share.last_modified_time else None,
            "metadata": share.metadata,
        } 