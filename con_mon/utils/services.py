"""Service utilities for con_mon."""
from enum import Enum
import json
from typing import Type, List, Tuple
from pydantic import BaseModel
from datetime import datetime
from con_mon.utils.db import get_db

from con_mon.compliance.data_loader import ConMonResultLoader, ConMonResultHistoryLoader
from con_mon.compliance.models import ConMonResult, ConMonResultHistory, Check, CheckResult
from con_mon.resources import Resource, ResourceCollection
from con_mon.mappings.github import (
    GithubConnectorService,
    GithubConnectorInput,
    GithubResourceCollection,
    github_connector_service,

    # Github Resources
    GithubResource,
)
from con_mon.mappings.aws import (
    AwsConnectorService,
    AwsConnectorInput,
    AwsResourceCollection,
    aws_connector_service,

    # AwsResources
    EC2Resource,
    S3Resource,
    IAMResource,
    CloudTrailResource,
    CloudWatchResource,
)
from con_mon.mappings.google import (
    GoogleConnectorService,
    GoogleConnectorInput,
    GoogleResourceCollection,
    google_connector_service,

    # GoogleResources
    UserResource,
    GroupResource,
)


class ResourceCollectionService(object):
    """Service for fetching and validating resource collections."""

    @property
    def connector_service(self):
        """Return the connector service for the connector type."""
        if self.connector_type == 'github':
            return github_connector_service
        elif self.connector_type == 'aws':
            return aws_connector_service
        elif self.connector_type == 'google':
            return google_connector_service
        raise ValueError(f"Unsupported connector type: {self.connector_type}")

    @property
    def ConnectorInput(self):
        """Return the ConnectorInput for the connector type."""
        if self.connector_type == 'github':
            return GithubConnectorInput
        elif self.connector_type == 'aws':
            return AwsConnectorInput
        elif self.connector_type == 'google':
            return GoogleConnectorInput
        raise ValueError(f"Unsupported connector type: {self.connector_type}")

    @property
    def resource_collection(self):
        """Return the ResourceCollection class for the connector type."""
        if self.connector_type == 'github':
            return GithubResourceCollection
        elif self.connector_type == 'aws':
            return AwsResourceCollection
        elif self.connector_type == 'google':
            return GoogleResourceCollection
        raise ValueError(f"Unsupported connector type: {self.connector_type}")

    @property
    def resource_models(self):
        """Return the Resource class for the connector type."""
        if self.connector_type == 'github':
            return [GithubResource]
        elif self.connector_type == 'aws':
            return [
                EC2Resource,
                S3Resource,
                IAMResource,
                CloudTrailResource,
                CloudWatchResource,
            ]
        elif self.connector_type == 'google':
            return [
                UserResource,
                GroupResource,
            ]
        raise ValueError(f"Unsupported connector type: {self.connector_type}")

    def __init__(
            self,
            connector_type: str,
    ):
        self.connector_type = connector_type.lower()  # Normalize to lowercase

    def get_resource_collection(
        self,
        credentials: dict | None = None,
    ):
        if not credentials:
            if self.connector_type == 'github':
                credentials = {'personal_access_token': 'dummy_token'}
            elif self.connector_type == 'aws':
                credentials = {
                    'role_arn': 'dummy_arn',
                    'external_id': 'dummy_external_id',
                }
            elif self.connector_type == 'google':
                credentials = {
                    'super_admin_email': 'dummy_email',
                }
            else:
                raise ValueError(f"Dummy not available for connector type: {self.connector_type}")

        # Initialize connector with credentials
        connector_input = self.ConnectorInput(**credentials)
        return self.connector_service.fetch_data(connector_input)

    @property
    def _all_resource_field_paths(self) -> list[str]:
        """Get all field paths in the resource type."""
        def get_field_paths(model: Type[BaseModel], prefix: str = "") -> list[str]:
            paths = []
            for field_name, field in model.model_fields.items():
                # Skip schema-only fields
                if field_name in ['name', 'description', 'provider', 'service']:
                    continue
                
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

        # Get field paths for each resource model
        all_paths = []
        for model in self.resource_models:
            all_paths.extend(get_field_paths(model))
        return all_paths

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
            print(f"\nChecking {resource.__class__.__name__}.{field_path}...")

            # Traverse the resource object following the field path
            for part in path_parts:
                if not hasattr(current, part):
                    print(f"❌ Field '{part}' not found")
                    return "not found"
                current = getattr(current, part)
                print(f"  ✓ Found '{part}'")

            # If current is a list, check all items
            if isinstance(current, list):
                print(f"✅ Found list with {len(current)} items")
                if len(current) > 0:
                    for i, item in enumerate(current):
                        print(f"  Item {i}:")
                        for field in item.__dict__:
                            getattr(item, field)
                            print(f"    ✓ {field}")
                else:
                    print("  (Empty list)")
                return "success"

            # If we got here and the value exists, it's a success
            if current is not None:
                print(f"✅ Found value")
                return "success"
            
            print(f"⚠️  Field exists but value is None")
            return "not found"  # Field exists but no data

        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return "error"  # Field path is invalid or caused an error

    def validate_resource_field_paths(
            self,
            resource_collection: ResourceCollection,
    ) -> dict[str, dict[str, str]]:
        """Validate all field paths in a resource collection."""
        validation_report: dict[str, dict[str, str]] = dict()
        for resource in resource_collection.resources:
            validation_report[resource.__class__.__name__] = dict()  # Use actual class name
            for field_path in self._all_resource_field_paths:
                validation_str = self._validate_field_path(field_path, resource)
                validation_report[resource.__class__.__name__][field_path] = validation_str
        return validation_report


