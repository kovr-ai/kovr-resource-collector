"""Service utilities for con_mon_v2."""
from typing import Type, Dict, List, Any
from pydantic import BaseModel
from con_mon_v2.resources import Resource, ResourceCollection
from con_mon_v2.mappings.github import GithubConnectorService, GithubConnectorInput, GithubResource, GithubResourceCollection
from con_mon_v2.mappings.aws import AwsConnectorService, AwsConnectorInput, AwsResource, AwsResourceCollection
from con_mon_v2.connectors.models import ConnectorType


class ResourceCollectionService(object):
    """Service for fetching and validating resource collections."""

    @property
    def connector_service(self):
        """
        return the connector service for the connector type from con_mon_v2.mappings.<connector_type>
        """
        return None

    @property
    def ConnectorInput(self):
        """
        return the ConnectorInput for the connector type from con_mon_v2.mappings.<connector_type>
        """
        return None

    @property
    def resource_collection(self):
        """
        return the models for all resources for the connector type from con_mon_v2.mappings.<connector_type>
        """
        return None

    def __init__(
            self,
            connector_type: str,
    ):
        self.connector_type = connector_type

    def get_resource_collection(
        self,
        credentials: dict,
    ):
        # Use dummy credentials for testing
        if self.connector_type == 'github':
            credentials = {'GITHUB_TOKEN': 'dummy_token'}
        elif self.connector_type == 'aws':
            credentials = {
                'AWS_ROLE_ARN': 'dummy_arn',
                'AWS_ACCESS_KEY_ID': 'dummy_key',
                'AWS_SECRET_ACCESS_KEY': 'dummy_secret',
                'AWS_SESSION_TOKEN': 'dummy_token'
            }

        # Initialize GitHub connector
        connector_input = self.ConnectorInput(**credentials)
        return self.connector_service.fetch_data(connector_input)

    @property
    def _all_resource_field_paths(self) -> list[str]:
        """Get all field paths in the resource type."""
        def get_field_paths(model: Type[BaseModel], prefix: str = "") -> list[str]:
            paths = []
            for field_name, field in model.model_fields.items():
                field_path = f"{prefix}.{field_name}" if prefix else field_name
                paths.append(field_path)

                # If field is another Pydantic model, recursively get its fields
                if isinstance(field.annotation, type) and issubclass(field.annotation, BaseModel):
                    paths.extend(get_field_paths(field.annotation, field_path))
                # Handle list/array of Pydantic models
                elif hasattr(field.annotation, "__origin__") and field.annotation.__origin__ == list:
                    if hasattr(field.annotation, "__args__") and issubclass(field.annotation.__args__[0], BaseModel):
                        paths.extend(get_field_paths(field.annotation.__args__[0], field_path))
            return paths

        return get_field_paths(self.resource_models)

    def _validate_field_path(
            self,
            field_path: str,
            resource: Resource,
    ) -> str:
        """Validate a field path exists in a resource."""
        try:
            # Split the field path into parts
            path_parts = field_path.split('.')
            current = resource

            # Traverse the resource object following the field path
            for part in path_parts:
                if not hasattr(current, part):
                    return "not found"
                current = getattr(current, part)

            # If we got here and the value exists, it's a success
            if current is not None:
                return "success"
            return "not found"  # Field exists but no data

        except Exception as e:
            return "error"  # Field path is invalid or caused an error

    def validate_resource_field_paths(
            self,
            resource_collection: ResourceCollection,
    ) -> dict[str, dict[str, str]]:
        """Validate all field paths in a resource collection."""
        validation_report: dict[str, dict[str, str]] = dict()
        for resource in resource_collection.resources:
            validation_report[resource.__name__] = dict()
            for field_path in self._all_resource_field_paths:
                validation_str = self._validate_field_path(field_path, resource)
                validation_report[resource.__name__][field_path] = validation_str
        return validation_report
