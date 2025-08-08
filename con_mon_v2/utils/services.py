"""Service utilities for con_mon_v2."""
from typing import Type, Dict, List, Any
from pydantic import BaseModel
from con_mon_v2.resources import Resource, ResourceCollection
from con_mon_v2.mappings.github import GithubConnectorService, GithubConnectorInput
from con_mon_v2.mappings.aws import AwsConnectorService, AwsConnectorInput
from con_mon_v2.connectors.models import ConnectorType


class ResourceCollectionService(object):
    """Service for fetching and validating resource collections."""
    def __init__(
            self,
            resource_type: Type[BaseModel],
            connector_type: str,
    ):
        self.resource_type = resource_type
        self.connector_type = connector_type

    def get_resource_collection(
            self,
            credentials: dict,
    ) -> ResourceCollection:
        """Get resources from a connector."""
        # Get connector service and input class based on type
        if self.connector_type == 'github':
            connector_service = GithubConnectorService(
                name="github",
                description="GitHub connector",
                connector_type=ConnectorType.GITHUB,
                fetch_function=lambda input_config: ResourceCollection(
                    name="github",
                    description="GitHub resources",
                    source_connector="github",
                    total_count=1,
                    resources=[]
                )
            )
            ConnectorInput = GithubConnectorInput
        elif self.connector_type == 'aws':
            connector_service = AwsConnectorService(
                name="aws",
                description="AWS connector",
                connector_type=ConnectorType.AWS,
                fetch_function=lambda input_config: ResourceCollection(
                    name="aws",
                    description="AWS resources",
                    source_connector="aws",
                    total_count=1,
                    resources=[]
                )
            )
            ConnectorInput = AwsConnectorInput
        else:
            raise ValueError(f"Unsupported connector type: {self.connector_type}")

        # Initialize connector with credentials
        connector_input = ConnectorInput(**credentials)
        return connector_service.fetch_data(connector_input)

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

        return get_field_paths(self.resource_type)

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
            validation_report[self.resource_type.__name__] = dict()
            for field_path in self._all_resource_field_paths:
                validation_str = self._validate_field_path(field_path, resource)
                validation_report[self.resource_type.__name__][field_path] = validation_str
        return validation_report


class CheckService(object):
    """Service for validating and executing checks."""
    def __init__(
            self,
            check: Any,  # Using Any to avoid circular import
            connector_type: str,
    ):
        self.check = check
        self.connector_type = connector_type
        self.resource_service = ResourceCollectionService(
            resource_type=check.resource_type,
            connector_type=connector_type
        )

    def get_resource_collection(
            self,
            credentials: dict,
    ) -> ResourceCollection:
        """Get resources from a connector."""
        return self.resource_service.get_resource_collection(credentials)

    @property
    def _all_resource_field_paths(self) -> list[str]:
        """Get all field paths in the resource type."""
        return self.resource_service._all_resource_field_paths

    def validate_resource_field_paths(
            self,
            resource_collection: ResourceCollection,
    ) -> dict[str, dict[str, str]]:
        """Validate all field paths in a resource collection."""
        return self.resource_service.validate_resource_field_paths(resource_collection)

    def validate_execute_check_logic(
            self,
            resource_collection: ResourceCollection,
    ) -> str:
        """Validate check execution logic."""
        try:
            # Execute the check evaluation
            results = self.check.evaluate(resource_collection.resources)

            if not results:
                return "not found"

            # Count successes and failures
            success_count = sum(1 for result in results if result)
            total_count = len(results)

            if total_count == 0:
                return "not found"
            elif success_count == total_count:
                return "success"
            elif success_count == 0:
                return "failure"
            else:
                return "partial"

        except Exception as e:
            return "error"
