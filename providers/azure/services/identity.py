from providers.service import BaseService, service_class
import random
import uuid
from datetime import datetime, timedelta


@service_class
class IdentityService(BaseService):
    def __init__(self, credential, subscription_id):
        super().__init__(credential)
        self.subscription_id = subscription_id
        # No real clients needed for mock data

    def process(self):
        data = {
            "role_assignments": {},
            "role_definitions": {},
            "managed_identities": {},
        }

        # Generate mock Role Assignments
        print("Generating mock Role Assignments...")
        assignment_count = random.randint(10, 25)
        for i in range(assignment_count):
            assignment_id = f"/subscriptions/{self.subscription_id}/providers/Microsoft.Authorization/roleAssignments/{uuid.uuid4()}"
            assignment_dict = self._generate_mock_role_assignment(i)
            data["role_assignments"][assignment_id] = assignment_dict
            print(f"Generated Role Assignment {i}")

        # Generate mock Role Definitions
        print("Generating mock Role Definitions...")
        definition_count = random.randint(5, 15)
        for i in range(definition_count):
            definition_id = f"/subscriptions/{self.subscription_id}/providers/Microsoft.Authorization/roleDefinitions/{uuid.uuid4()}"
            definition_dict = self._generate_mock_role_definition(i)
            data["role_definitions"][definition_id] = definition_dict
            print(f"Generated Role Definition: {definition_dict['role_name']}")

        # Generate mock Managed Identities
        print("Generating mock Managed Identities...")
        identity_count = random.randint(3, 8)
        for i in range(identity_count):
            identity_id = f"/subscriptions/{self.subscription_id}/resourceGroups/mock-rg-{i%3}/providers/Microsoft.ManagedIdentity/userAssignedIdentities/mock-identity-{i}"
            identity_dict = self._generate_mock_managed_identity(i)
            data["managed_identities"][identity_id] = identity_dict
            print(f"Generated Managed Identity: mock-identity-{i}")

        return data

    def _generate_mock_role_assignment(self, index):
        """Generate mock Role Assignment data"""
        principal_types = ["User", "Group", "ServicePrincipal"]
        scopes = [
            f"/subscriptions/{self.subscription_id}",
            f"/subscriptions/{self.subscription_id}/resourceGroups/mock-rg-{index%3}",
            f"/subscriptions/{self.subscription_id}/resourceGroups/mock-rg-{index%3}/providers/Microsoft.Compute/virtualMachines/mock-vm-{index}"
        ]
        
        role_definitions = [
            f"/subscriptions/{self.subscription_id}/providers/Microsoft.Authorization/roleDefinitions/b24988ac-6180-42a0-ab88-20f7382dd24c",  # Contributor
            f"/subscriptions/{self.subscription_id}/providers/Microsoft.Authorization/roleDefinitions/acdd72a7-3385-48ef-bd42-f606fba81ae7",  # Reader
            f"/subscriptions/{self.subscription_id}/providers/Microsoft.Authorization/roleDefinitions/18d7d88d-d35e-4fb5-a5c3-7773c20a72d9",  # User Access Administrator
            f"/subscriptions/{self.subscription_id}/providers/Microsoft.Authorization/roleDefinitions/8e3af657-a8ff-443c-a75c-2fe8c4bcb635",  # Owner
        ]
        
        created_on = datetime.now() - timedelta(days=random.randint(1, 365))
        
        return {
            "id": f"/subscriptions/{self.subscription_id}/providers/Microsoft.Authorization/roleAssignments/{uuid.uuid4()}",
            "name": str(uuid.uuid4()),
            "type": "Microsoft.Authorization/roleAssignments",
            "scope": random.choice(scopes),
            "role_definition_id": random.choice(role_definitions),
            "principal_id": str(uuid.uuid4()),
            "principal_type": random.choice(principal_types),
            "created_on": created_on.isoformat(),
            "updated_on": created_on.isoformat(),
            "created_by": str(uuid.uuid4()),
            "updated_by": str(uuid.uuid4()),
        }

    def _generate_mock_role_definition(self, index):
        """Generate mock Role Definition data"""
        custom_roles = [
            "Custom VM Operator",
            "Custom Storage Reader",
            "Custom Network Admin",
            "Custom Security Reviewer",
            "Custom Backup Operator"
        ]
        
        builtin_roles = [
            "Virtual Machine Contributor",
            "Storage Account Contributor", 
            "Network Contributor",
            "Security Admin",
            "Backup Contributor"
        ]
        
        is_custom = random.choice([True, False])
        role_name = random.choice(custom_roles if is_custom else builtin_roles)
        
        # Generate permissions based on role type
        if "VM" in role_name or "Virtual Machine" in role_name:
            actions = ["Microsoft.Compute/virtualMachines/*", "Microsoft.Compute/disks/read"]
        elif "Storage" in role_name:
            actions = ["Microsoft.Storage/storageAccounts/*", "Microsoft.Storage/storageAccounts/blobServices/*"]
        elif "Network" in role_name:
            actions = ["Microsoft.Network/*"]
        elif "Security" in role_name:
            actions = ["Microsoft.Security/*", "Microsoft.Authorization/*/read"]
        else:
            actions = ["Microsoft.Resources/subscriptions/resourceGroups/read"]
        
        created_on = datetime.now() - timedelta(days=random.randint(30, 730))
        
        return {
            "id": f"/subscriptions/{self.subscription_id}/providers/Microsoft.Authorization/roleDefinitions/{uuid.uuid4()}",
            "name": str(uuid.uuid4()),
            "type": "Microsoft.Authorization/roleDefinitions",
            "role_name": role_name,
            "description": f"Custom role for {role_name.lower()} operations",
            "role_type": "CustomRole" if is_custom else "BuiltInRole",
            "permissions": [
                {
                    "actions": actions,
                    "not_actions": [],
                    "data_actions": [],
                    "not_data_actions": [],
                }
            ],
            "assignable_scopes": [f"/subscriptions/{self.subscription_id}"],
            "created_on": created_on.isoformat(),
            "updated_on": created_on.isoformat(),
            "created_by": str(uuid.uuid4()),
            "updated_by": str(uuid.uuid4()),
        }

    def _generate_mock_managed_identity(self, index):
        """Generate mock Managed Identity data"""
        locations = ["eastus", "westus2", "centralus"]
        
        return {
            "id": f"/subscriptions/{self.subscription_id}/resourceGroups/mock-rg-{index%3}/providers/Microsoft.ManagedIdentity/userAssignedIdentities/mock-identity-{index}",
            "name": f"mock-identity-{index}",
            "location": random.choice(locations),
            "resource_group": f"mock-rg-{index%3}",
            "type": "Microsoft.ManagedIdentity/userAssignedIdentities",
            "principal_id": str(uuid.uuid4()),
            "client_id": str(uuid.uuid4()),
            "tenant_id": str(uuid.uuid4()),
            "tags": {
                "Environment": random.choice(["Dev", "Test", "Prod"]),
                "Application": f"App{index%5}",
                "ManagedBy": "Infrastructure",
            },
        } 