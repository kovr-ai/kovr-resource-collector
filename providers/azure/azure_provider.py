from providers.azure.services.compute import ComputeService
from providers.azure.services.storage import StorageService
from providers.azure.services.identity import IdentityService
from providers.azure.services.security import SecurityService
from providers.azure.services.networking import NetworkingService
from providers.provider import Provider, provider_class
from constants import Providers
import random


@provider_class
class AzureProvider(Provider):
    def __init__(self, metadata: dict):
        self.AZURE_CLIENT_ID = metadata.get("AZURE_CLIENT_ID") or "mock-client-id"
        self.AZURE_CLIENT_SECRET = metadata.get("AZURE_CLIENT_SECRET") or "mock-client-secret"
        self.AZURE_TENANT_ID = metadata.get("AZURE_TENANT_ID") or "mock-tenant-id"
        self.AZURE_SUBSCRIPTION_ID = metadata.get("AZURE_SUBSCRIPTION_ID") or "mock-subscription-id"

        # No validation needed for mock data
        print(f"Using mock Azure credentials for subscription: {self.AZURE_SUBSCRIPTION_ID}")

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
        """Mock connection to Azure - no real authentication needed"""
        try:
            print(f"Mock Azure connection successful!")
            print(f"Connected to mock subscription: {self.AZURE_SUBSCRIPTION_ID}")
            
            # Return mock credential object - services don't actually use it
            return {"mock": True, "subscription_id": self.AZURE_SUBSCRIPTION_ID}
            
        except Exception as e:
            print(f"Mock connection failed: {str(e)}")
            raise ValueError(f"Mock Azure connection failed: {str(e)}")

    def _get_all_locations(self, credential=None):
        """Get mock Azure locations"""
        locations = ["eastus", "westus2", "centralus", "northeurope", "southeastasia"]
        return locations

    def _get_resource_groups(self, credential=None):
        """Get mock resource groups"""
        resource_groups = ["mock-rg-0", "mock-rg-1", "mock-rg-2"]
        return resource_groups

    def process(self):
        """Process data collection from all Azure services using mock data"""
        data = {}
        credential = self.client
        
        # Get mock resource groups
        resource_groups = self._get_resource_groups(credential)
        print(f"Found {len(resource_groups)} mock resource groups")
        
        # Collect data for each service
        for index, service in enumerate(self.services):
            print(f"Generating mock data for service: {service['name']} ({index + 1}/{len(self.services)})")
            name = service["name"]
            instance = service["class"](credential, self.AZURE_SUBSCRIPTION_ID)
            data[name] = instance.process()

        return data 