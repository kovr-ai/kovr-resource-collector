"""
Validate with Mock Data Service Implementation
"""

import traceback
from typing import List
from pydantic import BaseModel
from llm_generator.services import Service

from con_mon.utils.services import ResourceCollectionService
from con_mon.resources import Resource
from con_mon.compliance.models import (
    Check,
    ComparisonOperation,
    ComparisonOperationEnum
)


def get_comparison_operation(logic) -> ComparisonOperation:
    if not logic:
        raise ValueError("Logic not specified in metadata")
    # For custom operations, use the custom logic
    operation_enum = ComparisonOperationEnum.CUSTOM
    function = ComparisonOperation.get_custom_function(
        operation_enum,
        logic
    )

    # Create and return the ComparisonOperation instance
    return ComparisonOperation(
        name=operation_enum,
        function=function
    )


class ValidateWithMockDataService(Service):
    """Service for validating Python logic against mock resource data"""

    def _load_resources(self, resource_name) -> List[Resource]:
        if "github" in resource_name.lower():
            connector_type = "github"
        elif any(term in resource_name.lower() for term in ["ec2", "iam", "s3", "cloudwatch", "cloudtrail"]):
            connector_type = "aws"
        elif "user" in resource_name.lower() or "group" in resource_name.lower():
            connector_type = "google"
        else:
            raise ValueError(f"Unsupported connector type for resource: {resource_name}")
        service = ResourceCollectionService(connector_type)
        _, resource_collection = service.get_resource_collection()
        return resource_collection.resources

    def _process_input(self, input_: BaseModel):
        """Process a single input and validate Python logic"""
        # Load mock data for this resource
        input_check = input_.check
        input_resource = input_.check.resource
        resources = self._load_resources(input_resource.name)

        validation_results = []

        for resource in resources:
            input_filepath = f"llm_generator_v2/data/debugging/sec3_checks_with_python_logic/step1_generate_python_logic/input/{input_check.unique_id}-{input_resource.name}.yaml"
            output_filepath = f"llm_generator_v2/data/debugging/sec3_checks_with_python_logic/step1_generate_python_logic/output/{input_check.unique_id}-{input_resource.name}.yaml"
            try:
                # Extract value using field path
                if resource.__class__.__name__ == input_resource.name:
                    fetched_value = Check._extract_field_value(resource, input_resource.field_path)
                else:
                    continue

                # Execute Python logic
                comparison_operation = get_comparison_operation(input_resource.logic)
                result = comparison_operation(fetched_value, None)
                if result is None:
                    raise Exception(f'resource failed silently')

                validation_results.append({
                    "success": True,
                    "result": result,
                    "error": "",
                    "input_filepath": input_filepath,
                    "output_filepath": output_filepath,
                    "field_path": input_resource.field_path,
                    "logic": input_resource.logic,
                    "fetched_value_type": str(type(fetched_value).__name__),
                    "fetched_value_sample": str(fetched_value)[:100] if fetched_value is not None else "None",
                })

            except Exception as e:
                trace_str = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
                if "__import__" in trace_str:
                    print(trace_str)
                    print(input_resource.logic)
                validation_results.append({
                    "success": False,
                    "result": None,
                    "error": trace_str,
                    "input_filepath": input_filepath,
                    "output_filepath": output_filepath,
                    "field_path": input_resource.field_path,
                    "logic": input_resource.logic,
                    "fetched_value_type": "error",
                    "fetched_value_sample": "error",
                })

        # Collect errors from failed tests
        errors = []
        for result in validation_results:
            if not result["success"]:
                errors.append(result)

        resource = input_resource.model_dump()
        resource['check'] = input_check.model_dump()
        return self.Output(resource=resource, errors=errors)
