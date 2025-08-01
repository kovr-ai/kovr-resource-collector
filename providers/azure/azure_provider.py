from providers.azure.services.compute import ComputeService
from providers.azure.services.storage import StorageService
from providers.azure.services.identity import IdentityService
from providers.azure.services.security import SecurityService
from providers.azure.services.networking import NetworkingService
from providers.provider import Provider, provider_class
from constants import Providers
from azure.identity import ClientSecretCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.subscription import SubscriptionClient


@provider_class
class AzureProvider(Provider):
    def __init__(self, metadata: dict):
        self.AZURE_CLIENT_ID = metadata.get("AZURE_CLIENT_ID")
        self.AZURE_CLIENT_SECRET = metadata.get("AZURE_CLIENT_SECRET")
        self.AZURE_TENANT_ID = metadata.get("AZURE_TENANT_ID")
        self.AZURE_SUBSCRIPTION_ID = metadata.get("AZURE_SUBSCRIPTION_ID")

        if (
            not self.AZURE_CLIENT_ID
            or not self.AZURE_CLIENT_SECRET
            or not self.AZURE_TENANT_ID
            or not self.AZURE_SUBSCRIPTION_ID
        ):
            raise ValueError(
                "AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID, and AZURE_SUBSCRIPTION_ID are required"
            )

        super().__init__(Providers.AZURE.value, metadata)

        # Define services to collect data from
        self.services = [
            {"name": "compute", "class": ComputeService},
            {"name": "storage", "class": StorageService},
            {"name": "identity", "class": IdentityService},
            {"name": "security", "class": SecurityService},
            {"name": "networking", "class": NetworkingService},
        ]

    def connect(self):
        """Establish connection to Azure using service principal credentials"""
        try:
            credential = ClientSecretCredential(
                tenant_id=self.AZURE_TENANT_ID,
                client_id=self.AZURE_CLIENT_ID,
                client_secret=self.AZURE_CLIENT_SECRET,
            )
            
            # Test connection by getting subscription info
            subscription_client = SubscriptionClient(credential)
            subscription = subscription_client.subscriptions.get(self.AZURE_SUBSCRIPTION_ID)
            print(f"Connected to Azure subscription: {subscription.display_name}")
            
            return credential
            
        except Exception as e:
            print(f"Failed to connect to Azure: {str(e)}")
            raise ValueError(f"Azure connection failed: {str(e)}")

    def _get_all_locations(self, credential):
        """Get all available Azure locations for the subscription"""
        locations = []
        try:
            subscription_client = SubscriptionClient(credential)
            location_list = subscription_client.subscriptions.list_locations(self.AZURE_SUBSCRIPTION_ID)
            locations = [location.name for location in location_list]
        except Exception as e:
            print(f"Failed to get locations: {str(e)}")
            locations = ["eastus"]  # Default to East US if we can't get locations
        return locations

    def _get_resource_groups(self, credential):
        """Get all resource groups in the subscription"""
        resource_groups = []
        try:
            resource_client = ResourceManagementClient(credential, self.AZURE_SUBSCRIPTION_ID)
            rg_list = resource_client.resource_groups.list()
            resource_groups = [rg.name for rg in rg_list]
        except Exception as e:
            print(f"Failed to get resource groups: {str(e)}")
            resource_groups = []
        return resource_groups

    def process(self):
        """Process data collection from all Azure services"""
        data = {}
        credential = self.client
        
        # Get resource groups to organize data collection
        resource_groups = self._get_resource_groups(credential)
        print(f"Found {len(resource_groups)} resource groups")
        
        # Collect data for each service
        for index, service in enumerate(self.services):
            print(f"Fetching data for service: {service['name']} ({index + 1}/{len(self.services)})")
            name = service["name"]
            instance = service["class"](credential, self.AZURE_SUBSCRIPTION_ID)
            data[name] = instance.process()

        return data 