class ConMonResultService(object):
    def __init__(
        self,
        check: Check,
        check_results: List[CheckResult],
        customer_id: str,
        connection_id: int,
    ):
        self.check = check
        self.check_results = check_results
        self.customer_id = customer_id
        self.connection_id = connection_id

    def get_con_mon_result(self) -> ConMonResult:
        """
        Convert CheckResult objects into ConMonResult objects for database storage.
        
        Returns:
            List containing a single ConMonResult that aggregates all check results
        """
        # Separate passed and failed resources
        success_resources = []
        failed_resources = []
        resource_json = dict()

        for check_result in self.check_results:
            resource = check_result.resource
            resource_json[resource.id] = json.loads(resource.model_dump_json())
            
            if check_result.passed is True:
                success_resources.append(check_result.resource.id)
            elif check_result.passed is False:
                failed_resources.append(check_result.resource.id)
            else:
                failed_resources.append(check_result.resource.id)
        
        # Calculate metrics
        success_count = len(success_resources)
        failure_count = len(failed_resources)
        total_count = success_count + failure_count
        success_percentage = round((success_count / total_count) * 100, 2) if total_count > 0 else 0
        
        # Determine overall result
        overall_result = 'PASS' if failure_count == 0 else 'FAIL'
        
        # Create result message using the check's result_summary method
        result_message = self.check.result_summary(self.check_results)
        
        # Create ConMonResult object
        con_mon_result = ConMonResult(
            customer_id=self.customer_id,
            connection_id=self.connection_id,
            check_id=self.check.id,
            result=overall_result,
            result_message=result_message,
            success_count=success_count,
            failure_count=failure_count,
            success_percentage=success_percentage,
            success_resources=success_resources,
            failed_resources=failed_resources,
            exclusions=[],  # No exclusions for now
            resource_json=resource_json,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        return con_mon_result

    @classmethod
    def insert_in_db(
        cls,
        executed_check_results: List[Tuple[Check, CheckResult]],
        customer_id: str,
        connection_id: int,
    ) -> int:
        con_mon_results: List[ConMonResult] = list()
        for check, check_results in executed_check_results:
            con_mon_result = cls(
                check,
                check_results,
                customer_id,
                connection_id,
            ).get_con_mon_result()
            con_mon_results.append(con_mon_result)

        if not con_mon_results:
            return 0

        return ConMonResultLoader().insert_results(con_mon_results)

class AsyncTaskService(object):
    def __init__(self, task_id: str):
        self.task_id = task_id
        self.db = get_db()

    class Status(Enum):
        IN_PROCESS = "IN_PROCESS"
        PROCESSED = "PROCESSED"
        FAILED = "FAILED"

    def update_task_status(self, status: Status):
        self.db.execute_update(
            "UPDATE async_tasks SET status = %s WHERE id = %s",
            (status, self.task_id)
        )