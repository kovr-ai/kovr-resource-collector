from providers.service import BaseService, service_class
from azure.mgmt.authorization import AuthorizationManagementClient
from azure.mgmt.msi import ManagedServiceIdentityClient


@service_class
class IdentityService(BaseService):
    def __init__(self, credential, subscription_id):
        super().__init__(credential)
        self.subscription_id = subscription_id
        self.auth_client = AuthorizationManagementClient(credential, subscription_id)
        self.msi_client = ManagedServiceIdentityClient(credential, subscription_id)

    def process(self):
        data = {
            "role_assignments": {},
            "role_definitions": {},
            "managed_identities": {},
        }

        try:
            # Get Role Assignments
            print("Collecting Role Assignments...")
            role_assignments = self.auth_client.role_assignments.list()
            for assignment in role_assignments:
                assignment_dict = self._role_assignment_to_dict(assignment)
                data["role_assignments"][assignment.id] = assignment_dict
                print(f"Found Role Assignment: {assignment.id}")

        except Exception as e:
            print(f"Error collecting Role Assignments: {str(e)}")
            data["role_assignments"] = {}

        try:
            # Get Role Definitions
            print("Collecting Role Definitions...")
            role_definitions = self.auth_client.role_definitions.list(f"/subscriptions/{self.subscription_id}")
            for definition in role_definitions:
                definition_dict = self._role_definition_to_dict(definition)
                data["role_definitions"][definition.id] = definition_dict
                print(f"Found Role Definition: {definition.role_name}")

        except Exception as e:
            print(f"Error collecting Role Definitions: {str(e)}")
            data["role_definitions"] = {}

        try:
            # Get Managed Identities
            print("Collecting Managed Identities...")
            managed_identities = self.msi_client.user_assigned_identities.list_by_subscription()
            for identity in managed_identities:
                identity_dict = self._managed_identity_to_dict(identity)
                data["managed_identities"][identity.id] = identity_dict
                print(f"Found Managed Identity: {identity.name}")

        except Exception as e:
            print(f"Error collecting Managed Identities: {str(e)}")
            data["managed_identities"] = {}

        return data

    def _role_assignment_to_dict(self, assignment):
        """Convert Role Assignment object to dictionary"""
        return {
            "id": assignment.id,
            "name": assignment.name,
            "type": assignment.type,
            "scope": assignment.scope,
            "role_definition_id": assignment.role_definition_id,
            "principal_id": assignment.principal_id,
            "principal_type": assignment.principal_type,
            "created_on": assignment.created_on.isoformat() if assignment.created_on else None,
            "updated_on": assignment.updated_on.isoformat() if assignment.updated_on else None,
            "created_by": assignment.created_by,
            "updated_by": assignment.updated_by,
        }

    def _role_definition_to_dict(self, definition):
        """Convert Role Definition object to dictionary"""
        return {
            "id": definition.id,
            "name": definition.name,
            "type": definition.type,
            "role_name": definition.role_name,
            "description": definition.description,
            "role_type": definition.role_type,
            "permissions": [
                {
                    "actions": permission.actions or [],
                    "not_actions": permission.not_actions or [],
                    "data_actions": permission.data_actions or [],
                    "not_data_actions": permission.not_data_actions or [],
                }
                for permission in (definition.permissions or [])
            ],
            "assignable_scopes": definition.assignable_scopes or [],
            "created_on": definition.created_on.isoformat() if definition.created_on else None,
            "updated_on": definition.updated_on.isoformat() if definition.updated_on else None,
            "created_by": definition.created_by,
            "updated_by": definition.updated_by,
        }

    def _managed_identity_to_dict(self, identity):
        """Convert Managed Identity object to dictionary"""
        return {
            "id": identity.id,
            "name": identity.name,
            "location": identity.location,
            "resource_group": identity.id.split('/')[4] if len(identity.id.split('/')) > 4 else None,
            "type": identity.type,
            "principal_id": identity.principal_id,
            "client_id": identity.client_id,
            "tenant_id": identity.tenant_id,
            "tags": dict(identity.tags) if identity.tags else {},
        } 